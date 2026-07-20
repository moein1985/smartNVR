import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'server_config_provider.dart';

class ChatMessage {
  final String text;
  final bool isUser;
  final Map<String, dynamic>? queryResult;

  ChatMessage({required this.text, required this.isUser, this.queryResult});

  bool get hasEvents {
    final result = queryResult;
    if (result == null) return false;
    final rows = result['rows'];
    if (rows is! List || rows.isEmpty) return false;
    final columns = result['columns'];
    if (columns is! List) return false;
    return columns.any((c) => c == 'id');
  }

  List<Map<String, dynamic>> get eventRows {
    final result = queryResult;
    if (result == null) return [];
    final rows = result['rows'];
    if (rows is! List || rows.isEmpty) return [];
    final columns = result['columns'];
    if (columns is! List || columns.isEmpty) return [];

    return rows.map((row) {
      if (row is Map<String, dynamic>) {
        return row;
      }
      if (row is List) {
        final map = <String, dynamic>{};
        for (var i = 0; i < row.length && i < columns.length; i++) {
          map[columns[i].toString()] = row[i];
        }
        return map;
      }
      return <String, dynamic>{};
    }).toList();
  }
}

class ChatState {
  final List<ChatMessage> messages;
  final bool isLoading;

  ChatState({this.messages = const [], this.isLoading = false});

  ChatState copyWith({
    List<ChatMessage>? messages,
    bool? isLoading,
  }) {
    return ChatState(
      messages: messages ?? this.messages,
      isLoading: isLoading ?? this.isLoading,
    );
  }
}

class ChatNotifier extends Notifier<ChatState> {
  @override
  ChatState build() {
    return ChatState(messages: [
      ChatMessage(
        text: 'سلام! من دستیار هوشمند Frigate هستم. می‌توانید سوالات خود درباره رویدادهای دوربین را بپرسید.',
        isUser: false,
      ),
    ]);
  }

  Future<void> sendMessage(String question) async {
    if (question.trim().isEmpty || state.isLoading) return;

    final userMsg = ChatMessage(text: question, isUser: true);
    state = state.copyWith(
      messages: [...state.messages, userMsg],
      isLoading: true,
    );

    try {
      final apiClient = ref.read(apiClientProvider);
      final result = await apiClient.query(question);

      final explanation = result['explanation'] as String? ?? '';
      state = state.copyWith(
        messages: [...state.messages, ChatMessage(
          text: explanation,
          isUser: false,
          queryResult: result,
        )],
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(
        messages: [...state.messages, ChatMessage(
          text: 'خطا در ارتباط با سرور: $e',
          isUser: false,
        )],
        isLoading: false,
      );
    }
  }
}

final chatNotifierProvider =
    NotifierProvider<ChatNotifier, ChatState>(ChatNotifier.new);
