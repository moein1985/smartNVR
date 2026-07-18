# Phase 4: Flutter Client (Mobile + Desktop) — Detailed Roadmap

## Objective

Build a cross-platform Flutter application (Android, iOS, Windows, macOS) that:
1. Provides a chat interface for natural language queries
2. Supports voice input (speech-to-text)
3. Displays event images/snapshots from Frigate
4. Receives push notifications for new detections

---

## Prerequisites

- Phase 2 complete (REST API running)
- Flutter SDK 3.22+ installed
- Dart 3.4+ installed

---

## Step 4.1: Flutter Project Scaffolding

```bash
flutter create --org com.frigate --project-name frigate_intelligence frigate_app
cd frigate_app
flutter pub add dio flutter_riverpod speech_to_text flutter_markdown cached_network_image
```

**Directory Structure:**
```
frigate_app/
├── lib/
│   ├── main.dart
│   ├── app.dart
│   ├── core/
│   │   ├── config/
│   │   │   └── app_config.dart          # API base URL, settings
│   │   ├── theme/
│   │   │   └── app_theme.dart
│   │   └── utils/
│   │       └── timestamp_utils.dart
│   ├── data/
│   │   ├── datasources/
│   │   │   └── api_client.dart          # Dio HTTP client
│   │   ├── models/
│   │   │   ├── query_request.dart
│   │   │   ├── query_response.dart
│   │   │   └── event_model.dart
│   │   └── repositories/
│   │       └── intelligence_repository.dart
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── query_result.dart
│   │   │   └── camera_event.dart
│   │   └── usecases/
│   │       ├── query_usecase.dart
│   │       └── voice_input_usecase.dart
│   ├── presentation/
│   │   ├── pages/
│   │   │   ├── chat_page.dart
│   │   │   ├── events_page.dart
│   │   │   └── settings_page.dart
│   │   ├── widgets/
│   │   │   ├── chat_bubble.dart
│   │   │   ├── sql_result_table.dart
│   │   │   ├── voice_input_button.dart
│   │   │   └── event_image.dart
│   │   └── providers/
│   │       ├── chat_provider.dart
│   │       └── events_provider.dart
│   └── l10n/
│       ├── app_fa.arb                   # Persian strings
│       └── app_en.arb                   # English strings
├── pubspec.yaml
└── test/
```

---

## Step 4.2: API Client

**File: `lib/data/datasources/api_client.dart`**

```dart
import 'package:dio/dio.dart';

class ApiClient {
  final Dio _dio;

  ApiClient(String baseUrl)
      : _dio = Dio(BaseOptions(
          baseUrl: baseUrl,
          connectTimeout: const Duration(seconds: 10),
          receiveTimeout: const Duration(seconds: 30),
        ));

  Future<Map<String, dynamic>> query(String question) async {
    final response = await _dio.post('/api/v1/query', data: {
      'question': question,
    });
    return response.data;
  }

  Future<List<Map<String, dynamic>>> getEvents({
    String? camera,
    String? label,
  }) async {
    final response = await _dio.get('/api/v1/events', queryParameters: {
      if (camera != null) 'camera': camera,
      if (label != null) 'label': label,
    });
    return List<Map<String, dynamic>>.from(response.data['events']);
  }

  Future<Map<String, dynamic>> health() async {
    final response = await _dio.get('/api/v1/health');
    return response.data;
  }
}
```

---

## Step 4.3: Chat Page (Main UI)

**File: `lib/presentation/pages/chat_page.dart`**

Features:
- Chat bubble list (user questions + AI responses)
- Text input field with send button
- Voice input button (microphone icon)
- Markdown rendering for AI responses
- SQL result table widget
- Loading indicator during query processing

**Key widgets:**
- `ChatBubble` — renders message with avatar (user vs AI)
- `SQLResultTable` — renders query results as DataTable
- `VoiceInputButton` — tap to record, release to send
- `EventImage` — loads thumbnail from Frigate API

---

## Step 4.4: Voice Input

**File: `lib/domain/usecases/voice_input_usecase.dart`**

```dart
import 'package:speech_to_text/speech_to_text.dart';

class VoiceInputUseCase {
  final SpeechToText _speech = SpeechToText();

  Future<bool> initialize() async {
    return await _speech.initialize();
  }

  Future<String> listen({String localeId = 'fa_IR'}) async {
    final completer = Completer<String>();
    _speech.listen(
      localeId: localeId,
      onResult: (result) {
        if (result.finalResult) {
          completer.complete(result.recognizedWords);
        }
      },
    );
    return completer.future;
  }

  void stop() {
    _speech.stop();
  }
}
```

---

## Step 4.5: Event Image Display

**File: `lib/presentation/widgets/event_image.dart`**

```dart
import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';

class EventImage extends StatelessWidget {
  final String eventId;
  final String frigateUrl;

  const EventImage({
    super.key,
    required this.eventId,
    required this.frigateUrl,
  });

  @override
  Widget build(BuildContext context) {
    final thumbnailUrl = '$frigateUrl/api/events/$eventId/thumbnail';
    return ClipRRect(
      borderRadius: BorderRadius.circular(8),
      child: CachedNetworkImage(
        imageUrl: thumbnailUrl,
        placeholder: (context, url) => const CircularProgressIndicator(),
        errorWidget: (context, url, error) => const Icon(Icons.error),
        fit: BoxFit.cover,
      ),
    );
  }
}
```

---

## Step 4.6: State Management (Riverpod)

**File: `lib/presentation/providers/chat_provider.dart`**

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/datasources/api_client.dart';

class ChatState {
  final List<ChatMessage> messages;
  final bool isLoading;
  ChatState({this.messages = const [], this.isLoading = false});
}

class ChatMessage {
  final String text;
  final bool isUser;
  final Map<String, dynamic>? queryResult;
  ChatMessage({required this.text, required this.isUser, this.queryResult});
}

class ChatNotifier extends StateNotifier<ChatState> {
  final ApiClient _api;

  ChatNotifier(this._api) : super(ChatState());

  Future<void> sendQuestion(String question) async {
    state = ChatState(
      messages: [...state.messages, ChatMessage(text: question, isUser: true)],
      isLoading: true,
    );
    try {
      final result = await _api.query(question);
      state = ChatState(
        messages: [...state.messages, ChatMessage(
          text: result['explanation'],
          isUser: false,
          queryResult: result,
        )],
        isLoading: false,
      );
    } catch (e) {
      state = ChatState(
        messages: [...state.messages, ChatMessage(text: 'خطا: $e', isUser: false)],
        isLoading: false,
      );
    }
  }
}
```

---

## Step 4.7: Push Notifications

**Dependencies:**
```yaml
# pubspec.yaml
firebase_messaging: ^15.0.0  # Android/iOS
flutter_local_notifications: ^17.0.0  # All platforms
```

**Backend addition (Phase 2 API):**
- `POST /api/v1/devices/register` — register FCM/APNs token
- Backend sends push when Frigate webhook fires

---

## Step 4.8: Desktop Support (Windows)

```bash
flutter config --enable-windows-desktop
flutter create --platforms=windows .
```

Windows-specific:
- Use `window_manager` for window size control
- System tray integration with `tray_manager`
- Auto-start with Windows

---

## Acceptance Criteria (Phase 4)

- [ ] Chat UI displays user questions and AI responses
- [ ] Voice input works in Persian (fa_IR locale)
- [ ] SQL results render as formatted tables
- [ ] Event thumbnails load from Frigate API
- [ ] App runs on Android, iOS, and Windows
- [ ] Dark/light theme support
- [ ] Persian (RTL) and English (LTR) localization
- [ ] Loading states during API calls
- [ ] Error handling with user-friendly messages
- [ ] Settings page for API URL configuration

**Verification:**
```bash
flutter run -d windows    # Desktop
flutter run -d chrome     # Web (fallback)
flutter run -d <device>   # Mobile
```
