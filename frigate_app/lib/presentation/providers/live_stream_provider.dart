import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_webrtc/flutter_webrtc.dart';
import 'server_config_provider.dart';

class CameraInfo {
  final String name;
  final bool enabled;
  final List<String> objects;
  final List<String> zones;
  final String liveStreamName;

  CameraInfo({
    required this.name,
    required this.enabled,
    required this.objects,
    required this.zones,
    required this.liveStreamName,
  });

  factory CameraInfo.fromJson(Map<String, dynamic> json) {
    final detect = json['detect'] as Map<String, dynamic>? ?? {};
    return CameraInfo(
      name: json['name']?.toString() ?? '',
      enabled: json['enabled'] as bool? ?? false,
      objects: (detect['objects'] as List?)?.map((e) => e.toString()).toList() ?? [],
      zones: (json['zones'] as List?)?.map((e) => e.toString()).toList() ?? [],
      liveStreamName: json['live_stream_name']?.toString() ?? json['name']?.toString() ?? '',
    );
  }
}

final cameraListProvider = FutureProvider<List<CameraInfo>>((ref) async {
  final apiClient = ref.watch(apiClientProvider);
  final result = await apiClient.getCameras();
  final cameras = result['cameras'] as List? ?? [];
  return cameras.map((c) => CameraInfo.fromJson(c as Map<String, dynamic>)).toList();
});

enum StreamStatus { idle, connecting, connected, error }

class WebRTCStreamController {
  final String serverIp;
  final String cameraName;
  RTCPeerConnection? _pc;
  RTCVideoRenderer? _renderer;
  StreamStatus _status = StreamStatus.idle;
  String _errorMessage = '';

  StreamStatus get status => _status;
  String get errorMessage => _errorMessage;
  RTCVideoRenderer? get renderer => _renderer;

  WebRTCStreamController({
    required this.serverIp,
    required this.cameraName,
  });

  Future<RTCVideoRenderer> startStream() async {
    _status = StreamStatus.connecting;
    _errorMessage = '';

    try {
      _renderer = RTCVideoRenderer();
      await _renderer!.initialize();

      _pc = await createPeerConnection({
        'iceServers': [],
        'bundlePolicy': 'max-bundle',
      });

      _pc!.onTrack = (event) {
        if (event.track.kind == 'video') {
          _renderer!.srcObject = event.streams[0];
        }
      };

      _pc!.onConnectionState = (state) {
        if (state == RTCPeerConnectionState.RTCPeerConnectionStateConnected) {
          _status = StreamStatus.connected;
        } else if (state == RTCPeerConnectionState.RTCPeerConnectionStateFailed) {
          _status = StreamStatus.error;
          _errorMessage = 'Connection failed';
        }
      };

      await _pc!.addTransceiver(
        kind: RTCRtpMediaType.RTCRtpMediaTypeVideo,
        init: RTCRtpTransceiverInit(direction: TransceiverDirection.RecvOnly),
      );
      await _pc!.addTransceiver(
        kind: RTCRtpMediaType.RTCRtpMediaTypeAudio,
        init: RTCRtpTransceiverInit(direction: TransceiverDirection.RecvOnly),
      );

      final offer = await _pc!.createOffer();
      await _pc!.setLocalDescription(offer);

      final answerSdp = await _exchangeSdp(offer.sdp ?? '');

      await _pc!.setRemoteDescription(
        RTCSessionDescription(answerSdp, 'answer'),
      );

      return _renderer!;
    } catch (e) {
      _status = StreamStatus.error;
      _errorMessage = e.toString();
      rethrow;
    }
  }

  Future<String> _exchangeSdp(String offerSdp) async {
    final dio = Dio(BaseOptions(
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 10),
    ));
    final response = await dio.post(
      'http://$serverIp:5000/api/webrtc?camera=$cameraName',
      data: {'sdp': offerSdp, 'type': 'offer'},
      options: Options(
        headers: {'Content-Type': 'application/json'},
        responseType: ResponseType.json,
      ),
    );
    final data = response.data as Map<String, dynamic>;
    return data['sdp'] as String;
  }

  void stopStream() {
    _pc?.close();
    _renderer?.dispose();
    _pc = null;
    _renderer = null;
    _status = StreamStatus.idle;
  }

  void dispose() {
    stopStream();
  }
}
