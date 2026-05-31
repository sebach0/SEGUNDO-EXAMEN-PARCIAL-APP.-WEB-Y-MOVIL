import 'package:dio/dio.dart';

import '../../core/constants/api_constants.dart';
import '../../core/network/api_error.dart';
import '../../core/network/tecnico_api_client.dart';
import '../domain/models/auth_me.dart';
import '../domain/models/tecnico_perfil.dart';

/// Autenticación y perfil del flujo técnico / responsable (tokens propios).
final class TecnicoAuthRepository {
  TecnicoAuthRepository(this._dio, {TecnicoApiClient? api})
      : _api = api ?? TecnicoApiClient();

  final Dio _dio;
  final TecnicoApiClient _api;

  static bool rolesPermitidosTecnicoApp(List<String> roles) {
    return roles.any((r) => r == 'TECNICO' || r == 'TALLER_RESPONSABLE');
  }

  Future<AuthMe> login({required String email, required String password}) async {
    try {
      final res = await _dio.post<Map<String, dynamic>>(
        ApiConstants.login,
        data: {'email': email.trim(), 'password': password},
      );
      final data = res.data;
      if (data == null) throw Exception('Respuesta inválida del servidor.');
      final access = data['access_token'] as String?;
      final refresh = data['refresh_token'] as String?;
      if (access == null || refresh == null) {
        throw Exception('Respuesta inválida del servidor.');
      }
      await _api.persistTokens(access: access, refresh: refresh);

      final me = await fetchMe();
      if (!rolesPermitidosTecnicoApp(me.roles)) {
        await logoutLocal();
        throw Exception(
          'Esta cuenta no tiene rol de técnico o responsable de taller. '
          'Usá el acceso cliente si sos propietario.',
        );
      }
      return me;
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }

  Future<AuthMe> fetchMe() async {
    try {
      final res = await _dio.get<Map<String, dynamic>>(ApiConstants.me);
      final data = res.data;
      if (data == null) throw Exception('Respuesta vacía de /auth/me');
      return AuthMe.fromJson(data);
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }

  Future<TecnicoPerfil> fetchPerfilCompleto(AuthMe me) async {
    try {
      if (me.roles.contains('TALLER_RESPONSABLE')) {
        final res = await _dio.get<Map<String, dynamic>>(ApiConstants.appTallerMiTaller);
        final data = res.data;
        if (data == null) {
          return TecnicoPerfil.minimal(me);
        }
        return TecnicoPerfil.fromMiTaller(me: me, tallerJson: data);
      }
      if (me.roles.contains('TECNICO')) {
        final res = await _dio.get<List<dynamic>>(ApiConstants.tecnicos);
        final list = res.data ?? const [];
        Map<String, dynamic>? row;
        for (final e in list) {
          if (e is Map<String, dynamic> && e['usuario_id'] == me.id) {
            row = e;
            break;
          }
        }
        if (row == null) {
          return TecnicoPerfil.minimal(me);
        }
        final tallerId = row['taller_id'] as int?;
        String? tallerNombre;
        if (tallerId != null) {
          try {
            final tr = await _dio.get<Map<String, dynamic>>(ApiConstants.tallerById(tallerId));
            tallerNombre = tr.data?['nombre_comercial'] as String?;
          } catch (_) {
            tallerNombre = null;
          }
        }
        return TecnicoPerfil.fromTecnicoRow(me: me, tecnicoJson: row, tallerNombre: tallerNombre);
      }
      return TecnicoPerfil.minimal(me);
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }

  Future<void> logout() async {
    try {
      await _dio.post<void>(ApiConstants.logout);
    } catch (_) {
      // Limpia sesión local aunque falle el backend.
    } finally {
      await _api.clearTokens();
    }
  }

  Future<void> logoutLocal() async {
    await _api.clearTokens();
  }

  Future<String?> readAccessToken() => _api.readAccessToken();
}
