// Repositorio — cotizaciones del cliente.
import 'package:dio/dio.dart';

import '../../../core/constants/api_constants.dart';
import '../../../core/network/api_error.dart';
import '../domain/cotizacion_models.dart';

final class CotizacionRepository {
  CotizacionRepository(this._dio);

  final Dio _dio;

  /// Lista todas las cotizaciones enviadas para una solicitud.
  Future<List<Cotizacion>> listBySolicitud(int solicitudId) async {
    try {
      final res = await _dio.get<List<dynamic>>(
        ApiConstants.cotizacionesDeSolicitud(solicitudId),
      );
      final raw = res.data ?? [];
      return [
        for (final e in raw)
          if (e is Map<String, dynamic>) Cotizacion.fromJson(e),
      ];
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }

  /// El cliente selecciona una cotización. Las demás quedan EXPIRADAS.
  Future<Cotizacion> seleccionar(int solicitudId, int cotizacionId) async {
    try {
      final res = await _dio.post<Map<String, dynamic>>(
        ApiConstants.seleccionarCotizacion(solicitudId, cotizacionId),
      );
      final m = res.data;
      if (m == null) throw Exception('Respuesta vacía');
      return Cotizacion.fromJson(m);
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }
}
