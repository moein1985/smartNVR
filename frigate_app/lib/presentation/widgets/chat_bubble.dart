import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/chat_provider.dart';
import '../providers/navigation_provider.dart';
import '../models/playback_params.dart';
import 'full_screen_gallery.dart';
import 'inline_vod_player.dart';

class ChatBubble extends ConsumerWidget {
  final ChatMessage message;
  final bool isMockMode;
  final String serverIp;

  const ChatBubble({
    super.key,
    required this.message,
    this.isMockMode = false,
    this.serverIp = '',
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final isUser = message.isUser;

    return Align(
      alignment: isUser ? Alignment.centerLeft : Alignment.centerRight,
      child: Container(
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.82,
        ),
        margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 12),
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
        decoration: BoxDecoration(
          color: isUser
              ? colorScheme.primaryContainer
              : colorScheme.surfaceContainerHigh,
          borderRadius: isUser
              ? const BorderRadius.only(
                  topLeft: Radius.circular(28),
                  topRight: Radius.circular(28),
                  bottomRight: Radius.circular(28),
                  bottomLeft: Radius.circular(8),
                )
              : const BorderRadius.only(
                  topLeft: Radius.circular(28),
                  topRight: Radius.circular(28),
                  bottomLeft: Radius.circular(28),
                  bottomRight: Radius.circular(8),
                ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (isUser)
              Text(
                message.text,
                style: theme.textTheme.bodyLarge?.copyWith(
                  color: colorScheme.onPrimaryContainer,
                ),
              )
            else
              MarkdownBody(
                data: message.text,
                styleSheet: MarkdownStyleSheet(
                  p: theme.textTheme.bodyLarge?.copyWith(
                    color: colorScheme.onSurfaceVariant,
                  ),
                  code: theme.textTheme.bodySmall?.copyWith(
                    backgroundColor: colorScheme.surfaceContainerHighest,
                    color: colorScheme.primary,
                  ),
                ),
              ),
            if (message.hasEvents) ...[
              const SizedBox(height: 12),
              _EventGallery(message: message, isMockMode: isMockMode, serverIp: serverIp),
            ],
            if (message.isPlaybackQuery && message.playbackIntent != null) ...[
              const SizedBox(height: 12),
              _PlaybackDeepLinkButton(
                playbackIntent: message.playbackIntent!,
                ref: ref,
              ),
              const SizedBox(height: 8),
              InlineVodPlayer(
                params: PlaybackParams.fromJson(message.playbackIntent!),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _EventGallery extends StatelessWidget {
  final ChatMessage message;
  final bool isMockMode;
  final String serverIp;

  const _EventGallery({required this.message, required this.isMockMode, required this.serverIp});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final rows = message.eventRows;

    final galleryItems = rows.map((r) {
      final id = r['id']?.toString() ?? 'unknown';
      return GalleryItem(
        imageUrl: isMockMode
            ? 'https://picsum.photos/seed/$id/800/600'
            : 'http://$serverIp:5000/api/events/$id/snapshot.jpg',
        clipUrl: isMockMode
            ? 'https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4'
            : 'http://$serverIp:5000/api/events/$id/clip.mp4',
        label: r['label']?.toString() ?? '',
        camera: r['camera']?.toString() ?? '',
      );
    }).toList();

    return Wrap(
      spacing: 10,
      runSpacing: 10,
      children: rows.asMap().entries.map((entry) {
        final index = entry.key;
        final row = entry.value;
        final eventId = row['id']?.toString() ?? 'unknown';
        final camera = row['camera']?.toString() ?? '';
        final label = row['label']?.toString() ?? '';
        final time = row['start_time']?.toString() ?? '';

        return Container(
          width: 160,
          decoration: BoxDecoration(
            color: colorScheme.surfaceContainerHighest,
            borderRadius: BorderRadius.circular(24),
          ),
          clipBehavior: Clip.antiAlias,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              GestureDetector(
                onTap: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => FullScreenGallery(
                        items: galleryItems,
                        initialIndex: index,
                      ),
                    ),
                  );
                },
                child: Stack(
                  children: [
                    ClipRRect(
                      borderRadius: const BorderRadius.vertical(
                        top: Radius.circular(24),
                      ),
                      child: CachedNetworkImage(
                        imageUrl: isMockMode
                            ? 'https://picsum.photos/seed/$eventId/400/300'
                            : 'http://$serverIp:5000/api/events/$eventId/snapshot.jpg',
                        width: 160,
                        height: 110,
                        fit: BoxFit.cover,
                        placeholder: (_, _) => Container(
                          width: 160,
                          height: 110,
                          color: colorScheme.surfaceContainerHighest,
                          child: Center(
                            child: SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: colorScheme.outline,
                              ),
                            ),
                          ),
                        ),
                        errorWidget: (_, _, _) => Container(
                          width: 160,
                          height: 110,
                          color: colorScheme.surfaceContainerHighest,
                          child: Icon(Icons.broken_image,
                              color: colorScheme.outline),
                        ),
                      ),
                    ),
                    Positioned.fill(
                      child: Align(
                        alignment: Alignment.bottomRight,
                        child: Padding(
                          padding: const EdgeInsets.all(6),
                          child: GestureDetector(
                            onTap: () {
                              Navigator.of(context).push(
                                MaterialPageRoute(
                                  builder: (_) => FullScreenGallery(
                                    items: galleryItems,
                                    initialIndex: index,
                                  ),
                                ),
                              );
                            },
                            child: Container(
                              padding: const EdgeInsets.all(4),
                              decoration: BoxDecoration(
                                color: Colors.black54,
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: const Icon(Icons.play_circle_fill,
                                  color: Colors.white, size: 20),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              Padding(
                padding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(Icons.videocam,
                            size: 14, color: colorScheme.primary),
                        const SizedBox(width: 4),
                        Expanded(
                          child: Text(camera,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: theme.textTheme.labelSmall?.copyWith(
                                color: colorScheme.onSurfaceVariant,
                              )),
                        ),
                      ],
                    ),
                    const SizedBox(height: 2),
                    Row(
                      children: [
                        Icon(Icons.label,
                            size: 14, color: colorScheme.tertiary),
                        const SizedBox(width: 4),
                        Expanded(
                          child: Text('$label  $time',
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: theme.textTheme.labelSmall?.copyWith(
                                color: colorScheme.onSurfaceVariant,
                              )),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }
}

class _PlaybackDeepLinkButton extends StatelessWidget {
  final Map<String, dynamic> playbackIntent;
  final WidgetRef ref;

  const _PlaybackDeepLinkButton({required this.playbackIntent, required this.ref});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final camera = playbackIntent['camera']?.toString() ?? 'cam1';

    return SizedBox(
      width: double.infinity,
      child: FilledButton.tonalIcon(
        onPressed: () {
          final params = PlaybackParams.fromJson(playbackIntent);
          ref.read(navigationProvider.notifier).navigateToPlayback(params);
        },
        icon: Icon(Icons.play_circle_outline, size: 20, color: colorScheme.primary),
        label: Text(
          'پخش ویدیوی $camera',
          style: theme.textTheme.labelLarge?.copyWith(
            color: colorScheme.primary,
          ),
        ),
        style: FilledButton.styleFrom(
          backgroundColor: colorScheme.primaryContainer,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20),
          ),
        ),
      ),
    );
  }
}
