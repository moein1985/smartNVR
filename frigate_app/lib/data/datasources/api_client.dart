// ignore_for_file: use_null_aware_elements
import 'dart:io';
import 'package:dio/dio.dart';
import '../../core/config/app_config.dart';

abstract class BaseApiClient {
  Future<Map<String, dynamic>> query(String question, {int maxRetries});
  Future<List<Map<String, dynamic>>> getEvents({
    String? camera,
    String? label,
  });
  Future<Map<String, dynamic>> health();
  Future<Map<String, dynamic>> getCameras();
  Future<Map<String, dynamic>> getRecordings({
    String? camera,
    String? date,
    int? hour,
    double? startTime,
    double? endTime,
  });
  Future<Map<String, dynamic>> getSettings();
  Future<Map<String, dynamic>> updateSettings(
      Map<String, dynamic> newSettings);
  Future<String> getSystemLogs(int lines);
  Future<Map<String, dynamic>> uploadUpdate(File file);
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
    final now = DateTime.now();
    final response = await _dio.post('/api/v1/query', data: {
      'question': question,
      'max_retries': maxRetries,
      'client_timezone': now.timeZoneName,
      'client_offset_minutes': now.timeZoneOffset.inMinutes,
      'client_timestamp': now.millisecondsSinceEpoch / 1000.0,
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

  @override
  Future<Map<String, dynamic>> getCameras() async {
    final response = await _dio.get('/api/v1/cameras');
    return response.data as Map<String, dynamic>;
  }

  @override
  Future<Map<String, dynamic>> getRecordings({
    String? camera,
    String? date,
    int? hour,
    double? startTime,
    double? endTime,
  }) async {
    final params = <String, dynamic>{
      if (camera != null) 'camera': camera,
      if (date != null) 'date': date,
      if (hour != null) 'hour': hour,
      if (startTime != null) 'start_time': startTime,
      if (endTime != null) 'end_time': endTime,
    };
    final response = await _dio.get('/api/v1/recordings', queryParameters: params);
    return response.data as Map<String, dynamic>;
  }

  @override
  Future<Map<String, dynamic>> getSettings() async {
    final response = await _dio.get('/api/v1/settings');
    return response.data as Map<String, dynamic>;
  }

  @override
  Future<Map<String, dynamic>> updateSettings(
      Map<String, dynamic> newSettings) async {
    final response = await _dio.post('/api/v1/settings', data: newSettings);
    return response.data as Map<String, dynamic>;
  }

  @override
  Future<String> getSystemLogs(int lines) async {
    final response = await _dio.get(
      '/api/v1/system/logs',
      queryParameters: {'lines': lines},
    );
    final data = response.data as Map<String, dynamic>;
    final logLines = data['lines'] as List;
    return logLines.cast<String>().join('\n');
  }

  @override
  Future<Map<String, dynamic>> uploadUpdate(File file) async {
    final formData = FormData.fromMap({
      'file': await MultipartFile.fromFile(file.path),
    });
    final response = await _dio.post(
      '/api/v1/system/update',
      data: formData,
      options: Options(
        sendTimeout: const Duration(minutes: 10),
        receiveTimeout: const Duration(minutes: 5),
      ),
    );
    return response.data as Map<String, dynamic>;
  }
}
