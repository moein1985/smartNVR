import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:frigate_intelligence/data/datasources/api_client.dart';
import 'package:frigate_intelligence/data/models/report_rule.dart';
import 'package:frigate_intelligence/presentation/providers/server_config_provider.dart';
import 'package:frigate_intelligence/presentation/providers/report_rules_provider.dart';
import 'package:frigate_intelligence/presentation/pages/report_rules_page.dart';
import 'package:frigate_intelligence/presentation/pages/orchestrator_page.dart';

class _FeatMockClient implements BaseApiClient {
  final List<ReportRule> _rules;
  final Map<String, dynamic> _hardware;
  final Map<String, dynamic> _containers;

  _FeatMockClient({
    List<ReportRule>? rules,
    Map<String, dynamic>? hardware,
    Map<String, dynamic>? containers,
  })  : _rules = rules ?? [
          ReportRule(
            id: 'rule-1',
            name: 'گزارش روزانه',
            enabled: true,
            zones: ['ahmad_table'],
            intervalHours: 24,
            destination: 'telegram',
            lastRun: '2026-07-23T08:00:00',
            lastStatus: 'success',
          ),
        ],
        _hardware = hardware ?? const {
          'cpu': {'cores': 4, 'utilization_pct': 30.0},
          'memory': {'total_gb': 16.0, 'available_gb': 8.0, 'used_pct': 50.0},
          'gpus': [
            {'index': 0, 'name': 'RTX 4090', 'memory_total_mb': 24564, 'memory_used_mb': 2048, 'gpu_utilization_pct': 22.0},
          ],
        },
        _containers = containers ?? const {
          'containers': [
            {
              'name': 'frigate',
              'image': 'frigate:latest',
              'status': 'running',
              'short_id': 'abc123',
              'ports': [],
              'capability': {'supports_gpu': true, 'detection_strategy': 'nvidia_gpu'},
            },
            {
              'name': 'frigate-intelligence',
              'image': 'fi:latest',
              'status': 'running',
              'short_id': 'def456',
              'ports': [],
              'capability': {'supports_gpu': false, 'detection_strategy': 'cpu_only'},
            },
          ],
        };

  @override
  Future<Map<String, dynamic>> query(String question, {int maxRetries = 3}) async =>
      {'sql': '', 'explanation': '', 'columns': [], 'rows': [], 'row_count': 0, 'attempts': 1, 'error': null};

  @override
  Future<List<Map<String, dynamic>>> getEvents({String? camera, String? label}) async => [];

  @override
  Future<Map<String, dynamic>> health() async => {'status': 'ok'};

  @override
  Future<Map<String, dynamic>> getCameras() async => {'cameras': [], 'total': 0};

  @override
  Future<Map<String, dynamic>> getRecordings({
    String? camera, String? date, int? hour, double? startTime, double? endTime,
  }) async => {'segments': [], 'total': 0};

  @override
  Future<Map<String, dynamic>> getSettings() async => {
    'telegram_enabled': false, 'work_hours_start': '08:00', 'work_hours_end': '16:00',
  };

  @override
  Future<Map<String, dynamic>> updateSettings(Map<String, dynamic> newSettings) async =>
      {'status': 'ok', 'message': 'Saved'};

  @override
  Future<String> getSystemLogs(int lines) async => 'log';

  @override
  Future<Map<String, dynamic>> uploadUpdate(File file) async => {'status': 'ok'};

  @override
  Future<Map<String, dynamic>> getHardware() async => _hardware;

  @override
  Future<Map<String, dynamic>> getContainers({bool allStatuses = false}) async => _containers;

  @override
  Future<Map<String, dynamic>> assignResources(Map<String, dynamic> payload) async =>
      {'status': 'ok', 'message': 'Override written'};

  @override
  Future<Map<String, dynamic>> getFrigateConfig() async => {'config': {}};

  @override
  Future<Map<String, dynamic>> updateFrigateConfig(Map<String, dynamic> payload) async =>
      {'status': 'ok', 'message': 'Updated', 'config': payload};

  @override
  Future<List<ReportRule>> getReportRules() async {
    await Future.delayed(const Duration(milliseconds: 100));
    return _rules;
  }

  @override
  Future<ReportRule> createReportRule(Map<String, dynamic> payload) async {
    await Future.delayed(const Duration(milliseconds: 100));
    return ReportRule.fromJson({
      ...payload,
      'id': 'new-rule-${DateTime.now().millisecondsSinceEpoch}',
      'created_at': DateTime.now().toIso8601String(),
      'last_run': '',
      'last_status': '',
    });
  }

  @override
  Future<ReportRule> updateReportRule(String id, Map<String, dynamic> payload) async {
    await Future.delayed(const Duration(milliseconds: 100));
    return ReportRule.fromJson({...payload, 'id': id, 'created_at': '', 'last_run': '', 'last_status': ''});
  }

  @override
  Future<void> deleteReportRule(String id) async {
    await Future.delayed(const Duration(milliseconds: 50));
  }

  @override
  Future<Map<String, dynamic>> testRunRule(String id) async =>
      {'status': 'ok', 'message': 'Test run complete', 'rule_id': id};

  @override
  Future<List<Map<String, dynamic>>> getRuleHistory(String id) async => [];
}

void main() {
  group('feat_016_7 ReportRulesPage', () {
    testWidgets('report_rules_page_renders_with_rules', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            apiClientProvider.overrideWith((ref) => _FeatMockClient()),
          ],
          child: const MaterialApp(home: ReportRulesPage()),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('قوانین گزارش‌گیری'), findsOneWidget);
      expect(find.text('گزارش روزانه'), findsOneWidget);
      expect(find.byType(FloatingActionButton), findsOneWidget);
    });

    testWidgets('report_rules_create_form_opens_on_fab_tap', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            apiClientProvider.overrideWith((ref) => _FeatMockClient()),
          ],
          child: const MaterialApp(home: ReportRulesPage()),
        ),
      );
      await tester.pumpAndSettle();

      await tester.tap(find.byType(FloatingActionButton));
      await tester.pumpAndSettle();

      expect(find.text('افزودن قانون جدید'), findsOneWidget);
      expect(find.text('نام قانون'), findsOneWidget);
      expect(find.text('مقصد'), findsOneWidget);
    });

    test('report_rules_provider_loads_rules', () async {
      final container = ProviderContainer(
        overrides: [
          apiClientProvider.overrideWith((ref) => _FeatMockClient()),
        ],
      );
      addTearDown(container.dispose);

      await container.read(reportRulesProvider.notifier).refresh();
      final state = container.read(reportRulesProvider);

      expect(state.isLoading, isFalse);
      expect(state.rules.length, 1);
      expect(state.rules.first.name, 'گزارش روزانه');
    });
  });

  group('feat_016_7 OrchestratorPage Interactive Binding', () {
    testWidgets('orchestrator_interactive_binding_shows_cpu_checkboxes', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            apiClientProvider.overrideWith((ref) => _FeatMockClient()),
          ],
          child: const MaterialApp(home: OrchestratorPage()),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('هسته‌های CPU'), findsNWidgets(2));
      expect(find.byType(FilterChip), findsNWidgets(8));
    });

    testWidgets('orchestrator_interactive_binding_shows_memory_input', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            apiClientProvider.overrideWith((ref) => _FeatMockClient()),
          ],
          child: const MaterialApp(home: OrchestratorPage()),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('محدودیت حافظه (GB)'), findsNWidgets(2));
      expect(find.text('اعمال'), findsNWidgets(2));
    });

    testWidgets('gpu_disabled_for_cpu_only_container', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            apiClientProvider.overrideWith((ref) => _FeatMockClient()),
          ],
          child: const MaterialApp(home: OrchestratorPage()),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('کارت گرافیک'), findsNWidgets(2));
      expect(find.text('GPU پشتیبانی نمی‌شود'), findsOneWidget);
      expect(find.byIcon(Icons.warning), findsOneWidget);
    });

    testWidgets('gpu_enabled_for_gpu_capable_container', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            apiClientProvider.overrideWith((ref) => _FeatMockClient()),
          ],
          child: const MaterialApp(home: OrchestratorPage()),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('بدون GPU'), findsOneWidget);
    });
  });

  group('feat_016_7 ReportRule Model', () {
    test('report_rule_from_json_parses_all_fields', () {
      final rule = ReportRule.fromJson({
        'id': 'test-1',
        'name': 'Test',
        'enabled': true,
        'zones': ['zone1', 'zone2'],
        'cameras': ['cam1'],
        'labels': ['person'],
        'interval_hours': 12,
        'timezone': 'UTC',
        'destination': 'bale',
        'chat_id': '123',
        'prompt_template': 'test prompt',
        'include_summary': false,
        'include_raw_data': true,
        'created_at': '2026-01-01',
        'last_run': '2026-01-02',
        'last_status': 'success',
      });

      expect(rule.id, 'test-1');
      expect(rule.name, 'Test');
      expect(rule.enabled, isTrue);
      expect(rule.zones, ['zone1', 'zone2']);
      expect(rule.intervalHours, 12);
      expect(rule.destination, 'bale');
      expect(rule.includeSummary, isFalse);
      expect(rule.includeRawData, isTrue);
    });

    test('report_rule_to_json_roundtrip', () {
      final rule = ReportRule(
        id: 'r1',
        name: 'Rule 1',
        zones: ['z1'],
        intervalHours: 6,
      );
      final json = rule.toJson();
      expect(json['id'], 'r1');
      expect(json['name'], 'Rule 1');
      expect(json['zones'], ['z1']);
      expect(json['interval_hours'], 6);
    });
  });
}
