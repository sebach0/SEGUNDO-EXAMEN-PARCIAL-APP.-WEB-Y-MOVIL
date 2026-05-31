import 'package:dio/dio.dart';

import '../../../core/constants/api_constants.dart';
import '../../../core/network/api_error.dart';
import '../domain/pago_models.dart';

/// CU20 — API pagos por solicitud (cliente autenticado).
final class PagosRepository {
  PagosRepository(this._dio);

  final Dio _dio;

  Future<List<PagoRead>> listarPorSolicitud(int solicitudId) async {
    try {
      final res = await _dio.get<List<dynamic>>(ApiConstants.appClienteEmergenciaPagos(solicitudId));
      final raw = res.data ?? [];
      return [
        for (final e in raw)
          if (e is Map<String, dynamic>) PagoRead.fromJson(e),
      ];
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }

  Future<PagoRead> iniciarPago({
    required int solicitudId,
    required double monto,
    required MetodoPago metodo,
    String moneda = 'BOB',
  }) async {
    try {
      final res = await _dio.post<Map<String, dynamic>>(
        ApiConstants.appClienteEmergenciaPagos(solicitudId),
        data: {
          'monto': monto,
          'metodo': metodo.apiValue,
          'moneda': moneda,
        },
      );
      final m = res.data;
      if (m == null) throw Exception('Respuesta vacía');
      return PagoRead.fromJson(m);
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }

  /// Segundo paso si el backend deja el pago en `PENDIENTE` (`PAGO_SIMULADO_AUTOCOMPLETE=false`).
  Future<PagoRead> completarSimulado({
    required int solicitudId,
    required int pagoId,
  }) async {
    try {
      final res = await _dio.post<Map<String, dynamic>>(
        ApiConstants.appClienteEmergenciaPagoCompletarSimulado(solicitudId, pagoId),
      );
      final m = res.data;
      if (m == null) throw Exception('Respuesta vacía');
      return PagoRead.fromJson(m);
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }

  Future<PagoRead> confirmarStripe({
    required int solicitudId,
    required int pagoId,
    String? paymentIntentId,
  }) async {
    try {
      final res = await _dio.post<Map<String, dynamic>>(
        ApiConstants.appClienteEmergenciaPagoConfirmarStripe(solicitudId, pagoId),
        data: {
          if (paymentIntentId != null) 'payment_intent_id': paymentIntentId,
        },
      );
      final m = res.data;
      if (m == null) throw Exception('Respuesta vacía');
      return PagoRead.fromJson(m);
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }
}
