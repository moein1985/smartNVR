import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:frigate_intelligence/data/datasources/api_client.dart';
import 'package:frigate_intelligence/presentation/providers/server_config_provider.dart';
import 'package:frigate_intelligence/presentation/providers/orchestrator_provider.dart';
import 'package:frigate_intelligence/presentation/pages/orchestrator_page.dart';

class _OrchestratorMockClient implements BaseApiClient {
  final Map<String, dynamic> _hardwareResponse;
  final Map<String, dynamic> _containersResponse;

  _OrchestratorMockClient({
    Map<String, dynamic>? hardwareResponse,
    Map<String, dynamic>? containersResponse,
  })  : _hardwareResponse = hardwareResponse ?? const {
          'cpu': {'cores': 8, 'utilization_pct': 35.5},
          'memory': {'total_gb': 16.0, 'available_gb': 8.5, 'used_pct': 46.9},
          'gpus': [
            {
              'index': 0,
              'name': 'NVIDIA GeForce RTX 4090',
              'memory_total_mb': 24564,
              'memory_used_mb': 2048,
              'gpu_utilization_pct': 22.0,
              'uuid': 'GPU-mock-abc',
            },
          ],
        },
        _containersResponse = containersResponse ?? const {
          'containers': [
            {
              'name': 'frigate-intelligence',
              'image': 'frigate-intelligence:latest',
              'status': 'running',
              'short_id': 'abc123',
              'ports': [
                {'container_port': '8000/tcp', 'host_ip': '0.0.0.0', 'host_port': '8088'},
              ],
            },
            {
              'name': 'frigate',
              'image': 'blakeblackshear/frigate:0.14',
              'status': 'exited',
              'short_id': 'def456',
              'ports': [],
            },
          ],
        };

  @override
  Future<Map<String, dynamic>> query(String question, {int maxRetries = 3}) async =>
      {'sql': '', 'explanation': '', 'columns': [], 'rows': [], 'row_count': 0, 'attempts': 1, 'error': null};

  @override
  Future<List<Map<String, dynamic>>> getEvents({String? camera, String? label}) async => [];

  @override
  Future<Map<String, dynamic>> health() async => {
    'status': 'ok',
    'version': '0.1.0',
    'db_connected': true,
    'server_timestamp': DateTime.now().millisecondsSinceEpoch / 1000.0,
    'server_timezone': 'UTC',
    'server_datetime_iso': DateTime.now().toUtc().toIso8601String(),
  };

  @override
  Future<Map<String, dynamic>> getCameras() async => {'cameras': [], 'total': 0};

  @override
  Future<Map<String, dynamic>> getRecordings({
    String? camera, String? date, int? hour, double? startTime, double? endTime,
  }) async => {'segments': [], 'total': 0, 'camera': camera ?? 'all'};

  @override
  Future<Map<String, dynamic>> getSettings() async => {
    'avalai_api_key': '', 'llm_model': 'gemini-2.5-flash',
    'telegram_enabled': false, 'telegram_bot_token': '', 'telegram_chat_id': '',
    'bale_enabled': false, 'bale_bot_token': '', 'bale_chat_id': '',
    'report_target': 'telegram', 'report_interval_hours': 24,
    'report_timezone': 'Asia/Tehran', 'log_level': 'INFO',
  };

  @override
  Future<Map<String, dynamic>> updateSettings(Map<String, dynamic> newSettings) async =>
      {'status': 'ok', 'message': 'Settings saved'};

  @override
  Future<String> getSystemLogs(int lines) async => 'Mock log line';

  @override
  Future<Map<String, dynamic>> uploadUpdate(File file) async =>
      {'status': 'ok', 'message': 'Update applied'};

  @override
  Future<Map<String, dynamic>> getHardware() async => _hardwareResponse;

  @override
  Future<Map<String, dynamic>> getContainers({bool allStatuses = false}) async =>
      _containersResponse;

  @override
  Future<Map<String, dynamic>> assignResources(Map<String, dynamic> payload) async =>
      {'status': 'ok', 'message': 'Override written'};

  @override
  Future<Map<String, dynamic>> getFrigateConfig() async =>
      {'config': <String, dynamic>{}};

  @override
  Future<Map<String, dynamic>> updateFrigateConfig(Map<String, dynamic> payload) async =>
      {'status': 'ok', 'message': 'Config updated', 'config': payload};
}

void main() {
  group('OrchestratorPage', () {
    testWidgets('renders hardware and containers sections', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            apiClientProvider.overrideWith((ref) => _OrchestratorMockClient()),
          ],
          child: const MaterialApp(
            home: OrchestratorPage(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('مدیریت سخت‌افزار و منابع'), findsOneWidget);
      expect(find.text('منابع سخت‌افزاری'), findsOneWidget);
      expect(find.textContaining('کانتینرهای فعال'), findsOneWidget);
    });

    testWidgets('displays CPU and RAM bars', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            apiClientProvider.overrideWith((ref) => _OrchestratorMockClient()),
          ],
          child: const MaterialApp(
            home: OrchestratorPage(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.textContaining('CPU'), findsOneWidget);
      expect(find.textContaining('RAM'), findsOneWidget);
      expect(find.byType(LinearProgressIndicator), findsAtLeast(2));
    });

    testWidgets('displays GPU card when GPUs present', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            apiClientProvider.overrideWith((ref) => _OrchestratorMockClient()),
          ],
          child: const MaterialApp(
            home: OrchestratorPage(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('NVIDIA GeForce RTX 4090'), findsOneWidget);
      expect(find.textContaining('کارت‌های گرافیک'), findsOneWidget);
    });

    testWidgets('shows container names and status dots', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            apiClientProvider.overrideWith((ref) => _OrchestratorMockClient()),
          ],
          child: const MaterialApp(
            home: OrchestratorPage(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('frigate-intelligence'), findsOneWidget);
      expect(find.text('frigate'), findsOneWidget);
      expect(find.textContaining('running'), findsOneWidget);
      expect(find.textContaining('exited'), findsOneWidget);
    });

    testWidgets('shows port chips for containers with ports', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            apiClientProvider.overrideWith((ref) => _OrchestratorMockClient()),
          ],
          child: const MaterialApp(
            home: OrchestratorPage(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.byType(Chip), findsAtLeast(1));
      expect(find.textContaining('8088'), findsOneWidget);
    });
  });

  group('OrchestratorProvider', () {
    test('fetchHardware updates state with hardware data', () async {
      final container = ProviderContainer(
        overrides: [
          apiClientProvider.overrideWith((ref) => _OrchestratorMockClient()),
        ],
      );
      addTearDown(container.dispose);

      await container.read(orchestratorProvider.notifier).fetchHardware();
      final state = container.read(orchestratorProvider);

      expect(state.isLoadingHardware, isFalse);
      expect(state.hardware, isNotNull);
      expect(state.hardware!['cpu']['cores'], 8);
    });

    test('fetchContainers updates state with container list', () async {
      final container = ProviderContainer(
        overrides: [
          apiClientProvider.overrideWith((ref) => _OrchestratorMockClient()),
        ],
      );
      addTearDown(container.dispose);

      await container.read(orchestratorProvider.notifier).fetchContainers();
      final state = container.read(orchestratorProvider);

      expect(state.isLoadingContainers, isFalse);
      expect(state.containers.length, 2);
    });

    test('refreshAll fetches both hardware and containers', () async {
      final container = ProviderContainer(
        overrides: [
          apiClientProvider.overrideWith((ref) => _OrchestratorMockClient()),
        ],
      );
      addTearDown(container.dispose);

      await container.read(orchestratorProvider.notifier).refreshAll();
      final state = container.read(orchestratorProvider);

      expect(state.hardware, isNotNull);
      expect(state.containers.length, 2);
    });
  });
}
