import 'package:dio/dio.dart';

import '../../../core/constants/api_constants.dart';
import '../../../core/network/api_error.dart';
import '../domain/mensaje_solicitud_models.dart';
import '../domain/notificacion_models.dart';

/// CU19 (notificaciones, FCM) y CU21 (mensajes por solicitud) — capa datos.
final class ComunicacionRepository {
  ComunicacionRepository(this._dio);

  final Dio _dio;

  Future<List<NotificacionRead>> listarNotificaciones({
    bool soloNoLeidas = false,
    int limit = 100,
  }) async {
    try {
      final res = await _dio.get<List<dynamic>>(
        ApiConstants.appClienteNotificaciones,
        queryParameters: {
          'no_leidas': soloNoLeidas,
          'limit': limit,
        },
      );
      final raw = res.data ?? [];
      return [
        for (final e in raw)
          if (e is Map<String, dynamic>) NotificacionRead.fromJson(e),
      ];
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }

  Future<NotificacionRead?> obtenerNotificacionPorId(int id) async {
    final list = await listarNotificaciones(soloNoLeidas: false, limit: 200);
    try {
      return list.firstWhere((n) => n.id == id);
    } catch (_) {
      return null;
    }
  }

  Future<NotificacionRead> marcarNotificacionLeida(int notificacionId) async {
    try {
      final res = await _dio.patch<Map<String, dynamic>>(
        ApiConstants.appClienteNotificacionLeida(notificacionId),
      );
      final m = res.data;
      if (m == null) throw Exception('Respuesta vacía');
      return NotificacionRead.fromJson(m);
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }

  Future<List<MensajeSolicitudRead>> listarMensajesSolicitud(int solicitudId) async {
    try {
      final res = await _dio.get<List<dynamic>>(
        ApiConstants.appClienteEmergenciaMensajes(solicitudId),
      );
      final raw = res.data ?? [];
      return [
        for (final e in raw)
          if (e is Map<String, dynamic>) MensajeSolicitudRead.fromJson(e),
      ];
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }

  Future<MensajeSolicitudRead> enviarMensaje({
    required int solicitudId,
    required String texto,
  }) async {
    try {
      final res = await _dio.post<Map<String, dynamic>>(
        ApiConstants.appClienteEmergenciaMensajes(solicitudId),
        data: {'mensaje': texto},
      );
      final m = res.data;
      if (m == null) throw Exception('Respuesta vacía');
      return MensajeSolicitudRead.fromJson(m);
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }

  /// Registro de token FCM (CU19 push). Llamar cuando integres `firebase_messaging`.
  Future<void> registrarTokenFcm({required String token, String? platform}) async {
    try {
      await _dio.post<void>(
        ApiConstants.appClienteFcm,
        data: {
          'token': token,
          if (platform != null) 'platform': platform,
        },
      );
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }

  Future<void> eliminarTokenFcm({required String token, String? platform}) async {
    try {
      await _dio.delete<void>(
        ApiConstants.appClienteFcm,
        data: {
          'token': token,
          if (platform != null) 'platform': platform,
        },
      );
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }
}
