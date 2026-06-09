import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../../../core/constants/api_constants.dart';
import '../../domain/models/cliente_mi_perfil.dart';
import '../../../core/network/api_error.dart';

/// Capa de datos: autenticación y registro cliente (sin estado de UI).
final class AuthRepository {
  AuthRepository(this._dio, {FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage();

  final Dio _dio;
  final FlutterSecureStorage _storage;

  Future<void> login({required String email, required String password}) async {
    try {
      final res = await _dio.post<Map<String, dynamic>>(
        ApiConstants.login,
        data: {'email': email.trim().toLowerCase(), 'password': password},
      );
      final data = res.data;
      if (data == null) throw Exception('Respuesta inválida del servidor.');
      final access = data['access_token'] as String?;
      final refresh = data['refresh_token'] as String?;
      if (access == null || refresh == null) {
        throw Exception('Respuesta inválida del servidor.');
      }
      await _storage.write(key: 'access_token', value: access);
      await _storage.write(key: 'refresh_token', value: refresh);
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }

  Future<void> solicitarRecuperacionContrasena({required String email}) async {
    try {
      await _dio.post<void>(
        ApiConstants.authSolicitarRecuperacionContrasena,
        data: {'email': email.trim()},
      );
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }

  Future<void> logoutLocal() async {
    await _storage.deleteAll();
  }

  Future<void> logout() async {
    try {
      await _dio
          .post<void>(ApiConstants.logout)
          .timeout(const Duration(seconds: 4));
    } catch (_) {
      // Aunque falle el backend, limpiamos sesión local.
    } finally {
      await logoutLocal();
    }
  }

  Future<ClienteMiPerfil> fetchMiPerfil() async {
    try {
      final res = await _dio.get<Map<String, dynamic>>(ApiConstants.appClienteMiPerfil);
      final data = res.data;
      if (data == null) {
        throw Exception('Respuesta vacía');
      }
      return ClienteMiPerfil.fromJson(data);
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }

  Future<ClienteMiPerfil> registerCliente({
    required String nombres,
    required String apellidos,
    required String email,
    required String telefono,
    required String password,
  }) async {
    try {
      final res = await _dio.post<Map<String, dynamic>>(
        ApiConstants.appClienteRegistro,
        data: {
          'nombres': nombres.trim(),
          'apellidos': apellidos.trim(),
          'email': email.trim(),
          'telefono': telefono.trim(),
          'password': password,
        },
      );
      final data = res.data;
      if (data == null) throw Exception('Respuesta vacía');
      return ClienteMiPerfil.fromJson(data);
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }

  Future<String?> readAccessToken() => _storage.read(key: 'access_token');

  Future<ClienteMiPerfil> updateMiPerfil({
    required String nombres,
    required String apellidos,
    required String telefono,
    required String ciudad,
    required String direccion,
  }) async {
    try {
      final data = <String, dynamic>{
        'nombres': nombres.trim(),
        'apellidos': apellidos.trim(),
        'telefono': telefono.trim(),
        'ciudad': ciudad.trim(),
        'direccion': direccion.trim(),
      };
      final res = await _dio.put<Map<String, dynamic>>(
        ApiConstants.appClienteMiPerfil,
        data: data,
      );
      final body = res.data;
      if (body == null) throw Exception('Respuesta vacía');
      return ClienteMiPerfil.fromJson(body);
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }
}
