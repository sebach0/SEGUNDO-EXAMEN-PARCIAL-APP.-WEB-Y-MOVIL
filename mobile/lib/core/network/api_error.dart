import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import '../constants/api_constants.dart';

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
  final data = e.response?.data;
  if (data is Map<String, dynamic> && data['detail'] != null) {
    final detail = data['detail'];
    return switch (detail) {
      String s => s,
      List list => list
          .map((x) => x is Map ? (x['msg'] ?? x).toString() : x.toString())
          .join('\n'),
      _ => 'No se pudo completar la solicitud.',
    };
  }
  return 'No se pudo completar la solicitud.';
}
