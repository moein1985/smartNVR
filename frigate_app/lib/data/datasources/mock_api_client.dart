import 'dart:io';
import 'api_client.dart';
import '../models/report_rule.dart';

class MockApiClient implements BaseApiClient {
  @override
  Future<Map<String, dynamic>> query(String question,
      {int maxRetries = 3}) async {
    await Future.delayed(const Duration(seconds: 2));
    return {
      'sql':
          "SELECT id, camera, label, start_time FROM event WHERE label='person' LIMIT 2;",
      'explanation':
          'در اینجا رویدادهای اخیر که شخص در آن‌ها تشخیص داده شده است را مشاهده می‌کنید:',
      'columns': ['id', 'camera', 'label', 'start_time'],
      'rows': [
        {
          'id': 'mock_event_1',
          'camera': 'cam1',
          'label': 'person',
          'start_time': '2026-07-20 10:15:00',
        },
        {
          'id': 'mock_event_2',
          'camera': 'cam2',
          'label': 'person',
          'start_time': '2026-07-20 09:30:00',
        },
      ],
      'row_count': 2,
      'attempts': 1,
      'error': null,
    };
  }

  @override
  Future<List<Map<String, dynamic>>> getEvents({
    String? camera,
    String? label,
  }) async {
    await Future.delayed(const Duration(seconds: 1));
    return [
      {
        'id': 'mock_event_1',
        'camera': 'cam1',
        'label': 'person',
        'start_time': '2026-07-20 10:15:00',
      },
      {
        'id': 'mock_event_2',
        'camera': 'cam2',
        'label': 'person',
        'start_time': '2026-07-20 09:30:00',
      },
    ];
  }

  @override
  Future<Map<String, dynamic>> health() async {
    await Future.delayed(const Duration(milliseconds: 500));
    final now = DateTime.now().toUtc();
    return {
      'status': 'ok',
      'version': '0.1.0',
      'db_connected': true,
      'server_timestamp': now.millisecondsSinceEpoch / 1000.0,
      'server_timezone': 'UTC',
      'server_datetime_iso': now.toIso8601String(),
    };
  }

  @override
  Future<Map<String, dynamic>> getCameras() async {
    await Future.delayed(const Duration(milliseconds: 500));
    return {
      'cameras': [
        {
          'name': 'cam1',
          'enabled': true,
          'detect': {
            'width': 640,
            'height': 480,
            'fps': 5,
            'objects': ['person', 'car', 'motorcycle', 'bicycle', 'dog', 'cat'],
          },
          'zones': ['parking_1', 'main_gate'],
          'live_stream_name': 'cam1',
        },
      ],
      'total': 1,
    };
  }

  @override
  Future<Map<String, dynamic>> getRecordings({
    String? camera,
    String? date,
    int? hour,
    double? startTime,
    double? endTime,
  }) async {
    await Future.delayed(const Duration(milliseconds: 500));
    return {
      'segments': [
        {
          'id': 'mock_rec_1',
          'camera': 'cam1',
          'path': '/media/frigate/recordings/2026-07-20/11/cam1/00.04.mp4',
          'start_time': 1784545204.0,
          'end_time': 1784545213.99,
          'duration': 9.99,
          'objects': 0,
          'motion': 89,
        },
        {
          'id': 'mock_rec_2',
          'camera': 'cam1',
          'path': '/media/frigate/recordings/2026-07-20/11/cam1/00.14.mp4',
          'start_time': 1784545214.0,
          'end_time': 1784545223.99,
          'duration': 9.99,
          'objects': 1,
          'motion': 92,
        },
      ],
      'total': 2,
      'camera': camera ?? 'all',
      'date': date,
      'hour': hour,
    };
  }

  @override
  Future<Map<String, dynamic>> getSettings() async {
    await Future.delayed(const Duration(milliseconds: 500));
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
    await Future.delayed(const Duration(milliseconds: 500));
    return {'status': 'ok', 'message': 'Settings saved successfully'};
  }

  @override
  Future<String> getSystemLogs(int lines) async {
    await Future.delayed(const Duration(milliseconds: 500));
    return [
      '2026-07-22 19:00:42 [frigate_intelligence] INFO: Initializing Frigate Intelligence Platform',
      '2026-07-22 19:00:42 [frigate_intelligence.infrastructure.api.fastapi_app] INFO: GET /api/v1/health -> 200 (12.3ms) [a3f8b1c2]',
      '2026-07-22 19:00:43 [frigate_intelligence.infrastructure.scheduler.cron_service] INFO: Scheduled report job every 24h',
      '2026-07-22 19:01:15 [frigate_intelligence.infrastructure.api.fastapi_app] INFO: POST /api/v1/query -> 200 (1842.5ms) [b7c2e9a1]',
      '2026-07-22 19:02:03 [frigate_intelligence.infrastructure.api.fastapi_app] INFO: GET /api/v1/system/logs -> 200 (5.1ms) [c1d4f2b8]',
    ].join('\n');
  }

  @override
  Future<Map<String, dynamic>> uploadUpdate(File file) async {
    await Future.delayed(const Duration(seconds: 2));
    return {
      'status': 'ok',
      'message': 'Update applied successfully (mock)',
      'details': {
        'old_image': 'frigate-intelligence:latest',
        'new_image': 'frigate-intelligence:v1.2.0',
        'health_check_passed': true,
      },
    };
  }

  @override
  Future<Map<String, dynamic>> getHardware() async {
    await Future.delayed(const Duration(milliseconds: 500));
    return {
      'cpu': {'cores': 8, 'utilization_pct': 35.5},
      'memory': {
        'total_gb': 16.0,
        'available_gb': 8.5,
        'used_pct': 46.9,
      },
      'gpus': [
        {
          'index': 0,
          'name': 'NVIDIA GeForce RTX 4090',
          'memory_total_mb': 24564,
          'memory_used_mb': 2048,
          'gpu_utilization_pct': 22.0,
          'uuid': 'GPU-mock-abc-123',
        },
      ],
    };
  }

  @override
  Future<Map<String, dynamic>> getContainers({bool allStatuses = false}) async {
    await Future.delayed(const Duration(milliseconds: 500));
    return {
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
          'status': 'running',
          'short_id': 'def456',
          'ports': [
            {'container_port': '5000/tcp', 'host_ip': '0.0.0.0', 'host_port': '5000'},
            {'container_port': '8554/tcp', 'host_ip': '0.0.0.0', 'host_port': '8554'},
          ],
        },
      ],
    };
  }

  @override
  Future<Map<String, dynamic>> assignResources(Map<String, dynamic> payload) async {
    await Future.delayed(const Duration(milliseconds: 500));
    return {
      'status': 'ok',
      'message': 'Override file written (mock)',
      'path': 'docker-compose.override.yml',
    };
  }

  @override
  Future<Map<String, dynamic>> getFrigateConfig() async {
    await Future.delayed(const Duration(milliseconds: 500));
    return {
      'config': {
        'mqtt': {'host': 'localhost', 'port': 1883},
        'cameras': {
          'cam1': {'enabled': true, 'detect': {'width': 640, 'height': 480}},
        },
      },
    };
  }

  @override
  Future<Map<String, dynamic>> updateFrigateConfig(Map<String, dynamic> payload) async {
    await Future.delayed(const Duration(milliseconds: 500));
    return {
      'status': 'ok',
      'message': 'Frigate config updated (mock)',
      'config': payload,
    };
  }

  @override
  Future<List<ReportRule>> getReportRules() async {
    await Future.delayed(const Duration(milliseconds: 500));
    return [
      ReportRule(
        id: 'mock-rule-1',
        name: 'گزارش روزانه امنیت',
        enabled: true,
        zones: ['main_gate', 'warehouse_sensitive'],
        cameras: ['cam1'],
        labels: ['person'],
        intervalHours: 24,
        destination: 'telegram',
        createdAt: '2026-07-20T08:00:00',
        lastRun: '2026-07-23T08:00:00',
        lastStatus: 'success',
      ),
      ReportRule(
        id: 'mock-rule-2',
        name: 'حضور پرسنل',
        enabled: false,
        zones: ['ahmad_table', 'soleymani_table'],
        cameras: ['cam1'],
        labels: ['person'],
        intervalHours: 12,
        destination: 'bale',
        createdAt: '2026-07-21T10:00:00',
        lastRun: '',
        lastStatus: '',
      ),
    ];
  }

  @override
  Future<ReportRule> createReportRule(Map<String, dynamic> payload) async {
    await Future.delayed(const Duration(milliseconds: 500));
    return ReportRule.fromJson({
      ...payload,
      'id': 'mock-rule-${DateTime.now().millisecondsSinceEpoch}',
      'created_at': DateTime.now().toIso8601String(),
      'last_run': '',
      'last_status': '',
    });
  }

  @override
  Future<ReportRule> updateReportRule(String id, Map<String, dynamic> payload) async {
    await Future.delayed(const Duration(milliseconds: 500));
    return ReportRule.fromJson({
      'id': id,
      'name': payload['name'] ?? 'Updated Rule',
      'enabled': payload['enabled'] ?? true,
      'zones': payload['zones'] ?? [],
      'cameras': payload['cameras'] ?? [],
      'labels': payload['labels'] ?? [],
      'interval_hours': payload['interval_hours'] ?? 24,
      'timezone': payload['timezone'] ?? 'Asia/Tehran',
      'destination': payload['destination'] ?? 'telegram',
      'chat_id': payload['chat_id'] ?? '',
      'prompt_template': payload['prompt_template'] ?? '',
      'include_summary': payload['include_summary'] ?? true,
      'include_raw_data': payload['include_raw_data'] ?? false,
      'created_at': '2026-07-20T08:00:00',
      'last_run': '',
      'last_status': '',
    });
  }

  @override
  Future<void> deleteReportRule(String id) async {
    await Future.delayed(const Duration(milliseconds: 300));
  }

  @override
  Future<Map<String, dynamic>> testRunRule(String id) async {
    await Future.delayed(const Duration(seconds: 2));
    return {
      'status': 'ok',
      'message': 'Report generated (mock)',
      'rule_id': id,
    };
  }

  @override
  Future<List<Map<String, dynamic>>> getRuleHistory(String id) async {
    await Future.delayed(const Duration(milliseconds: 500));
    return [
      {
        'id': 'hist-1',
        'rule_id': id,
        'rule_name': 'Test Rule',
        'executed_at': '2026-07-23T08:00:00',
        'status': 'success',
        'message_preview': '📊 گزارش — 3 نفر حاضر',
        'destination': 'telegram',
      },
    ];
  }
}
