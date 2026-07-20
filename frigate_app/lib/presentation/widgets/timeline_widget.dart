import 'dart:math';
import 'package:flutter/material.dart';
import '../providers/recording_provider.dart';

class TimelineWidget extends StatefulWidget {
  final String camera;
  final String date;
  final List<RecordingSegment> segments;
  final int? selectedHour;
  final Function(int hour) onHourSelected;
  final Function(RecordingSegment segment) onSegmentSelected;

  const TimelineWidget({
    super.key,
    required this.camera,
    required this.date,
    required this.segments,
    this.selectedHour,
    required this.onHourSelected,
    required this.onSegmentSelected,
  });

  @override
  State<TimelineWidget> createState() => _TimelineWidgetState();
}

class _TimelineWidgetState extends State<TimelineWidget> {
  final ScrollController _scrollController = ScrollController();
  static const double _hourWidth = 80.0;
  static const double _timelineHeight = 60.0;

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  Map<int, List<RecordingSegment>> get _segmentsByHour {
    final map = <int, List<RecordingSegment>>{};
    for (final seg in widget.segments) {
      final hour = _getHourFromTimestamp(seg.startTime);
      map.putIfAbsent(hour, () => []).add(seg);
    }
    return map;
  }

  int _getHourFromTimestamp(double timestamp) {
    final dt = DateTime.fromMillisecondsSinceEpoch((timestamp * 1000).toInt());
    return dt.hour;
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final segmentsByHour = _segmentsByHour;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Text(
            'خط زمانی - ${widget.date}',
            style: theme.textTheme.titleSmall,
          ),
        ),
        SizedBox(
          height: _timelineHeight + 24,
          child: ListView.builder(
            controller: _scrollController,
            scrollDirection: Axis.horizontal,
            itemCount: 24,
            itemBuilder: (context, hour) {
              final segs = segmentsByHour[hour] ?? [];
              final hasRecordings = segs.isNotEmpty;
              final hasObjects = segs.any((s) => (s.objects ?? 0) > 0);
              final isSelected = widget.selectedHour == hour;

              return GestureDetector(
                onTap: () {
                  widget.onHourSelected(hour);
                  if (segs.isNotEmpty) {
                    widget.onSegmentSelected(segs.first);
                  }
                },
                child: Container(
                  width: _hourWidth,
                  margin: const EdgeInsets.symmetric(horizontal: 2),
                  child: Column(
                    children: [
                      Container(
                        height: _timelineHeight,
                        decoration: BoxDecoration(
                          color: isSelected
                              ? colorScheme.primaryContainer
                              : hasObjects
                                  ? colorScheme.tertiaryContainer
                                  : hasRecordings
                                      ? colorScheme.secondaryContainer
                                      : colorScheme.surfaceContainerHighest,
                          borderRadius: BorderRadius.circular(8),
                          border: isSelected
                              ? Border.all(color: colorScheme.primary, width: 2)
                              : null,
                        ),
                        child: Stack(
                          children: [
                            if (hasRecordings)
                              CustomPaint(
                                size: Size(_hourWidth - 4, _timelineHeight - 4),
                                painter: _SegmentPainter(
                                  segments: segs,
                                  color: colorScheme.primary,
                                  objectColor: colorScheme.tertiary,
                                ),
                              ),
                            Center(
                              child: Text(
                                '${hour.toString().padLeft(2, '0')}:00',
                                style: theme.textTheme.labelSmall?.copyWith(
                                  color: hasRecordings
                                      ? colorScheme.onSecondaryContainer
                                      : colorScheme.outline,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        segs.isNotEmpty ? '${segs.length}' : '-',
                        style: theme.textTheme.labelSmall?.copyWith(
                          color: hasRecordings ? colorScheme.primary : colorScheme.outline,
                        ),
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}

class _SegmentPainter extends CustomPainter {
  final List<RecordingSegment> segments;
  final Color color;
  final Color objectColor;

  _SegmentPainter({
    required this.segments,
    required this.color,
    required this.objectColor,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (segments.isEmpty) return;

    final firstStart = segments.first.startTime;
    final lastEnd = segments.last.endTime;
    final totalDuration = (lastEnd - firstStart).clamp(1.0, double.infinity);

    for (final seg in segments) {
      final startX = ((seg.startTime - firstStart) / totalDuration) * size.width;
      final endX = ((seg.endTime - firstStart) / totalDuration) * size.width;
      final segWidth = max(endX - startX, 2.0);

      final paint = Paint()
        ..color = (seg.objects ?? 0) > 0 ? objectColor : color
        ..style = PaintingStyle.fill;

      canvas.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromLTWH(startX, size.height * 0.2, segWidth, size.height * 0.6),
          const Radius.circular(2),
        ),
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _SegmentPainter oldDelegate) =>
      segments != oldDelegate.segments;
}
