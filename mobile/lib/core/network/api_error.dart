import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import '../constants/api_constants.dart';

/// True si el fallo parece de red (sin respuesta del servidor).
bool isNetworkFailure(Object error) {
  if (error is! DioException) return false;
  return error.type == DioExceptionType.connectionError ||
      error.type == DioExceptionType.connectionTimeout ||
      error.type == DioExceptionType.sendTimeout ||
      error.type == DioExceptionType.receiveTimeout;
}

/// Extrae mensaje legible de errores Dio / FastAPI.
String messageFromDio(Object error) {
  if (error is! DioException) {
    return 'Ocurrió un error inesperado.';
  }
  final e = error;
  return switch (e.type) {
    DioExceptionType.connectionTimeout ||
    DioExceptionType.sendTimeout ||
    DioExceptionType.receiveTimeout =>
      _timeoutMessage(),
    DioExceptionType.connectionError => _connectionErrorMessage(),
    _ => _detailFromResponse(e),
  };
}

String _timeoutMessage() {
  const base = 'Tiempo de espera agotado. Revisa tu conexión.';
  if (!kDebugMode) return base;
  return '$base\n\n[Debug] URL API: ${ApiConstants.baseUrl}\n'
      'Revisá mobile/.env → API_BASE_URL (misma red Wi‑Fi que el dispositivo).';
}

String _connectionErrorMessage() {
  const base = 'Sin conexión con el servidor.';
  if (!kDebugMode) return base;
  return '$base\n\n[Debug] URL API: ${ApiConstants.baseUrl}';
}

String _detailFromResponse(DioException e) {
  final status = e.response?.statusCode;
  final data = e.response?.data;
  if (data is Map<String, dynamic> && data['detail'] != null) {
    final detail = data['detail'];
    return switch (detail) {
      String s when s.isNotEmpty => s,
      List list => list
          .map((x) => x is Map ? (x['msg'] ?? x).toString() : x.toString())
          .join('\n'),
      _ => _fallbackForStatus(status),
    };
  }
  return _fallbackForStatus(status);
}

String _fallbackForStatus(int? status) {
  return switch (status) {
    401 => 'Credenciales incorrectas.',
    403 => 'No tienes permiso para esta acción.',
    404 => 'Recurso no encontrado en el servidor.',
    422 => 'Datos inválidos. Revisa el formulario.',
    500 => 'Error interno del servidor. Verifica que Docker (backend y base de datos) estén activos.',
    int s => 'No se pudo completar la solicitud (HTTP $s).',
    null => 'No se pudo completar la solicitud.',
  };
}
