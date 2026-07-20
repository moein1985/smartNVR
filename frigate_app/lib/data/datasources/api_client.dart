// ignore_for_file: use_null_aware_elements
import 'package:dio/dio.dart';
import '../../core/config/app_config.dart';

abstract class BaseApiClient {
  Future<Map<String, dynamic>> query(String question, {int maxRetries});
  Future<List<Map<String, dynamic>>> getEvents({
    String? camera,
    String? label,
  });
  Future<Map<String, dynamic>> health();
}

class ApiClient implements BaseApiClient {
  Dio _dio;

  ApiClient(ServerConfig config) : _dio = _createDio(config);

  static Dio _createDio(ServerConfig config) {
    return Dio(BaseOptions(
      baseUrl: config.baseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 30),
      headers: {'Content-Type': 'application/json'},
    ));
  }

  void updateConfig(ServerConfig config) {
    _dio = _createDio(config);
  }

  Dio get dio => _dio;

  @override
  Future<Map<String, dynamic>> query(String question,
      {int maxRetries = 3}) async {
    final response = await _dio.post('/api/v1/query', data: {
      'question': question,
      'max_retries': maxRetries,
    });
    return response.data as Map<String, dynamic>;
  }

  @override
  Future<List<Map<String, dynamic>>> getEvents({
    String? camera,
    String? label,
  }) async {
    final params = <String, dynamic>{
      if (camera != null) 'camera': camera,
      if (label != null) 'label': label,
    };
    final response = await _dio.get('/api/v1/events', queryParameters: params);
    final data = response.data as Map<String, dynamic>;
    final events = data['events'] as List;
    return events.cast<Map<String, dynamic>>();
  }

  @override
  Future<Map<String, dynamic>> health() async {
    final response = await _dio.get('/api/v1/health');
    return response.data as Map<String, dynamic>;
  }
}
