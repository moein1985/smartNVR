import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:frigate_intelligence/data/datasources/api_client.dart';
import 'package:frigate_intelligence/presentation/providers/server_config_provider.dart';
import 'package:frigate_intelligence/presentation/providers/system_maintenance_provider.dart';
import 'package:frigate_intelligence/presentation/pages/settings_page.dart';

class _MaintenanceMockClient implements BaseApiClient {
  final String logsResponse;
  final Map<String, dynamic> updateResponse;

  _MaintenanceMockClient({
    this.logsResponse =
        '2026-07-22 19:00:42 [test] INFO: System initialized\n'
        '2026-07-22 19:01:15 [test] INFO: GET /api/v1/health -> 200',
    this.updateResponse = const {
      'status': 'ok',
      'message': 'Update applied successfully',
    },
  });

  @override
  Future<Map<String, dynamic>> query(String question,
      {int maxRetries = 3}) async {
    return {
      'sql': '',
      'explanation': '',
      'columns': [],
      'rows': [],
      'row_count': 0,
      'attempts': 1,
      'error': null,
    };
  }

  @override
  Future<List<Map<String, dynamic>>> getEvents({
    String? camera,
    String? label,
  }) async => [];

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
  Future<Map<String, dynamic>> getCameras() async =>
      {'cameras': [], 'total': 0};

  @override
  Future<Map<String, dynamic>> getRecordings({
    String? camera,
    String? date,
    int? hour,
    double? startTime,
    double? endTime,
  }) async => {'segments': [], 'total': 0, 'camera': camera ?? 'all'};

  @override
  Future<Map<String, dynamic>> getSettings() async => {
    'avalai_api_key': '',
    'llm_model': 'gemini-2.5-flash',
    'telegram_enabled': false,
    'telegram_bot_token': '',
    'telegram_chat_id': '',
    'bale_enabled': false,
    'bale_bot_token': '',
    'bale_chat_id': '',
    'report_target': 'telegram',
    'report_interval_hours': 24,
    'report_timezone': 'Asia/Tehran',
    'log_level': 'INFO',
  };

  @override
  Future<Map<String, dynamic>> updateSettings(
      Map<String, dynamic> newSettings) async =>
      {'status': 'ok', 'message': 'Settings saved successfully'};

  @override
  Future<String> getSystemLogs(int lines) async => logsResponse;

  @override
  Future<Map<String, dynamic>> uploadUpdate(File file) async => updateResponse;
}

void main() {
  group('SystemMaintenance', () {
    testWidgets('settings page renders system maintenance section',
        (tester) async {
      tester.view.physicalSize = const Size(500, 1400);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            apiClientProvider
                .overrideWith((ref) => _MaintenanceMockClient()),
          ],
          child: const MaterialApp(
            home: SettingsPage(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('نگهداری سیستم'), findsOneWidget);
      expect(find.text('لاگ‌های سیستم'), findsOneWidget);
      expect(find.text('به‌روزرسانی OTA'), findsOneWidget);
      expect(find.byIcon(Icons.terminal), findsOneWidget);
      expect(find.byIcon(Icons.system_update), findsOneWidget);
    });

    testWidgets('refresh logs button fetches and displays logs',
        (tester) async {
      tester.view.physicalSize = const Size(500, 1400);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            apiClientProvider.overrideWith(
              (ref) => _MaintenanceMockClient(
                logsResponse: '2026-07-22 19:00:42 [test] INFO: Test log line',
              ),
            ),
          ],
          child: const MaterialApp(
            home: SettingsPage(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Test log line'), findsNothing);

      await tester.ensureVisible(find.byIcon(Icons.refresh));
      await tester.tap(find.byIcon(Icons.refresh));
      await tester.pumpAndSettle();

      expect(find.textContaining('Test log line'), findsOneWidget);
    });

    testWidgets('OTA button shows correct label when idle', (tester) async {
      tester.view.physicalSize = const Size(500, 1400);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            apiClientProvider
                .overrideWith((ref) => _MaintenanceMockClient()),
          ],
          child: const MaterialApp(
            home: SettingsPage(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('انتخاب فایل به‌روزرسانی (.tar)'), findsOneWidget);
    });

    testWidgets(
        'system_maintenance_provider fetchLogs updates state correctly',
        (tester) async {
      final container = ProviderContainer(
        overrides: [
          apiClientProvider.overrideWith(
            (ref) => _MaintenanceMockClient(
              logsResponse: 'Log line 1\nLog line 2',
            ),
          ),
        ],
      );
      addTearDown(container.dispose);

      final notifier =
          container.read(systemMaintenanceProvider.notifier);
      await notifier.fetchLogs();

      final state = container.read(systemMaintenanceProvider);
      expect(state.isLoadingLogs, isFalse);
      expect(state.logs, 'Log line 1\nLog line 2');
    });

    testWidgets(
        'system_maintenance_provider uploadUpdate sets success state',
        (tester) async {
      final container = ProviderContainer(
        overrides: [
          apiClientProvider.overrideWith(
            (ref) => _MaintenanceMockClient(
              updateResponse: {
                'status': 'ok',
                'message': 'Update applied successfully',
              },
            ),
          ),
        ],
      );
      addTearDown(container.dispose);

      final notifier =
          container.read(systemMaintenanceProvider.notifier);

      await notifier.uploadUpdate('/fake/path/update.tar');

      final state = container.read(systemMaintenanceProvider);
      expect(state.updateState, UpdateState.success);
      expect(state.message, 'Update applied successfully');
    });

    testWidgets(
        'system_maintenance_provider uploadUpdate sets rolledBack state',
        (tester) async {
      final container = ProviderContainer(
        overrides: [
          apiClientProvider.overrideWith(
            (ref) => _MaintenanceMockClient(
              updateResponse: {
                'status': 'rolled_back',
                'message': 'Update rolled back',
              },
            ),
          ),
        ],
      );
      addTearDown(container.dispose);

      final notifier =
          container.read(systemMaintenanceProvider.notifier);

      await notifier.uploadUpdate('/fake/path/update.tar');

      final state = container.read(systemMaintenanceProvider);
      expect(state.updateState, UpdateState.rolledBack);
      expect(state.message, 'Update rolled back');
    });

    testWidgets(
        'system_maintenance_provider reset returns to idle state',
        (tester) async {
      final container = ProviderContainer(
        overrides: [
          apiClientProvider
              .overrideWith((ref) => _MaintenanceMockClient()),
        ],
      );
      addTearDown(container.dispose);

      final notifier =
          container.read(systemMaintenanceProvider.notifier);
      await notifier.fetchLogs();
      notifier.reset();

      final state = container.read(systemMaintenanceProvider);
      expect(state.updateState, UpdateState.idle);
      expect(state.logs, isNull);
      expect(state.message, isNull);
    });
  });
}
