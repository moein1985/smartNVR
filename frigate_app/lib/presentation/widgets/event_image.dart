import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';

class EventImage extends StatelessWidget {
  final String eventId;
  final String? frigateUrl;
  final bool isMockMode;
  final double borderRadius;

  const EventImage({
    super.key,
    required this.eventId,
    this.frigateUrl,
    this.isMockMode = false,
    this.borderRadius = 24,
  });

  String get _fallbackUrl => 'https://picsum.photos/seed/$eventId/400/300';

  String get _frigateSnapshotUrl =>
      '${frigateUrl ?? 'http://192.168.85.203:5000'}/api/events/$eventId/snapshot.jpg';

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    final imageUrl = isMockMode ? _fallbackUrl : _frigateSnapshotUrl;

    return ClipRRect(
      borderRadius: BorderRadius.circular(borderRadius),
      child: CachedNetworkImage(
        imageUrl: imageUrl,
        fit: BoxFit.cover,
        placeholder: (context, url) => Container(
          color: colorScheme.surfaceContainerHighest,
          child: Center(
            child: SizedBox(
              width: 24,
              height: 24,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                color: colorScheme.primary,
              ),
            ),
          ),
        ),
        errorWidget: (context, url, error) {
          if (url != _fallbackUrl) {
            return CachedNetworkImage(
              imageUrl: _fallbackUrl,
              fit: BoxFit.cover,
              placeholder: (context, url) => Container(
                color: colorScheme.surfaceContainerHighest,
                child: Center(
                  child: SizedBox(
                    width: 24,
                    height: 24,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: colorScheme.primary,
                    ),
                  ),
                ),
              ),
              errorWidget: (context, url, error) => Container(
                color: colorScheme.surfaceContainerHighest,
                child: Icon(Icons.broken_image, color: colorScheme.outline),
              ),
            );
          }
          return Container(
            color: colorScheme.surfaceContainerHighest,
            child: Icon(Icons.broken_image, color: colorScheme.outline),
          );
        },
      ),
    );
  }
}
