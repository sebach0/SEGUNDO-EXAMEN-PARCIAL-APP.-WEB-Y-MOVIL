// Repositorio — consumo del API de emergencias.
import 'package:dio/dio.dart';
import 'package:http_parser/http_parser.dart';

import '../../../core/constants/api_constants.dart';
import '../../../core/network/api_error.dart';
import '../domain/solicitud_emergencia_models.dart';
import '../domain/solicitud_seguimiento_models.dart';
import '../domain/ubicacion_tecnico_compartida.dart';

final class EmergenciasRepository {
  EmergenciasRepository(this._dio);

  final Dio _dio;

  Future<List<SolicitudEmergenciaListItem>> listMine() async {
    try {
      final res = await _dio.get<List<dynamic>>(ApiConstants.appClienteEmergencias);
      final raw = res.data ?? [];
      return [
        for (final e in raw)
          if (e is Map<String, dynamic>) SolicitudEmergenciaListItem.fromJson(e),
      ];
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }

  Future<SolicitudEmergenciaDetail> fetchDetail(int solicitudId) async {
    try {
      final res = await _dio.get<Map<String, dynamic>>(ApiConstants.appClienteEmergencia(solicitudId));
      final m = res.data;
      if (m == null) throw Exception('Solicitud no encontrada');
      return SolicitudEmergenciaDetail.fromJson(m);
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }

  /// Estado, historial, taller, técnico y ETA.
  Future<SolicitudSeguimiento> fetchSeguimiento(int solicitudId) async {
    try {
      final res = await _dio.get<Map<String, dynamic>>(
        ApiConstants.appClienteEmergenciaSeguimiento(solicitudId),
      );
      final m = res.data;
      if (m == null) throw Exception('Seguimiento no disponible');
      return SolicitudSeguimiento.fromJson(m);
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }

  Future<UbicacionTecnicoCompartida> fetchUbicacionTecnico(int solicitudId) async {
    try {
      final res = await _dio.get<Map<String, dynamic>>(
        ApiConstants.appClienteEmergenciaUbicacionTecnico(solicitudId),
      );
      final m = res.data;
      if (m == null) throw Exception('Ubicación no disponible');
      return UbicacionTecnicoCompartida.fromJson(m);
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }

  Future<SolicitudEmergenciaDetail> create({
    required int vehiculoId,
    String? descripcionTexto,
    Map<String, dynamic>? ubicacionInicial,
  }) async {
    try {
      final res = await _dio.post<Map<String, dynamic>>(
        ApiConstants.appClienteEmergencias,
        data: {
          'vehiculo_id': vehiculoId,
          if (descripcionTexto != null) 'descripcion_texto': descripcionTexto,
          if (ubicacionInicial != null) 'ubicacion_inicial': ubicacionInicial,
        },
      );
      final m = res.data;
      if (m == null) throw Exception('Respuesta vacía');
      return SolicitudEmergenciaDetail.fromJson(m);
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }

  Future<SolicitudEmergenciaDetail> patchTexto(int solicitudId, {String? descripcionTexto}) async {
    try {
      final res = await _dio.patch<Map<String, dynamic>>(
        ApiConstants.appClienteEmergencia(solicitudId),
        data: {'descripcion_texto': descripcionTexto},
      );
      final m = res.data;
      if (m == null) throw Exception('Respuesta vacía');
      return SolicitudEmergenciaDetail.fromJson(m);
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }

  Future<SolicitudEmergenciaDetail> postUbicacion(
    int solicitudId, {
    required double latitud,
    required double longitud,
    double? precisionMetros,
    String? direccionReferencia,
    bool esActual = true,
  }) async {
    try {
      final res = await _dio.post<Map<String, dynamic>>(
        ApiConstants.appClienteEmergenciaUbicaciones(solicitudId),
        data: {
          'latitud': latitud,
          'longitud': longitud,
          if (precisionMetros != null) 'precision_metros': precisionMetros,
          if (direccionReferencia != null) 'direccion_referencia': direccionReferencia,
          'es_actual': esActual,
        },
      );
      final m = res.data;
      if (m == null) throw Exception('Respuesta vacía');
      return SolicitudEmergenciaDetail.fromJson(m);
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }

  /// Subida directa al API (multipart). Preferido frente a [postEvidencia] con URL externa.
  Future<SolicitudEmergenciaDetail> postEvidenciaArchivo(
    int solicitudId, {
    required String tipoApi,
    required String filePath,
    required String filename,
    String? mimeType,
  }) async {
    try {
      final form = FormData.fromMap({
        'tipo': tipoApi,
        'file': await MultipartFile.fromFile(
          filePath,
          filename: filename,
          contentType: mimeType != null && mimeType.isNotEmpty
              ? MediaType.parse(mimeType)
              : null,
        ),
      });
      final res = await _dio.post<Map<String, dynamic>>(
        ApiConstants.appClienteEmergenciaEvidenciasArchivo(solicitudId),
        data: form,
      );
      final m = res.data;
      if (m == null) throw Exception('Respuesta vacía');
      return SolicitudEmergenciaDetail.fromJson(m);
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }

  Future<SolicitudEmergenciaDetail> postEvidencia(
    int solicitudId, {
    required String tipoApi, // FOTO | AUDIO
    required String archivoUrl,
    String? mimeType,
    String? nombreArchivo,
    int? tamanoBytes,
  }) async {
    try {
      final res = await _dio.post<Map<String, dynamic>>(
        ApiConstants.appClienteEmergenciaEvidencias(solicitudId),
        data: {
          'tipo': tipoApi,
          'archivo_url': archivoUrl,
          if (mimeType != null) 'mime_type': mimeType,
          if (nombreArchivo != null) 'nombre_archivo': nombreArchivo,
          if (tamanoBytes != null) 'tamano_bytes': tamanoBytes,
        },
      );
      final m = res.data;
      if (m == null) throw Exception('Respuesta vacía');
      return SolicitudEmergenciaDetail.fromJson(m);
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }
}
