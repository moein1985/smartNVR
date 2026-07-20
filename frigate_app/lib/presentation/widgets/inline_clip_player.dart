import 'package:flutter/material.dart';
import 'package:media_kit/media_kit.dart';
import 'package:media_kit_video/media_kit_video.dart';

class InlineClipPlayer extends StatefulWidget {
  final String clipUrl;

  const InlineClipPlayer({
    super.key,
    required this.clipUrl,
  });

  @override
  State<InlineClipPlayer> createState() => _InlineClipPlayerState();
}

class _InlineClipPlayerState extends State<InlineClipPlayer> {
  late final Player _player;
  late final VideoController _controller;
  bool _initialized = false;
  bool _hasError = false;

  @override
  void initState() {
    super.initState();
    _player = Player();
    _controller = VideoController(_player);
    _initPlayer();
  }

  Future<void> _initPlayer() async {
    try {
      await _player.open(Media(widget.clipUrl));
      if (mounted) {
        setState(() => _initialized = true);
      }
    } catch (_) {
      if (mounted) {
        setState(() => _hasError = true);
      }
    }
  }

  @override
  void dispose() {
    _player.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_hasError) {
      return Container(
        color: Colors.black,
        child: const Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.error_outline, color: Colors.white38, size: 48),
              SizedBox(height: 8),
              Text('کلیپ در دسترس نیست',
                  style: TextStyle(color: Colors.white54)),
            ],
          ),
        ),
      );
    }

    if (!_initialized) {
      return Container(
        color: Colors.black,
        child: const Center(
          child: CircularProgressIndicator(color: Colors.white54),
        ),
      );
    }

    return Container(
      color: Colors.black,
      child: AspectRatio(
        aspectRatio: 16 / 9,
        child: Video(controller: _controller),
      ),
    );
  }
}
