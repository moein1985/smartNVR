import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/chat_provider.dart';
import '../providers/server_config_provider.dart';
import '../widgets/chat_bubble.dart';
import 'settings_page.dart';

class ChatPage extends ConsumerStatefulWidget {
  const ChatPage({super.key});

  @override
  ConsumerState<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends ConsumerState<ChatPage> {
  final TextEditingController _inputController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final FocusNode _inputFocus = FocusNode();

  @override
  void dispose() {
    _inputController.dispose();
    _scrollController.dispose();
    _inputFocus.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _sendMessage() async {
    final text = _inputController.text.trim();
    if (text.isEmpty) return;
    _inputController.clear();
    _scrollToBottom();
    await ref.read(chatNotifierProvider.notifier).sendMessage(text);
    _scrollToBottom();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final chatState = ref.watch(chatNotifierProvider);
    final configAsync = ref.watch(serverConfigProvider);
    final serverConfig = configAsync.maybeWhen(
      data: (c) => c,
      orElse: () => null,
    );
    final isMockMode = serverConfig?.isMockMode ?? false;
    final serverIp = serverConfig?.ip ?? '';

    return Scaffold(
      appBar: AppBar(
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: colorScheme.primaryContainer,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(Icons.smart_toy, color: colorScheme.onPrimaryContainer, size: 20),
            ),
            const SizedBox(width: 12),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Frigate Intelligence',
                    style: theme.textTheme.titleSmall),
                Text(
                  isMockMode ? 'حالت آفلاین - داده‌های تستی' : 'متصل به سرور',
                  style: theme.textTheme.labelSmall?.copyWith(
                    color: isMockMode ? colorScheme.tertiary : colorScheme.outline,
                  ),
                ),
              ],
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings_outlined),
            onPressed: () {
              Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const SettingsPage()),
              );
            },
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.symmetric(vertical: 12),
              itemCount: chatState.messages.length,
              itemBuilder: (context, index) {
                return ChatBubble(
                  message: chatState.messages[index],
                  isMockMode: isMockMode,
                  serverIp: serverIp,
                );
              },
            ),
          ),
          if (chatState.isLoading)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: colorScheme.primary,
                ),
              ),
            ),
          _buildInputBar(context),
        ],
      ),
    );
  }

  Widget _buildInputBar(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Container(
      color: colorScheme.surfaceContainer,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: SafeArea(
        top: false,
        child: Row(
          children: [
            IconButton.filled(
              onPressed: () {},
              icon: const Icon(Icons.mic_none, size: 22),
              style: IconButton.styleFrom(
                backgroundColor: colorScheme.surfaceContainerHighest,
                foregroundColor: colorScheme.onSurfaceVariant,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: TextField(
                controller: _inputController,
                focusNode: _inputFocus,
                textInputAction: TextInputAction.send,
                onSubmitted: (_) => _sendMessage(),
                decoration: InputDecoration(
                  hintText: 'سوال خود را بپرسید...',
                  hintStyle: TextStyle(color: colorScheme.outline),
                  suffixIcon: IconButton(
                    onPressed: _sendMessage,
                    icon: Icon(
                      Icons.send_rounded,
                      color: colorScheme.primary,
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
