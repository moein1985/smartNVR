import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'server_config_provider.dart';

class RecordingSegment {
  final String id;
  final String camera;
  final String path;
  final double startTime;
  final double endTime;
  final double duration;
  final int? objects;
  final int? motion;

  RecordingSegment({
    required this.id,
    required this.camera,
    required this.path,
    required this.startTime,
    required this.endTime,
    required this.duration,
    this.objects,
    this.motion,
  });

  factory RecordingSegment.fromJson(Map<String, dynamic> json) {
    return RecordingSegment(
      id: json['id']?.toString() ?? '',
      camera: json['camera']?.toString() ?? '',
      path: json['path']?.toString() ?? '',
      startTime: (json['start_time'] as num?)?.toDouble() ?? 0,
      endTime: (json['end_time'] as num?)?.toDouble() ?? 0,
      duration: (json['duration'] as num?)?.toDouble() ?? 0,
      objects: json['objects'] as int?,
      motion: json['motion'] as int?,
    );
  }
}

class RecordingQuery {
  final String camera;
  final String date;
  final int? hour;

  RecordingQuery({required this.camera, required this.date, this.hour});

  @override
  bool operator ==(Object other) =>
      other is RecordingQuery &&
      other.camera == camera &&
      other.date == date &&
      other.hour == hour;

  @override
  int get hashCode => Object.hash(camera, date, hour);
}

final recordingListProvider =
    FutureProvider.family<List<RecordingSegment>, RecordingQuery>((ref, query) async {
  final apiClient = ref.watch(apiClientProvider);
  final result = await apiClient.getRecordings(
    camera: query.camera,
    date: query.date,
    hour: query.hour,
  );
  final segments = result['segments'] as List? ?? [];
  return segments
      .map((s) => RecordingSegment.fromJson(s as Map<String, dynamic>))
      .toList();
});
