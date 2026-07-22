// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:frigate_intelligence/main.dart';
import 'package:frigate_intelligence/presentation/providers/server_config_provider.dart';
import 'package:frigate_intelligence/data/datasources/api_client.dart';

class _SyncedMockClient implements BaseApiClient {
  @override
  Future<Map<String, dynamic>> query(String question, {int maxRetries = 3}) async {
    return {'sql': '', 'explanation': '', 'columns': [], 'rows': [], 'row_count': 0, 'attempts': 1, 'error': null};
  }

  @override
  Future<List<Map<String, dynamic>>> getEvents({String? camera, String? label}) async => [];

  @override
  Future<Map<String, dynamic>> health() async {
    return {
      'status': 'ok', 'version': '0.1.0', 'db_connected': true,
      'server_timestamp': DateTime.now().millisecondsSinceEpoch / 1000.0,
      'server_timezone': 'UTC',
      'server_datetime_iso': DateTime.now().toUtc().toIso8601String(),
    };
  }

  @override
  Future<Map<String, dynamic>> getCameras() async => {'cameras': [], 'total': 0};

  @override
  Future<Map<String, dynamic>> getRecordings({String? camera, String? date, int? hour, double? startTime, double? endTime}) async =>
      {'segments': [], 'total': 0, 'camera': camera ?? 'all'};

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
  Future<Map<String, dynamic>> updateSettings(Map<String, dynamic> newSettings) async =>
      {'status': 'ok', 'message': 'Settings saved successfully'};

  @override
  Future<String> getSystemLogs(int lines) async =>
      '2026-07-22 19:00:42 [test] INFO: Mock log line 1\n2026-07-22 19:00:43 [test] INFO: Mock log line 2';

  @override
  Future<Map<String, dynamic>> uploadUpdate(File file) async =>
      {'status': 'ok', 'message': 'Update applied (mock)'};

  @override
  Future<Map<String, dynamic>> getHardware() async => {
    'cpu': {'cores': 4, 'utilization_pct': 10.0},
    'memory': {'total_gb': 8.0, 'available_gb': 4.0, 'used_pct': 50.0},
    'gpus': <Map<String, dynamic>>[],
  };

  @override
  Future<Map<String, dynamic>> getContainers({bool allStatuses = false}) async =>
      {'containers': <Map<String, dynamic>>[]};

  @override
  Future<Map<String, dynamic>> assignResources(Map<String, dynamic> payload) async =>
      {'status': 'ok', 'message': 'Override written (mock)'};

  @override
  Future<Map<String, dynamic>> getFrigateConfig() async =>
      {'config': <String, dynamic>{}};

  @override
  Future<Map<String, dynamic>> updateFrigateConfig(Map<String, dynamic> payload) async =>
      {'status': 'ok', 'message': 'Config updated (mock)', 'config': payload};
}

void main() {
  testWidgets('Chat page renders with greeting and input bar', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          apiClientProvider.overrideWith((ref) => _SyncedMockClient()),
        ],
        child: const FrigateIntelligenceApp(),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Frigate Intelligence'), findsOneWidget);
    expect(find.byIcon(Icons.settings_outlined), findsNWidgets(2));
    expect(find.byIcon(Icons.mic_none), findsOneWidget);
    expect(find.byIcon(Icons.send_rounded), findsOneWidget);
  });
}
