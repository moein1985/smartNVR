import 'dart:async';
import 'dart:convert';
import 'dart:io';
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

  WebSocket? _ws;

  Future<RTCVideoRenderer> startStream() async {
    _status = StreamStatus.connecting;
    _errorMessage = '';

    try {
      _renderer = RTCVideoRenderer();
      await _renderer!.initialize();

      _pc = await createPeerConnection({
        'iceServers': [
          {'urls': 'stun:stun.l.google.com:19302'}
        ],
        'bundlePolicy': 'max-bundle',
      });

      _pc!.onTrack = (event) {
        print('[WebRTC] onTrack: kind=${event.track.kind}, streams=${event.streams.length}');
        if (event.track.kind == 'video') {
          _renderer!.srcObject = event.streams[0];
        }
      };

      _pc!.onConnectionState = (state) {
        print('[WebRTC] onConnectionState: $state');
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

      final wsUrl = 'ws://$serverIp:5000/live/webrtc/api/ws?src=$cameraName';
      print('[WebRTC] Connecting to WebSocket: $wsUrl');
      _ws = await WebSocket.connect(wsUrl).timeout(
        const Duration(seconds: 5),
        onTimeout: () => throw TimeoutException('WebSocket connection timeout'),
      );
      print('[WebRTC] WebSocket connected');

      final answerCompleter = Completer<String>();

      _ws!.listen(
        (data) {
          if (data is String) {
            final msg = jsonDecode(data) as Map<String, dynamic>;
            final type = msg['type'] as String?;
            print('[WebRTC] WS message: type=$type');

            if (type == 'webrtc/answer') {
              final answerSdp = msg['value'] as String;
              if (!answerCompleter.isCompleted) {
                answerCompleter.complete(answerSdp);
              }
            } else if (type == 'webrtc/candidate') {
              final candidate = msg['value'] as String?;
              if (candidate != null && candidate.isNotEmpty) {
                _pc!.addCandidate(
                  RTCIceCandidate(candidate, '0', 0),
                );
              }
            } else if (type == 'error') {
              final error = msg['value'] as String?;
              print('[WebRTC] go2rtc error value: $error');
              print('[WebRTC] Full WS message: $msg');
              if (!answerCompleter.isCompleted) {
                answerCompleter.completeError(Exception('go2rtc error: $error'));
              }
            }
          }
        },
        onError: (e) {
          print('[WebRTC] WebSocket error: $e');
          if (!answerCompleter.isCompleted) {
            answerCompleter.completeError(e);
          }
        },
        onDone: () {
          print('[WebRTC] WebSocket closed');
          if (!answerCompleter.isCompleted) {
            answerCompleter.completeError(Exception('WebSocket closed before receiving answer'));
          }
        },
      );

      _pc!.onIceCandidate = (candidate) {
        final msg = jsonEncode({
          'type': 'webrtc/candidate',
          'value': candidate.candidate ?? '',
        });
        _ws?.add(msg);
      };

      final offer = await _pc!.createOffer();
      await _pc!.setLocalDescription(offer);

      final offerMsg = jsonEncode({
        'type': 'webrtc/offer',
        'value': offer.sdp ?? '',
      });
      _ws!.add(offerMsg);
      print('[WebRTC] Sent webrtc/offer, SDP length: ${offer.sdp?.length ?? 0}');

      final answerSdp = await answerCompleter.future.timeout(
        const Duration(seconds: 10),
        onTimeout: () {
          throw TimeoutException('Timeout waiting for WebRTC answer from go2rtc');
        },
      );

      print('[WebRTC] Received answer SDP, length: ${answerSdp.length}');

      await _pc!.setRemoteDescription(
        RTCSessionDescription(answerSdp, 'answer'),
      );

      print('[WebRTC] Remote description set successfully');

      return _renderer!;
    } catch (e) {
      _status = StreamStatus.error;
      _errorMessage = e.toString();
      rethrow;
    }
  }

  void stopStream() {
    _ws?.close();
    _ws = null;
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
