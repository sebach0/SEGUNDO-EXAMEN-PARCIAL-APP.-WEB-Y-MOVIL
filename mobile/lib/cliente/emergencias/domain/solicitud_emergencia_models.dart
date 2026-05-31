// Modelos de dominio — API `/app/cliente/emergencias` (snake_case JSON).
import 'package:flutter/foundation.dart';

import '../../../core/utils/api_datetime.dart';
import 'solicitud_ai_payload.dart';

double _asDouble(Object? v) {
  if (v is num) return v.toDouble();
  if (v is String) return double.parse(v);
  throw FormatException('No es número: $v');
}

double? _asDoubleNullable(Object? v) {
  if (v == null) return null;
  if (v is num) return v.toDouble();
  if (v is String) return double.parse(v);
  throw FormatException('No es número: $v');
}

DateTime _asDateTime(Object? v) {
  return parseApiDateTime(v);
}

enum EstadoSolicitudEmergencia {
  registrada('REGISTRADA'),
  enRevision('EN_REVISION'),
  tallerAsignado('TALLER_ASIGNADO'),
  tecnicoAsignado('TECNICO_ASIGNADO'),
  enCamino('EN_CAMINO'),
  enAtencion('EN_ATENCION'),
  finalizada('FINALIZADA'),
  cancelada('CANCELADA');

  const EstadoSolicitudEmergencia(this.apiValue);
  final String apiValue;

  static EstadoSolicitudEmergencia parse(String s) {
    return EstadoSolicitudEmergencia.values.firstWhere(
      (e) => e.apiValue == s,
      orElse: () => EstadoSolicitudEmergencia.registrada,
    );
  }

  /// Etiqueta corta para UI (español).
  String get etiquetaUi => switch (this) {
        EstadoSolicitudEmergencia.registrada => 'Registrada',
        EstadoSolicitudEmergencia.enRevision => 'En revisión',
        EstadoSolicitudEmergencia.tallerAsignado => 'Taller asignado',
        EstadoSolicitudEmergencia.tecnicoAsignado => 'Técnico asignado',
        EstadoSolicitudEmergencia.enCamino => 'En camino',
        EstadoSolicitudEmergencia.enAtencion => 'En atención',
        EstadoSolicitudEmergencia.finalizada => 'Finalizada',
        EstadoSolicitudEmergencia.cancelada => 'Cancelada',
      };
}

enum TipoEvidenciaSolicitud {
  foto('FOTO'),
  audio('AUDIO');

  const TipoEvidenciaSolicitud(this.apiValue);
  final String apiValue;

  static TipoEvidenciaSolicitud parse(String s) {
    return TipoEvidenciaSolicitud.values.firstWhere((e) => e.apiValue == s);
  }
}

@immutable
class SolicitudUbicacionRead {
  const SolicitudUbicacionRead({
    required this.id,
    required this.solicitudId,
    required this.latitud,
    required this.longitud,
    this.precisionMetros,
    this.direccionReferencia,
    required this.esActual,
    required this.registradoAt,
  });

  final int id;
  final int solicitudId;
  final double latitud;
  final double longitud;
  final double? precisionMetros;
  final String? direccionReferencia;
  final bool esActual;
  final DateTime registradoAt;

  factory SolicitudUbicacionRead.fromJson(Map<String, dynamic> j) {
    return SolicitudUbicacionRead(
      id: j['id'] as int,
      solicitudId: j['solicitud_id'] as int,
      latitud: _asDouble(j['latitud']),
      longitud: _asDouble(j['longitud']),
      precisionMetros: j['precision_metros'] != null ? _asDouble(j['precision_metros']) : null,
      direccionReferencia: j['direccion_referencia'] as String?,
      esActual: j['es_actual'] as bool,
      registradoAt: _asDateTime(j['registrado_at']),
    );
  }
}

@immutable
class SolicitudEvidenciaRead {
  const SolicitudEvidenciaRead({
    required this.id,
    required this.solicitudId,
    required this.tipo,
    required this.archivoUrl,
    this.mimeType,
    this.nombreArchivo,
    this.tamanoBytes,
    required this.createdAt,
  });

  final int id;
  final int solicitudId;
  final TipoEvidenciaSolicitud tipo;
  final String archivoUrl;
  final String? mimeType;
  final String? nombreArchivo;
  final int? tamanoBytes;
  final DateTime createdAt;

  factory SolicitudEvidenciaRead.fromJson(Map<String, dynamic> j) {
    return SolicitudEvidenciaRead(
      id: j['id'] as int,
      solicitudId: j['solicitud_id'] as int,
      tipo: TipoEvidenciaSolicitud.parse(j['tipo'] as String),
      archivoUrl: j['archivo_url'] as String,
      mimeType: j['mime_type'] as String?,
      nombreArchivo: j['nombre_archivo'] as String?,
      tamanoBytes: j['tamano_bytes'] as int?,
      createdAt: _asDateTime(j['created_at']),
    );
  }
}

@immutable
class SolicitudEmergenciaDetail {
  const SolicitudEmergenciaDetail({
    required this.id,
    required this.clienteId,
    required this.vehiculoId,
    required this.estado,
    this.descripcionTexto,
    required this.createdAt,
    required this.updatedAt,
    required this.ubicaciones,
    required this.evidencias,
    this.tallerId,
    this.tecnicoId,
    this.tiempoEstimadoMin,
    this.finalizadaAt,
    this.presupuestoBob,
    this.presupuestoRegistradoAt,
    this.aiPayload,
  });

  final int id;
  final int clienteId;
  final int vehiculoId;
  final EstadoSolicitudEmergencia estado;
  final String? descripcionTexto;
  final DateTime createdAt;
  final DateTime updatedAt;
  final List<SolicitudUbicacionRead> ubicaciones;
  final List<SolicitudEvidenciaRead> evidencias;
  final int? tallerId;
  final int? tecnicoId;
  final int? tiempoEstimadoMin;
  final DateTime? finalizadaAt;
  /// Presupuesto en BOB que puede registrar el técnico al pasar a atención.
  final double? presupuestoBob;
  final DateTime? presupuestoRegistradoAt;
  final SolicitudAiPayloadV1? aiPayload;

  factory SolicitudEmergenciaDetail.fromJson(Map<String, dynamic> j) {
    return SolicitudEmergenciaDetail(
      id: j['id'] as int,
      clienteId: j['cliente_id'] as int,
      vehiculoId: j['vehiculo_id'] as int,
      estado: EstadoSolicitudEmergencia.parse(j['estado'] as String),
      descripcionTexto: j['descripcion_texto'] as String?,
      createdAt: _asDateTime(j['created_at']),
      updatedAt: _asDateTime(j['updated_at']),
      ubicaciones: [
        for (final e in j['ubicaciones'] as List<dynamic>? ?? [])
          if (e is Map<String, dynamic>) SolicitudUbicacionRead.fromJson(e),
      ],
      evidencias: [
        for (final e in j['evidencias'] as List<dynamic>? ?? [])
          if (e is Map<String, dynamic>) SolicitudEvidenciaRead.fromJson(e),
      ],
      tallerId: j['taller_id'] as int?,
      tecnicoId: j['tecnico_id'] as int?,
      tiempoEstimadoMin: j['tiempo_estimado_min'] as int?,
      finalizadaAt: j['finalizada_at'] != null ? _asDateTime(j['finalizada_at']) : null,
      presupuestoBob: _asDoubleNullable(j['presupuesto_bob']),
      presupuestoRegistradoAt: j['presupuesto_registrado_at'] != null
          ? _asDateTime(j['presupuesto_registrado_at'])
          : null,
      aiPayload: SolicitudAiPayloadV1.tryParse(j['ai_payload']),
    );
  }
}

@immutable
class SolicitudEmergenciaListItem {
  const SolicitudEmergenciaListItem({
    required this.id,
    required this.clienteId,
    required this.vehiculoId,
    required this.estado,
    this.descripcionTexto,
    required this.createdAt,
    required this.updatedAt,
    this.tallerId,
    this.tecnicoId,
    this.tiempoEstimadoMin,
    this.finalizadaAt,
    this.aiPayload,
  });

  final int id;
  final int clienteId;
  final int vehiculoId;
  final EstadoSolicitudEmergencia estado;
  final String? descripcionTexto;
  final DateTime createdAt;
  final DateTime updatedAt;
  final int? tallerId;
  final int? tecnicoId;
  final int? tiempoEstimadoMin;
  final DateTime? finalizadaAt;
  final SolicitudAiPayloadV1? aiPayload;

  factory SolicitudEmergenciaListItem.fromJson(Map<String, dynamic> j) {
    return SolicitudEmergenciaListItem(
      id: j['id'] as int,
      clienteId: j['cliente_id'] as int,
      vehiculoId: j['vehiculo_id'] as int,
      estado: EstadoSolicitudEmergencia.parse(j['estado'] as String),
      descripcionTexto: j['descripcion_texto'] as String?,
      createdAt: _asDateTime(j['created_at']),
      updatedAt: _asDateTime(j['updated_at']),
      tallerId: j['taller_id'] as int?,
      tecnicoId: j['tecnico_id'] as int?,
      tiempoEstimadoMin: j['tiempo_estimado_min'] as int?,
      finalizadaAt: j['finalizada_at'] != null ? _asDateTime(j['finalizada_at']) : null,
      aiPayload: SolicitudAiPayloadV1.tryParse(j['ai_payload']),
    );
  }
}
