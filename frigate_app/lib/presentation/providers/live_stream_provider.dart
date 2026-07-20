import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:media_kit/media_kit.dart';
import 'package:media_kit_video/media_kit_video.dart';
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

class LiveStreamController {
  final String serverIp;
  final String cameraName;
  Player? _player;
  VideoController? _videoController;
  StreamStatus _status = StreamStatus.idle;
  String _errorMessage = '';

  StreamStatus get status => _status;
  String get errorMessage => _errorMessage;
  VideoController? get videoController => _videoController;

  LiveStreamController({
    required this.serverIp,
    required this.cameraName,
  });

  Future<VideoController> startStream() async {
    _status = StreamStatus.connecting;
    _errorMessage = '';

    try {
      final rtspUrl = 'rtsp://$serverIp:8554/$cameraName';
      debugPrint('[Live] Starting RTSP stream: $rtspUrl');

      _player = Player();
      _videoController = VideoController(_player!);

      await _player!.open(Media(rtspUrl));
      debugPrint('[Live] Player opened successfully');

      _status = StreamStatus.connected;
      return _videoController!;
    } catch (e) {
      _status = StreamStatus.error;
      _errorMessage = e.toString();
      debugPrint('[Live] Error: $e');
      rethrow;
    }
  }

  void stopStream() {
    _player?.dispose();
    _player = null;
    _videoController = null;
    _status = StreamStatus.idle;
  }

  void dispose() {
    stopStream();
  }
}
