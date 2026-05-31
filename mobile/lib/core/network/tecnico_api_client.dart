// Cliente HTTP para el módulo técnico — tokens separados del flujo cliente.
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../constants/api_constants.dart';

class TecnicoApiClient {
  static final TecnicoApiClient _instance = TecnicoApiClient._internal();
  factory TecnicoApiClient() => _instance;

  late final Dio _dio;
  final _storage = const FlutterSecureStorage();

  static const _accessKey = 'tecnico_access_token';
  static const _refreshKey = 'tecnico_refresh_token';

  TecnicoApiClient._internal() {
    _dio = Dio(BaseOptions(
      baseUrl: ApiConstants.baseUrl,
      connectTimeout: ApiConstants.connectTimeout,
      receiveTimeout: ApiConstants.receiveTimeout,
      headers: {'Content-Type': 'application/json'},
    ));

    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _storage.read(key: _accessKey);
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
      onError: (error, handler) {
        if (error.response?.statusCode == 401) {
          _storage.delete(key: _accessKey);
          _storage.delete(key: _refreshKey);
        }
        return handler.next(error);
      },
    ));
  }

  Dio get dio => _dio;

  Future<void> persistTokens({required String access, required String refresh}) async {
    await _storage.write(key: _accessKey, value: access);
    await _storage.write(key: _refreshKey, value: refresh);
  }

  Future<void> clearTokens() async {
    await _storage.delete(key: _accessKey);
    await _storage.delete(key: _refreshKey);
  }

  Future<String?> readAccessToken() => _storage.read(key: _accessKey);
}
