import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:media_kit_video/media_kit_video.dart';
import '../providers/live_stream_provider.dart';
import '../providers/server_config_provider.dart';

class LiveViewTab extends ConsumerStatefulWidget {
  const LiveViewTab({super.key});

  @override
  ConsumerState<LiveViewTab> createState() => _LiveViewTabState();
}

class _LiveViewTabState extends ConsumerState<LiveViewTab> {
  final Map<String, LiveStreamController> _controllers = {};
  final Map<String, VideoController> _videoControllers = {};
  final Map<String, StreamStatus> _statuses = {};
  final Map<String, String> _errors = {};

  @override
  void dispose() {
    for (final c in _controllers.values) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _connectStream(String cameraName, String serverIp) async {
    if (_controllers.containsKey(cameraName)) return;

    final controller = LiveStreamController(
      serverIp: serverIp,
      cameraName: cameraName,
    );
    _controllers[cameraName] = controller;

    setState(() => _statuses[cameraName] = StreamStatus.connecting);

    try {
      final vc = await controller.startStream();
      if (mounted) {
        setState(() {
          _videoControllers[cameraName] = vc;
          _statuses[cameraName] = StreamStatus.connected;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _statuses[cameraName] = StreamStatus.error;
          _errors[cameraName] = e.toString();
        });
      }
    }
  }

  void _disconnectStream(String cameraName) {
    _controllers[cameraName]?.dispose();
    _controllers.remove(cameraName);
    _videoControllers.remove(cameraName);
    setState(() {
      _statuses.remove(cameraName);
      _errors.remove(cameraName);
    });
  }

  @override
  Widget build(BuildContext context) {
    final camerasAsync = ref.watch(cameraListProvider);
    final configAsync = ref.watch(serverConfigProvider);
    final serverIp = configAsync.maybeWhen(
      data: (c) => c.ip,
      orElse: () => '',
    );

    return camerasAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (err, _) => Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.cloud_off, size: 48),
            const SizedBox(height: 12),
            Text('خطا در دریافت لیست دوربین‌ها'),
            const SizedBox(height: 8),
            FilledButton(
              onPressed: () => ref.invalidate(cameraListProvider),
              child: const Text('تلاش مجدد'),
            ),
          ],
        ),
      ),
      data: (cameras) {
        if (cameras.isEmpty) {
          return const Center(child: Text('هیچ دوربینی پیکربندی نشده است'));
        }

        return GridView.builder(
          padding: const EdgeInsets.all(8),
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 2,
            childAspectRatio: 16 / 11,
            crossAxisSpacing: 8,
            mainAxisSpacing: 8,
          ),
          itemCount: cameras.length,
          itemBuilder: (context, index) {
            final cam = cameras[index];
            return _CameraCell(
              cameraName: cam.name,
              status: _statuses[cam.name] ?? StreamStatus.idle,
              errorMessage: _errors[cam.name] ?? '',
              videoController: _videoControllers[cam.name],
              onTap: () {
                final status = _statuses[cam.name];
                if (status == StreamStatus.connected ||
                    status == StreamStatus.connecting) {
                  _disconnectStream(cam.name);
                } else {
                  _connectStream(cam.name, serverIp);
                }
              },
              onFullscreen: _videoControllers[cam.name] != null
                  ? () => _openFullscreen(context, cam.name)
                  : null,
            );
          },
        );
      },
    );
  }

  void _openFullscreen(BuildContext context, String cameraName) {
    final vc = _videoControllers[cameraName];
    if (vc == null) return;

    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => Scaffold(
          backgroundColor: Colors.black,
          appBar: AppBar(
            backgroundColor: Colors.black54,
            foregroundColor: Colors.white,
            title: Text(cameraName),
          ),
          body: Center(
            child: Video(controller: vc),
          ),
        ),
      ),
    );
  }
}

class _CameraCell extends StatelessWidget {
  final String cameraName;
  final StreamStatus status;
  final String errorMessage;
  final VideoController? videoController;
  final VoidCallback onTap;
  final VoidCallback? onFullscreen;

  const _CameraCell({
    required this.cameraName,
    required this.status,
    required this.errorMessage,
    required this.videoController,
    required this.onTap,
    this.onFullscreen,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return ClipRRect(
      borderRadius: BorderRadius.circular(12),
      child: Stack(
        fit: StackFit.expand,
        children: [
          if (videoController != null && status == StreamStatus.connected)
            Video(controller: videoController!)
          else
            Container(color: colorScheme.surfaceContainerHighest),

          if (status == StreamStatus.connecting)
            Container(
              color: Colors.black38,
              child: const Center(
                child: CircularProgressIndicator(color: Colors.white70),
              ),
            ),

          if (status == StreamStatus.error)
            Container(
              color: Colors.black54,
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.error_outline, color: Colors.white54, size: 32),
                    const SizedBox(height: 4),
                    Text('خطا', style: TextStyle(color: Colors.white54, fontSize: 12)),
                  ],
                ),
              ),
            ),

          Positioned(
            top: 8,
            left: 8,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.black54,
                borderRadius: BorderRadius.circular(6),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    status == StreamStatus.connected
                        ? Icons.circle
                        : status == StreamStatus.connecting
                            ? Icons.circle_outlined
                            : Icons.circle_outlined,
                    size: 8,
                    color: status == StreamStatus.connected
                        ? Colors.green
                        : status == StreamStatus.connecting
                            ? Colors.orange
                            : Colors.white38,
                  ),
                  const SizedBox(width: 4),
                  Text(
                    cameraName,
                    style: const TextStyle(color: Colors.white, fontSize: 12),
                  ),
                ],
              ),
            ),
          ),

          if (status == StreamStatus.connected && onFullscreen != null)
            Positioned(
              top: 8,
              right: 8,
              child: GestureDetector(
                onTap: onFullscreen,
                child: Container(
                  padding: const EdgeInsets.all(4),
                  decoration: BoxDecoration(
                    color: Colors.black54,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: const Icon(Icons.fullscreen, color: Colors.white, size: 18),
                ),
              ),
            ),

          if (status == StreamStatus.idle || status == StreamStatus.error)
            Center(
              child: GestureDetector(
                onTap: onTap,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  decoration: BoxDecoration(
                    color: Colors.black54,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        status == StreamStatus.error ? Icons.refresh : Icons.play_arrow,
                        color: Colors.white,
                        size: 18,
                      ),
                      const SizedBox(width: 4),
                      Text(
                        status == StreamStatus.error ? 'تلاش مجدد' : 'اتصال',
                        style: const TextStyle(color: Colors.white, fontSize: 13),
                      ),
                    ],
                  ),
                ),
              ),
            ),

          if (status == StreamStatus.connected)
            Positioned(
              bottom: 8,
              right: 8,
              child: GestureDetector(
                onTap: onTap,
                child: Container(
                  padding: const EdgeInsets.all(4),
                  decoration: BoxDecoration(
                    color: Colors.black54,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: const Icon(Icons.close, color: Colors.white, size: 18),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
