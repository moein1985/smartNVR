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
    return {'status': 'ok', 'db_connected': true};
  }
}
