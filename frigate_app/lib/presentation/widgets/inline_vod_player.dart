import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:media_kit/media_kit.dart';
import 'package:media_kit_video/media_kit_video.dart';
import '../models/playback_params.dart';
import '../providers/server_config_provider.dart';

class InlineVodPlayer extends ConsumerStatefulWidget {
  final PlaybackParams params;

  const InlineVodPlayer({
    super.key,
    required this.params,
  });

  static String constructVodUrl(String serverIp, PlaybackParams params) {
    final startTime = params.startTime.toInt();
    final endTime = params.endTime.toInt();
    return 'http://$serverIp:5000/api/${params.camera}/start/$startTime/end/$endTime/clip.mp4';
  }

  @override
  ConsumerState<InlineVodPlayer> createState() => _InlineVodPlayerState();
}

class _InlineVodPlayerState extends ConsumerState<InlineVodPlayer> {
  Player? _player;
  VideoController? _controller;
  bool _initialized = false;
  bool _hasError = false;

  @override
  void initState() {
    super.initState();
    _initPlayer();
  }

  void _initPlayer() {
    final configAsync = ref.read(serverConfigProvider);
    final serverIp = configAsync.maybeWhen(
      data: (c) => c.ip,
      orElse: () => '',
    );

    if (serverIp.isEmpty) {
      setState(() => _hasError = true);
      return;
    }

    final url = InlineVodPlayer.constructVodUrl(serverIp, widget.params);
    debugPrint('[InlineVodPlayer] Opening URL: $url');

    _player = Player();
    _controller = VideoController(_player!);
    _player!.open(Media(url)).then((_) {
      if (mounted) {
        setState(() => _initialized = true);
      }
    }).catchError((_) {
      if (mounted) {
        setState(() => _hasError = true);
      }
    });
  }

  @override
  void dispose() {
    _player?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_hasError) {
      return Container(
        height: 200,
        decoration: BoxDecoration(
          color: Colors.black,
          borderRadius: BorderRadius.circular(12),
        ),
        child: const Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.error_outline, color: Colors.white38, size: 36),
              SizedBox(height: 8),
              Text('ویدیو در دسترس نیست',
                  style: TextStyle(color: Colors.white54, fontSize: 13)),
            ],
          ),
        ),
      );
    }

    if (!_initialized || _controller == null) {
      return Container(
        height: 200,
        decoration: BoxDecoration(
          color: Colors.black,
          borderRadius: BorderRadius.circular(12),
        ),
        child: const Center(
          child: CircularProgressIndicator(color: Colors.white54),
        ),
      );
    }

    return ClipRRect(
      borderRadius: BorderRadius.circular(12),
      child: Container(
        height: 200,
        color: Colors.black,
        child: AspectRatio(
          aspectRatio: 16 / 9,
          child: Video(controller: _controller!),
        ),
      ),
    );
  }
}
