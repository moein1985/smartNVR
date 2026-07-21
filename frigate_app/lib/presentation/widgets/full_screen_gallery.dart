import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:media_kit/media_kit.dart';
import 'package:media_kit_video/media_kit_video.dart';

class GalleryItem {
  final String imageUrl;
  final String clipUrl;
  final String label;
  final String camera;

  const GalleryItem({
    required this.imageUrl,
    required this.clipUrl,
    this.label = '',
    this.camera = '',
  });
}

class FullScreenGallery extends StatefulWidget {
  final List<GalleryItem> items;
  final int initialIndex;

  const FullScreenGallery({
    super.key,
    required this.items,
    this.initialIndex = 0,
  });

  @override
  State<FullScreenGallery> createState() => _FullScreenGalleryState();
}

class _FullScreenGalleryState extends State<FullScreenGallery> {
  late int _currentIndex;
  late PageController _pageController;
  final Map<int, TransformationController> _zoomControllers = {};

  Player? _videoPlayer;
  VideoController? _videoController;
  int? _videoPageIndex;
  bool _videoLoading = false;

  TransformationController _getZoomController(int index) {
    return _zoomControllers.putIfAbsent(index, () => TransformationController());
  }

  @override
  void initState() {
    super.initState();
    _currentIndex = widget.initialIndex;
    _pageController = PageController(initialPage: widget.initialIndex);
  }

  @override
  void dispose() {
    _pageController.dispose();
    _videoPlayer?.dispose();
    for (final c in _zoomControllers.values) {
      c.dispose();
    }
    super.dispose();
  }

  void _resetZoom(int index) {
    _getZoomController(index).value = Matrix4.identity();
  }

  void _disposeVideo() {
    _videoPlayer?.dispose();
    _videoPlayer = null;
    _videoController = null;
    _videoPageIndex = null;
    _videoLoading = false;
  }

  void _loadVideo(int index) {
    final item = widget.items[index];
    if (item.clipUrl.isEmpty) return;

    _disposeVideo();
    setState(() => _videoLoading = true);

    _videoPlayer = Player();
    _videoController = VideoController(_videoPlayer!);
    _videoPageIndex = index;

    _videoPlayer!.open(Media(item.clipUrl)).then((_) {
      if (mounted && _videoPageIndex == index) {
        setState(() => _videoLoading = false);
      }
    }).catchError((_) {
      if (mounted && _videoPageIndex == index) {
        setState(() => _videoLoading = false);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black54,
        foregroundColor: Colors.white,
        title: Text('${_currentIndex + 1} / ${widget.items.length}'),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => Navigator.of(context).pop(),
        ),
      ),
      body: PageView.builder(
        controller: _pageController,
        itemCount: widget.items.length,
        onPageChanged: (index) {
          _disposeVideo();
          setState(() => _currentIndex = index);
        },
        itemBuilder: (context, index) {
          final item = widget.items[index];

          if (_videoPageIndex == index &&
              _videoController != null &&
              !_videoLoading) {
            return _VideoPage(
              controller: _videoController!,
              label: item.label,
              camera: item.camera,
              onClose: () {
                setState(() => _disposeVideo());
              },
            );
          }

          return GestureDetector(
            onDoubleTap: () => _resetZoom(index),
            child: Stack(
              children: [
                InteractiveViewer(
                  transformationController: _getZoomController(index),
                  boundaryMargin: const EdgeInsets.all(double.infinity),
                  minScale: 1.0,
                  maxScale: 4.0,
                  child: Center(
                    child: CachedNetworkImage(
                      imageUrl: item.imageUrl,
                      fit: BoxFit.contain,
                      placeholder: (_, _) => const Center(
                        child:
                            CircularProgressIndicator(color: Colors.white54),
                      ),
                      errorWidget: (_, _, _) => const Center(
                        child: Icon(Icons.broken_image,
                            color: Colors.white38, size: 64),
                      ),
                    ),
                  ),
                ),
                if (item.clipUrl.isNotEmpty)
                  Positioned.fill(
                    child: Center(
                      child: _videoLoading
                          ? const CircularProgressIndicator(
                              color: Colors.white54)
                          : GestureDetector(
                              onTap: () => _loadVideo(index),
                              child: Container(
                                padding: const EdgeInsets.all(16),
                                decoration: BoxDecoration(
                                  color: Colors.black54,
                                  borderRadius: BorderRadius.circular(40),
                                ),
                                child: const Icon(
                                  Icons.play_circle_fill,
                                  color: Colors.white,
                                  size: 56,
                                ),
                              ),
                            ),
                    ),
                  ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _VideoPage extends StatelessWidget {
  final VideoController controller;
  final String label;
  final String camera;
  final VoidCallback onClose;

  const _VideoPage({
    required this.controller,
    required this.label,
    required this.camera,
    required this.onClose,
  });

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        Center(
          child: AspectRatio(
            aspectRatio: 16 / 9,
            child: Video(controller: controller),
          ),
        ),
        Positioned(
          top: 8,
          right: 8,
          child: FloatingActionButton.small(
            backgroundColor: Colors.black54,
            onPressed: onClose,
            child: const Icon(Icons.close, color: Colors.white),
          ),
        ),
      ],
    );
  }
}
