import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import '../providers/chat_provider.dart';

class ChatBubble extends StatelessWidget {
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
  Widget build(BuildContext context) {
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

    return Wrap(
      spacing: 10,
      runSpacing: 10,
      children: rows.map((row) {
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
              ClipRRect(
                borderRadius: const BorderRadius.vertical(
                  top: Radius.circular(24),
                ),
                child: isMockMode
                    ? Image.network(
                        'https://picsum.photos/seed/$eventId/400/300',
                        width: 160,
                        height: 110,
                        fit: BoxFit.cover,
                        errorBuilder: (_, _, _) => Container(
                          width: 160,
                          height: 110,
                          color: colorScheme.surfaceContainerHighest,
                          child: Icon(Icons.broken_image,
                              color: colorScheme.outline),
                        ),
                      )
                    : Image.network(
                        'http://$serverIp:5000/api/events/$eventId/snapshot.jpg',
                        width: 160,
                        height: 110,
                        fit: BoxFit.cover,
                        errorBuilder: (_, _, _) => Container(
                          width: 160,
                          height: 110,
                          color: colorScheme.surfaceContainerHighest,
                          child: Icon(Icons.broken_image,
                              color: colorScheme.outline),
                        ),
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
