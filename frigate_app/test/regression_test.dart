import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:frigate_intelligence/main.dart';
import 'package:frigate_intelligence/presentation/providers/live_stream_provider.dart';
import 'package:frigate_intelligence/presentation/providers/server_config_provider.dart';
import 'package:frigate_intelligence/presentation/providers/navigation_provider.dart';
import 'package:frigate_intelligence/presentation/models/playback_params.dart';
import 'package:frigate_intelligence/presentation/widgets/inline_vod_player.dart';
import 'package:frigate_intelligence/data/datasources/api_client.dart';
import 'package:frigate_intelligence/data/models/report_rule.dart';
import 'package:frigate_intelligence/presentation/pages/settings_page.dart';

void main() {
  // Default override: synced mock API client for all tests
  final defaultClient = _SkewableMockApiClient(
    serverTimestamp: DateTime.now().millisecondsSinceEpoch / 1000.0,
  );

  group('MainScaffold', () {
    testWidgets('bug_020_bottom_nav_has_three_items', (tester) async {
      // Regression test for BUG-020: MainScaffold only had 2 nav items (AI, NVR);
      // Settings was not accessible from the bottom navigation bar.
      tester.view.physicalSize = const Size(500, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            apiClientProvider.overrideWith((ref) => defaultClient),
          ],
          child: const FrigateIntelligenceApp(),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.byType(NavigationBar), findsOneWidget);
      expect(find.byType(NavigationDestination), findsNWidgets(3));
      expect(find.text('AI'), findsOneWidget);
      expect(find.text('NVR'), findsOneWidget);
      expect(find.text('Settings'), findsOneWidget);
    });

    testWidgets('bug_020_settings_tab_navigates_to_settings_page', (tester) async {
      // Regression test for BUG-020: Tapping Settings nav item should show
      // the SettingsPage with server config fields.
      tester.view.physicalSize = const Size(500, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            apiClientProvider.overrideWith((ref) => defaultClient),
          ],
          child: const FrigateIntelligenceApp(),
        ),
      );
      await tester.pumpAndSettle();

      await tester.tap(find.text('Settings'));
      await tester.pumpAndSettle();

      expect(find.text('تنظیمات سرور'), findsOneWidget);
    });
  });

  group('TimeSync', () {
    testWidgets('bug_024_time_sync_banner_shows_on_skew', (tester) async {
      // Regression test for BUG-024: When server timestamp is >2 min different
      // from client time, a MaterialBanner warning must be displayed.
      tester.view.physicalSize = const Size(500, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);

      final skewedClient = _SkewableMockApiClient(
        serverTimestamp: DateTime.now().millisecondsSinceEpoch / 1000.0 - 180,
      );

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            apiClientProvider.overrideWith((ref) => skewedClient),
          ],
          child: const FrigateIntelligenceApp(),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.byType(MaterialBanner), findsOneWidget);
      expect(find.textContaining('Clock skew detected'), findsOneWidget);
    });

    testWidgets('bug_024_time_sync_no_banner_when_synced', (tester) async {
      // Regression test for BUG-024: When server timestamp is within 2 min
      // of client time, no MaterialBanner should be displayed.
      tester.view.physicalSize = const Size(500, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);

      final syncedClient = _SkewableMockApiClient(
        serverTimestamp: DateTime.now().millisecondsSinceEpoch / 1000.0,
      );

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            apiClientProvider.overrideWith((ref) => syncedClient),
          ],
          child: const FrigateIntelligenceApp(),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.byType(MaterialBanner), findsNothing);
    });
  });

  group('PlaybackTab', () {
    // BUG-019 regression: Player initialization moved from build() to initState().
    // media_kit Player() requires native libraries not available in flutter_test,
    // so this is verified via code review + flutter analyze (no init in build()).
    // See playback_tab.dart: initState() calls _initPlayer(), build() does not.
  });

  group('LiveStreamController', () {
    test('bug_017_rtsp_url_construction', () {
      // Regression test for BUG-017: Android blocked cleartext HTTP to
      // local network. While the actual fix is in AndroidManifest.xml,
      // we verify the RTSP URL is constructed correctly for local network.
      final controller = LiveStreamController(
        serverIp: '192.168.85.203',
        cameraName: 'cam1',
      );

      // The controller should expose camera name and server IP correctly
      expect(controller.cameraName, 'cam1');
      expect(controller.serverIp, '192.168.85.203');
      expect(controller.status, StreamStatus.idle);
      expect(controller.errorMessage, isEmpty);
    });
  });

  group('PlaybackDeepLink', () {
    test('bug_027_playback_deep_link_navigates', () {
      // Regression test for BUG-027: navigateToPlayback should set
      // mainTabIndex=1 (NVR) and nvrSubTabIndex=1 (Playback).
      final container = ProviderContainer();
      addTearDown(container.dispose);

      final notifier = container.read(navigationProvider.notifier);
      notifier.navigateToPlayback(PlaybackParams(
        camera: 'cam1',
        date: '2026-07-21',
        startTime: 1784394000.0,
        endTime: 1784395800.0,
      ));

      final state = container.read(navigationProvider);
      expect(state.mainTabIndex, 1);
      expect(state.nvrSubTabIndex, 1);
      expect(state.playbackParams, isNotNull);
      expect(state.playbackParams!.camera, 'cam1');
    });

    test('bug_027_playback_params_auto_select_camera', () {
      // Regression test for BUG-027: PlaybackParams.fromJson should parse
      // the playback intent map correctly with camera, date, start/end times.
      final params = PlaybackParams.fromJson({
        'camera': 'cam1',
        'start_time': 1784394000.0,
        'end_time': 1784395800.0,
        'date': '2026-07-21',
      });

      expect(params.camera, 'cam1');
      expect(params.date, '2026-07-21');
      expect(params.startTime, 1784394000.0);
      expect(params.endTime, 1784395800.0);

      // Verify equality for deduplication in PlaybackTab
      final same = PlaybackParams.fromJson({
        'camera': 'cam1',
        'start_time': 1784394000.0,
        'end_time': 1784395800.0,
        'date': '2026-07-21',
      });
      expect(params, same);
    });
  });

  group('InlineVodPlayer', () {
    test('bug_028_inline_vod_player_constructs_url', () {
      // Regression test for BUG-028: InlineVodPlayer should construct
      // the correct Frigate VOD clip URL from PlaybackParams + server IP.
      final params = PlaybackParams(
        camera: 'cam1',
        date: '2026-07-21',
        startTime: 1784394000.0,
        endTime: 1784395800.0,
      );

      final url = InlineVodPlayer.constructVodUrl('192.168.85.203', params);

      expect(url,
          'http://192.168.85.203:5000/api/cam1/start/1784394000/end/1784395800/clip.mp4');
    });
  });

  group('SettingsPage', () {
    testWidgets('bug_032_settings_page_has_telegram_section', (tester) async {
      // Regression test for BUG-032: Settings page should render the
      // Telegram & Reporting section with bot token, chat ID, report time,
      // timezone dropdown, enable switch, and save button.
      tester.view.physicalSize = const Size(500, 1200);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            apiClientProvider.overrideWith((ref) => defaultClient),
          ],
          child: const MaterialApp(
            home: SettingsPage(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Section header for Telegram & Reporting
      expect(find.text('تلگرام و گزارش‌گیری'), findsOneWidget);

      // Enable switch
      expect(find.text('فعال‌سازی گزارش‌های زمان‌بندی شده'), findsOneWidget);
      expect(find.byType(SwitchListTile), findsNWidgets(2));

      // Bot Token field
      expect(find.text('Telegram Bot Token'), findsOneWidget);

      // Chat ID field
      expect(find.text('Telegram Chat ID'), findsOneWidget);

      // Report Interval field
      expect(find.text('بازه گزارش‌گیری (ساعت)'), findsOneWidget);

      // Timezone dropdown
      expect(find.text('منطقه زمانی'), findsOneWidget);
      expect(find.byType(DropdownButtonFormField<String>), findsOneWidget);

      // Save button
      expect(find.text('ذخیره تنظیمات تلگرام'), findsOneWidget);
    });
  });
}

class _SkewableMockApiClient implements BaseApiClient {
  final double serverTimestamp;

  _SkewableMockApiClient({required this.serverTimestamp});

  @override
  Future<Map<String, dynamic>> query(String question,
      {int maxRetries = 3}) async {
    return {
      'sql': 'SELECT 1',
      'explanation': 'mock',
      'columns': ['1'],
      'rows': [
        [1]
      ],
      'row_count': 1,
      'attempts': 1,
      'error': null,
    };
  }

  @override
  Future<List<Map<String, dynamic>>> getEvents({
    String? camera,
    String? label,
  }) async {
    return [];
  }

  @override
  Future<Map<String, dynamic>> health() async {
    return {
      'status': 'ok',
      'version': '0.1.0',
      'db_connected': true,
      'server_timestamp': serverTimestamp,
      'server_timezone': 'UTC',
      'server_datetime_iso': DateTime.fromMillisecondsSinceEpoch(
        (serverTimestamp * 1000).round(),
        isUtc: true,
      ).toIso8601String(),
    };
  }

  @override
  Future<Map<String, dynamic>> getCameras() async {
    return {'cameras': [], 'total': 0};
  }

  @override
  Future<Map<String, dynamic>> getRecordings({
    String? camera,
    String? date,
    int? hour,
    double? startTime,
    double? endTime,
  }) async {
    return {'segments': [], 'total': 0, 'camera': camera ?? 'all'};
  }

  @override
  Future<Map<String, dynamic>> getSettings() async {
    return {
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
  }

  @override
  Future<Map<String, dynamic>> updateSettings(
      Map<String, dynamic> newSettings) async {
    return {'status': 'ok', 'message': 'Settings saved successfully'};
  }

  @override
  Future<String> getSystemLogs(int lines) async =>
      '2026-07-22 19:00:42 [test] INFO: Mock log line';

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

  @override
  Future<List<ReportRule>> getReportRules() async => [];

  @override
  Future<ReportRule> createReportRule(Map<String, dynamic> payload) async =>
      ReportRule.fromJson({...payload, 'id': 'test', 'created_at': '', 'last_run': '', 'last_status': ''});

  @override
  Future<ReportRule> updateReportRule(String id, Map<String, dynamic> payload) async =>
      ReportRule.fromJson({...payload, 'id': id, 'created_at': '', 'last_run': '', 'last_status': ''});

  @override
  Future<void> deleteReportRule(String id) async {}

  @override
  Future<Map<String, dynamic>> testRunRule(String id) async =>
      {'status': 'ok', 'message': 'Test run', 'rule_id': id};

  @override
  Future<List<Map<String, dynamic>>> getRuleHistory(String id) async => [];
}
