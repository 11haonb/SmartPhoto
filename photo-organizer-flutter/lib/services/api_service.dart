import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:photo_organizer/utils/constants.dart';
import 'package:photo_organizer/models/models.dart';

class ApiService {
  late final Dio _dio;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  ApiService() {
    _dio = Dio(BaseOptions(
      baseUrl: ApiConfig.baseUrl,
      connectTimeout: ApiConfig.connectTimeout,
      receiveTimeout: ApiConfig.receiveTimeout,
    ));

    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _storage.read(key: 'access_token');
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (error, handler) {
        if (error.response?.statusCode == 401) {
          _storage.delete(key: 'access_token');
        }
        handler.next(error);
      },
    ));
  }

  Future<void> saveToken(String token) async {
    await _storage.write(key: 'access_token', value: token);
  }

  Future<String?> getToken() async {
    return await _storage.read(key: 'access_token');
  }

  Future<void> clearToken() async {
    await _storage.delete(key: 'access_token');
  }

  // ── Auth ──
  Future<void> sendSmsCode(String phone) async {
    await _dio.post('/auth/send-code', data: {'phone': phone});
  }

  Future<Map<String, dynamic>> login(String phone, String code) async {
    final response = await _dio.post('/auth/login', data: {
      'phone': phone,
      'code': code,
    });
    return response.data;
  }

  // ── Photos ──
  Future<Map<String, dynamic>> createBatch(int totalPhotos) async {
    final response = await _dio.post('/photos/batch', data: {
      'total_photos': totalPhotos,
    });
    return response.data;
  }

  Future<Map<String, dynamic>> uploadPhoto(
    String batchId,
    File file, {
    void Function(int, int)? onProgress,
  }) async {
    final formData = FormData.fromMap({
      'batch_id': batchId,
      'file': await MultipartFile.fromFile(
        file.path,
        filename: file.path.split('/').last,
      ),
    });

    final response = await _dio.post(
      '/photos/upload',
      data: formData,
      options: Options(
        sendTimeout: ApiConfig.uploadTimeout,
        receiveTimeout: ApiConfig.uploadTimeout,
      ),
      onSendProgress: onProgress,
    );
    return response.data;
  }

  Future<List<PhotoModel>> getBatchPhotos(String batchId) async {
    final response = await _dio.get('/photos/batch/$batchId');
    return (response.data as List)
        .map((e) => PhotoModel.fromJson(e))
        .toList();
  }

  Future<PhotoDetailModel> getPhotoDetail(String photoId) async {
    final response = await _dio.get('/photos/$photoId');
    return PhotoDetailModel.fromJson(response.data);
  }

  Future<void> deletePhoto(String photoId) async {
    await _dio.delete('/photos/$photoId');
  }

  // ── Organize ──
  Future<Map<String, dynamic>> startOrganize(String batchId) async {
    final response = await _dio.post('/organize/start', data: {
      'batch_id': batchId,
    });
    return response.data;
  }

  Future<ProcessingTaskModel> getOrganizeStatus(String taskId) async {
    final response = await _dio.get('/organize/status/$taskId');
    return ProcessingTaskModel.fromJson(response.data);
  }

  Future<OrganizeResultsModel> getOrganizeResults(String taskId) async {
    final response = await _dio.get('/organize/results/$taskId');
    return OrganizeResultsModel.fromJson(response.data);
  }

  // ── Settings ──
  Future<Map<String, dynamic>> getSettings() async {
    final response = await _dio.get('/settings');
    return response.data;
  }

  Future<Map<String, dynamic>> updateSettings(Map<String, dynamic> data) async {
    final response = await _dio.put('/settings', data: data);
    return response.data;
  }

  Future<List<AIProviderModel>> getAIProviders() async {
    final response = await _dio.get('/settings/ai-providers');
    return (response.data as List)
        .map((e) => AIProviderModel.fromJson(e))
        .toList();
  }
}
