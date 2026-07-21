class PlaybackParams {
  final String camera;
  final String date;
  final double startTime;
  final double endTime;

  PlaybackParams({
    required this.camera,
    required this.date,
    required this.startTime,
    required this.endTime,
  });

  factory PlaybackParams.fromJson(Map<String, dynamic> json) {
    return PlaybackParams(
      camera: json['camera']?.toString() ?? 'cam1',
      date: json['date']?.toString() ?? '',
      startTime: (json['start_time'] as num?)?.toDouble() ?? 0,
      endTime: (json['end_time'] as num?)?.toDouble() ?? 0,
    );
  }

  @override
  bool operator ==(Object other) =>
      other is PlaybackParams &&
      other.camera == camera &&
      other.date == date &&
      other.startTime == startTime &&
      other.endTime == endTime;

  @override
  int get hashCode => Object.hash(camera, date, startTime, endTime);
}
