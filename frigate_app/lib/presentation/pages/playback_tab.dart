import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:media_kit/media_kit.dart';
import 'package:media_kit_video/media_kit_video.dart';
import 'package:intl/intl.dart';
import '../providers/live_stream_provider.dart';
import '../providers/recording_provider.dart';
import '../providers/server_config_provider.dart';
import '../widgets/timeline_widget.dart';

class PlaybackTab extends ConsumerStatefulWidget {
  const PlaybackTab({super.key});

  @override
  ConsumerState<PlaybackTab> createState() => _PlaybackTabState();
}

class _PlaybackTabState extends ConsumerState<PlaybackTab> {
  String? _selectedCamera;
  String _selectedDate = DateFormat('yyyy-MM-dd').format(DateTime.now());
  int? _selectedHour;
  List<RecordingSegment> _currentSegments = [];
  int _currentSegmentIndex = 0;

  Player? _player;
  VideoController? _videoController;
  bool _isPlaying = false;

  @override
  void dispose() {
    _player?.dispose();
    super.dispose();
  }

  Future<void> _initPlayer() async {
    _player = Player();
    _videoController = VideoController(_player!);
    _player!.stream.completed.listen((completed) {
      if (completed && mounted) {
        _playNextSegment();
      }
    });
    _player!.stream.playing.listen((playing) {
      if (mounted) setState(() => _isPlaying = playing);
    });
  }

  void _playSegment(int index) {
    if (index >= _currentSegments.length) {
      if (_selectedHour != null && _selectedHour! < 23) {
        setState(() => _selectedHour = _selectedHour! + 1);
      }
      return;
    }

    setState(() => _currentSegmentIndex = index);

    final segment = _currentSegments[index];
    final configAsync = ref.read(serverConfigProvider);
    final serverIp = configAsync.maybeWhen(
      data: (c) => c.ip,
      orElse: () => '',
    );
    final url = 'http://$serverIp:5000${segment.path}';

    _player?.open(Media(url));
  }

  void _playNextSegment() {
    _playSegment(_currentSegmentIndex + 1);
  }

  void _onHourSelected(int hour) {
    setState(() => _selectedHour = hour);
  }

  void _onSegmentSelected(RecordingSegment segment) {
    final index = _currentSegments.indexOf(segment);
    if (index >= 0) {
      _playSegment(index);
    }
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: DateTime.parse(_selectedDate),
      firstDate: DateTime(2026, 1, 1),
      lastDate: DateTime.now(),
    );
    if (picked != null) {
      setState(() {
        _selectedDate = DateFormat('yyyy-MM-dd').format(picked);
        _selectedHour = null;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final camerasAsync = ref.watch(cameraListProvider);

    if (_player == null) {
      _initPlayer();
    }

    return Column(
      children: [
        _buildControls(camerasAsync),
        Expanded(
          child: _currentSegments.isEmpty
              ? _buildEmptyState()
              : _buildPlayer(),
        ),
        if (_selectedCamera != null)
          _buildTimeline(),
      ],
    );
  }

  Widget _buildControls(AsyncValue<List<CameraInfo>> camerasAsync) {
    return Padding(
      padding: const EdgeInsets.all(12),
      child: Row(
        children: [
          Expanded(
            child: camerasAsync.when(
              loading: () => const SizedBox(
                height: 48,
                child: Center(child: CircularProgressIndicator()),
              ),
              error: (_, _) => const Text('خطا در دریافت دوربین‌ها'),
              data: (cameras) {
                return DropdownButton<String>(
                  value: _selectedCamera,
                  hint: const Text('انتخاب دوربین'),
                  isExpanded: true,
                  items: cameras.map((cam) {
                    return DropdownMenuItem(
                      value: cam.name,
                      child: Text(cam.name),
                    );
                  }).toList(),
                  onChanged: (value) {
                    setState(() {
                      _selectedCamera = value;
                      _selectedHour = null;
                    });
                  },
                );
              },
            ),
          ),
          const SizedBox(width: 12),
          OutlinedButton.icon(
            onPressed: _pickDate,
            icon: const Icon(Icons.calendar_today, size: 18),
            label: Text(_selectedDate),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    final theme = Theme.of(context);
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.history, size: 64, color: theme.colorScheme.outline),
          const SizedBox(height: 12),
          Text(
            _selectedCamera == null
                ? 'یک دوربین انتخاب کنید'
                : 'یک ساعت از خط زمانی انتخاب کنید',
            style: theme.textTheme.bodyLarge?.copyWith(
              color: theme.colorScheme.outline,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPlayer() {
    if (_videoController == null) {
      return const Center(child: CircularProgressIndicator());
    }

    return Column(
      children: [
        Expanded(
          child: Container(
            color: Colors.black,
            child: AspectRatio(
              aspectRatio: 16 / 9,
              child: Video(controller: _videoController!),
            ),
          ),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              IconButton(
                onPressed: () => _playSegment(0),
                icon: const Icon(Icons.skip_previous),
              ),
              IconButton(
                onPressed: () {
                  if (_isPlaying) {
                    _player?.pause();
                  } else {
                    _player?.play();
                  }
                },
                icon: Icon(_isPlaying ? Icons.pause : Icons.play_arrow),
              ),
              IconButton(
                onPressed: _playNextSegment,
                icon: const Icon(Icons.skip_next),
              ),
              const SizedBox(width: 12),
              Text(
                'بخش ${_currentSegmentIndex + 1} از ${_currentSegments.length}',
                style: Theme.of(context).textTheme.labelSmall,
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildTimeline() {
    if (_selectedCamera == null) return const SizedBox.shrink();

    final query = RecordingQuery(
      camera: _selectedCamera!,
      date: _selectedDate,
      hour: _selectedHour,
    );

    final segmentsAsync = ref.watch(recordingListProvider(query));

    return segmentsAsync.when(
      loading: () => const Padding(
        padding: EdgeInsets.all(16),
        child: Center(child: CircularProgressIndicator()),
      ),
      error: (err, _) => Padding(
        padding: const EdgeInsets.all(16),
        child: Text('خطا: $err'),
      ),
      data: (segments) {
        if (segments.isNotEmpty && _currentSegments != segments) {
          _currentSegments = segments;
          if (_currentSegmentIndex >= segments.length) {
            _currentSegmentIndex = 0;
          }
        }
        return TimelineWidget(
          camera: _selectedCamera!,
          date: _selectedDate,
          segments: segments,
          selectedHour: _selectedHour,
          onHourSelected: _onHourSelected,
          onSegmentSelected: _onSegmentSelected,
        );
      },
    );
  }
}
