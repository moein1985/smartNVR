# Phase 4: Flutter Client (Mobile + Desktop) — Detailed Roadmap

**Status:** ✅ Completed  
**Date Completed:** July 2026

## Architectural Pivots (Phase 4)
- **MockApiClient** added for offline development — returns hardcoded test data with picsum.photos images when `isMockMode == true`.
- **Row parsing fix:** Backend returns `rows` as `list[list[Any]]` (arrays), not `list[map]`. `eventRows` getter in `chat_provider.dart` zips `columns` with each row to produce maps. Handles both List-rows (real) and Map-rows (mock).
- **Image URL fix:** Changed from hardcoded `http://192.168.85.203:5000/...` to dynamic `http://$serverIp:5000/...` using `serverConfigProvider`. `errorBuilder` shows `broken_image` icon instead of falling back to picsum.photos.
- Server IP/port configurable via in-app Settings page, persisted with SharedPreferences.

---

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
flutter pub add dio flutter_riverpod speech_to_text flutter_markdown cached_network_image shared_preferences
```

**Directory Structure:**
```
frigate_app/
├── lib/
│   ├── main.dart
│   ├── app.dart
│   ├── core/
│   │   ├── config/
│   │   │   ├── app_config.dart          # Server config model (IP, Port)
│   │   │   └── server_config_service.dart  # SharedPreferences persistence
│   │   ├── theme/
│   │   │   └── app_theme.dart
│   │   └── utils/
│   │       └── timestamp_utils.dart
│   ├── data/
│   │   ├── datasources/
│   │   │   └── api_client.dart          # Dio HTTP client (dynamic base URL)
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
│   │   │   └── settings_page.dart       # Server config UI (IP + Port)
│   │   ├── widgets/
│   │   │   ├── chat_bubble.dart
│   │   │   ├── sql_result_table.dart
│   │   │   ├── voice_input_button.dart
│   │   │   └── event_image.dart
│   │   └── providers/
│   │       ├── chat_provider.dart
│   │       ├── events_provider.dart
│   │       └── server_config_provider.dart  # Riverpod state for server config
│   └── l10n/
│       ├── app_fa.arb                   # Persian strings
│       └── app_en.arb                   # English strings
├── pubspec.yaml
└── test/
```

---

## Step 4.2: Server Configuration — Persistence Layer

**File: `lib/core/config/app_config.dart`**

```dart
class ServerConfig {
  final String ip;
  final int port;

  const ServerConfig({required this.ip, required this.port});

  String get baseUrl => 'http://$ip:$port';

  @override
  bool operator ==(Object other) =>
      other is ServerConfig && other.ip == ip && other.port == port;

  @override
  int get hashCode => Object.hash(ip, port);
}
```

**File: `lib/core/config/server_config_service.dart`**

```dart
import 'package:shared_preferences/shared_preferences.dart';
import 'app_config.dart';

class ServerConfigService {
  static const _keyIp = 'server_ip';
  static const _keyPort = 'server_port';

  // Default fallback — used on first launch
  static const ServerConfig _default = ServerConfig(ip: '192.168.85.203', port: 8088);

  Future<ServerConfig> load() async {
    final prefs = await SharedPreferences.getInstance();
    final ip = prefs.getString(_keyIp) ?? _default.ip;
    final port = prefs.getInt(_keyPort) ?? _default.port;
    return ServerConfig(ip: ip, port: port);
  }

  Future<void> save(ServerConfig config) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyIp, config.ip);
    await prefs.setInt(_keyPort, config.port);
  }
}
```

**`pubspec.yaml` dependency:**
```yaml
dependencies:
  shared_preferences: ^2.2.3
```

---

## Step 4.3: Dynamic API Client

**File: `lib/data/datasources/api_client.dart`**

The `ApiClient` no longer takes a hardcoded base URL. Instead, it accepts a `ServerConfig` and rebuilds the Dio instance whenever the config changes.

```dart
import 'package:dio/dio.dart';
import '../../core/config/app_config.dart';

class ApiClient {
  Dio _dio;

  ApiClient(ServerConfig config)
      : _dio = _createDio(config);

  static Dio _createDio(ServerConfig config) {
    return Dio(BaseOptions(
      baseUrl: config.baseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 30),
    ));
  }

  /// Called when the user updates server IP/Port at runtime.
  void updateConfig(ServerConfig config) {
    _dio = _createDio(config);
  }

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

## Step 4.4: Server Config State Management (Riverpod)

**File: `lib/presentation/providers/server_config_provider.dart`**

Riverpod providers that:
1. Load the saved config from `SharedPreferences` at startup.
2. Expose a reactive `ServerConfig` to the entire app.
3. Recreate the `ApiClient` whenever the config changes.

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/config/app_config.dart';
import '../../core/config/server_config_service.dart';
import '../../data/datasources/api_client.dart';

/// Service singleton
final serverConfigServiceProvider = Provider<ServerConfigService>((ref) {
  return ServerConfigService();
});

/// Async config loaded from SharedPreferences on startup
final serverConfigProvider = FutureProvider<ServerConfig>((ref) async {
  final service = ref.watch(serverConfigServiceProvider);
  return service.load();
});

/// ApiClient that reactively rebuilds when server config changes
final apiClientProvider = Provider<ApiClient>((ref) {
  final configAsync = ref.watch(serverConfigProvider);
  return configAsync.maybeWhen(
    data: (config) => ApiClient(config),
    orElse: () => ApiClient(const ServerConfig(ip: '0.0.0.0', port: 0)),
  );
});

/// Notifier to update and persist server config
final serverConfigNotifierProvider =
    StateNotifierProvider<ServerConfigNotifier, AsyncValue<ServerConfig>>((ref) {
  return ServerConfigNotifier(ref);
});

class ServerConfigNotifier extends StateNotifier<AsyncValue<ServerConfig>> {
  final Ref _ref;

  ServerConfigNotifier(this._ref) : super(const AsyncValue.loading()) {
    _init();
  }

  Future<void> _init() async {
    final service = _ref.read(serverConfigServiceProvider);
    final config = await service.load();
    state = AsyncValue.data(config);
  }

  Future<void> updateAndSave(ServerConfig newConfig) async {
    final service = _ref.read(serverConfigServiceProvider);
    await service.save(newConfig);
    state = AsyncValue.data(newConfig);
    // ref.watch in apiClientProvider will trigger rebuild automatically
  }
}
```

---

## Step 4.5: Settings Page (Server Configuration UI)

**File: `lib/presentation/pages/settings_page.dart`**

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/config/app_config.dart';
import '../providers/server_config_provider.dart';

class SettingsPage extends ConsumerStatefulWidget {
  const SettingsPage({super.key});

  @override
  ConsumerState<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends ConsumerState<SettingsPage> {
  late TextEditingController _ipController;
  late TextEditingController _portController;
  ConnectionStatus _status = ConnectionStatus.idle;

  @override
  void initState() {
    super.initState();
    _ipController = TextEditingController();
    _portController = TextEditingController();
    // Pre-fill from current config
    ref.read(serverConfigProvider).whenData((config) {
      _ipController.text = config.ip;
      _portController.text = config.port.toString();
    });
  }

  Future<void> _testAndSave() async {
    final ip = _ipController.text.trim();
    final port = int.tryParse(_portController.text.trim()) ?? 0;
    if (ip.isEmpty || port == 0) return;

    setState(() => _status = ConnectionStatus.connecting);

    final config = ServerConfig(ip: ip, port: port);
    final apiClient = ApiClient(config);

    try {
      final health = await apiClient.health();
      final isOk = health['status'] == 'ok';
      setState(() => _status = isOk ? ConnectionStatus.connected : ConnectionStatus.failed);

      if (isOk) {
        // Persist and update app state reactively
        await ref.read(serverConfigNotifierProvider.notifier).updateAndSave(config);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('اتصال موفق بود و تنظیمات ذخیره شد')),
          );
        }
      }
    } catch (e) {
      setState(() => _status = ConnectionStatus.failed);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('تنظیمات سرور')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('آدرس IP سرور', style: Theme.of(context).textTheme.labelLarge),
            const SizedBox(height: 8),
            TextField(
              controller: _ipController,
              decoration: const InputDecoration(
                hintText: '192.168.85.203',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.dns),
              ),
              keyboardType: TextInputType.number,
            ),
            const SizedBox(height: 20),
            Text('پورت', style: Theme.of(context).textTheme.labelLarge),
            const SizedBox(height: 8),
            TextField(
              controller: _portController,
              decoration: const InputDecoration(
                hintText: '8088',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.router),
              ),
              keyboardType: TextInputType.number,
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: _status == ConnectionStatus.connecting ? null : _testAndSave,
                icon: const Icon(Icons.save),
                label: const Text('ذخیره و اتصال'),
              ),
            ),
            const SizedBox(height: 16),
            _StatusIndicator(status: _status),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _ipController.dispose();
    _portController.dispose();
    super.dispose();
  }
}

enum ConnectionStatus { idle, connecting, connected, failed }

class _StatusIndicator extends StatelessWidget {
  final ConnectionStatus status;
  const _StatusIndicator({required this.status});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(
          switch (status) {
            ConnectionStatus.idle => Icons.circle_outlined,
            ConnectionStatus.connecting => Icons.sync,
            ConnectionStatus.connected => Icons.check_circle,
            ConnectionStatus.failed => Icons.error,
          },
          color: switch (status) {
            ConnectionStatus.idle => Colors.grey,
            ConnectionStatus.connecting => Colors.orange,
            ConnectionStatus.connected => Colors.green,
            ConnectionStatus.failed => Colors.red,
          },
        ),
        const SizedBox(width: 8),
        Text(switch (status) {
          ConnectionStatus.idle => 'آماده',
          ConnectionStatus.connecting => 'در حال اتصال...',
          ConnectionStatus.connected => 'متصل ✓',
          ConnectionStatus.failed => 'اتصال ناموفق ✗',
        }),
      ],
    );
  }
}
```

**Key UI features:**
- **Server IP** text field with `TextInputType.number` and DNS icon
- **Port** text field with router icon
- **"Save / Connect"** button that tests the connection via `/api/v1/health` before persisting
- **Status indicator** with 4 states: idle (grey), connecting (orange spinner), connected (green check), failed (red error)
- **Persian RTL labels** for localization consistency
- **Pre-fills** fields with the current saved config on load

---

## Step 4.6: Chat Page (Main UI)

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

## Step 4.7: Voice Input

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

## Step 4.8: Event Image Display

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

## Step 4.9: State Management (Riverpod)

**File: `lib/presentation/providers/chat_provider.dart`**

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/datasources/api_client.dart';
import 'server_config_provider.dart';

// ChatNotifier consumes the reactive apiClientProvider,
// so it automatically points to the user's saved server config.
final chatNotifierProvider = StateNotifierProvider<ChatNotifier, ChatState>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return ChatNotifier(apiClient);
});

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

## Step 4.10: Push Notifications

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

## Step 4.11: Desktop Support (Windows)

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
- [ ] Settings page for Server IP + Port configuration with connection health indicator
- [ ] Server config persisted across app restarts via SharedPreferences
- [ ] ApiClient reactively rebuilds when user updates IP/Port in Settings

**Verification:**
```bash
flutter run -d windows    # Desktop
flutter run -d chrome     # Web (fallback)
flutter run -d <device>   # Mobile
```
