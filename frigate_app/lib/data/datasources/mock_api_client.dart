import 'api_client.dart';

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
}
