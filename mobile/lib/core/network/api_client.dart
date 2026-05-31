// lib/core/network/api_client.dart
// =========================================================
// Cliente HTTP centralizado con Dio
// Maneja: token JWT, refresh, errores y timeouts
// =========================================================
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../constants/api_constants.dart';

class ApiClient {
  static final ApiClient _instance = ApiClient._internal();
  factory ApiClient() => _instance;

  late final Dio _dio;
  final _storage = const FlutterSecureStorage();

  ApiClient._internal() {
    _dio = Dio(BaseOptions(
      baseUrl: ApiConstants.baseUrl,
      connectTimeout: ApiConstants.connectTimeout,
      receiveTimeout: ApiConstants.receiveTimeout,
      headers: {'Content-Type': 'application/json'},
    ));

    // Interceptor: inyectar token JWT en cada request
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        if (options.data is FormData) {
          options.headers.remove(Headers.contentTypeHeader);
        }
        final token = await _storage.read(key: 'access_token');
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
      onError: (error, handler) {
        // Si 401: sesión expirada — navegar a login (manejado por el BLoC/Provider)
        if (error.response?.statusCode == 401) {
          _storage.deleteAll();
        }
        return handler.next(error);
      },
    ));
  }

  Dio get dio => _dio;
}
