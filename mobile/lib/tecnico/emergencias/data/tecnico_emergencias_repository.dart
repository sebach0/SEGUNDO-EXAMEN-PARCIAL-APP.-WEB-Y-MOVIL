import 'package:dio/dio.dart';

import '../../../cliente/comunicacion/domain/mensaje_solicitud_models.dart';
import '../../../cliente/emergencias/domain/solicitud_emergencia_models.dart';
import '../../../cliente/emergencias/domain/ubicacion_tecnico_compartida.dart';
import '../../../core/constants/api_constants.dart';
import '../../../core/network/api_error.dart';
import '../domain/tecnico_servicio_models.dart';

final class TecnicoEmergenciasRepository {
  TecnicoEmergenciasRepository(this._dio);

  final Dio _dio;

  Future<List<ServicioAsignadoTecnico>> listarServiciosAsignados() async {
    try {
      final res = await _dio.get<List<dynamic>>(ApiConstants.appTecnicoEmergenciasServiciosAsignados);
      final list = res.data ?? const [];
      return list
          .whereType<Map>()
          .map((e) => ServicioAsignadoTecnico.fromJson(Map<String, dynamic>.from(e)))
          .toList();
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }

  Future<UbicacionClienteActual> obtenerUbicacionCliente(int solicitudId) async {
    try {
      final res = await _dio.get<Map<String, dynamic>>(
        ApiConstants.appTecnicoEmergenciaUbicacion(solicitudId),
      );
      final data = res.data;
      if (data == null) throw Exception('Respuesta vacía de ubicación.');
      return UbicacionClienteActual.fromJson(data);
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }

  Future<UbicacionTecnicoCompartida> compartirUbicacionTecnico(
    int solicitudId, {
    required double latitud,
    required double longitud,
    double? precisionMetros,
  }) async {
    try {
      final res = await _dio.post<Map<String, dynamic>>(
        ApiConstants.appTecnicoEmergenciaUbicacionTecnico(solicitudId),
        data: {
          'latitud': latitud,
          'longitud': longitud,
          if (precisionMetros != null) 'precision_metros': precisionMetros,
          'es_actual': true,
        },
      );
      final data = res.data;
      if (data == null) throw Exception('Respuesta vacía al compartir ubicación.');
      return UbicacionTecnicoCompartida.fromJson(data);
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }

  Future<ServicioAsignadoTecnico> actualizarEstado({
    required int solicitudId,
    required EstadoSolicitudEmergencia nuevoEstado,
    String? observacion,
    double? presupuestoBob,
  }) async {
    try {
      final res = await _dio.patch<Map<String, dynamic>>(
        ApiConstants.appTecnicoEmergenciaEstado(solicitudId),
        data: {
          'nuevo_estado': nuevoEstado.apiValue,
          'observacion': observacion,
          if (presupuestoBob != null) 'presupuesto_bob': presupuestoBob,
        },
      );
      final data = res.data;
      if (data == null) throw Exception('Respuesta vacía al actualizar estado.');
      return ServicioAsignadoTecnico.fromJson(data);
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }

  Future<List<MensajeSolicitudRead>> listarMensajes(int solicitudId) async {
    try {
      final res = await _dio.get<List<dynamic>>(ApiConstants.appTecnicoEmergenciaMensajes(solicitudId));
      final list = res.data ?? const [];
      return list
          .whereType<Map>()
          .map((e) => MensajeSolicitudRead.fromJson(Map<String, dynamic>.from(e)))
          .toList();
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
        ApiConstants.appTecnicoEmergenciaMensajes(solicitudId),
        data: {'mensaje': texto},
      );
      final data = res.data;
      if (data == null) throw Exception('Respuesta vacía al enviar mensaje.');
      return MensajeSolicitudRead.fromJson(data);
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }
}
