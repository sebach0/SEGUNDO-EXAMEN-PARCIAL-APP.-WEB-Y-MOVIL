// Modelos — GET `/app/cliente/emergencias/{id}/seguimiento` (CU16–CU18).
import 'package:flutter/foundation.dart';

import '../../../core/utils/api_datetime.dart';
import 'solicitud_ai_payload.dart';
import 'solicitud_emergencia_models.dart';

DateTime _asDateTime(Object? v) {
  return parseApiDateTime(v);
}

double? _asDoubleNullable(Object? v) {
  if (v == null) return null;
  if (v is num) return v.toDouble();
  if (v is String) return double.parse(v);
  throw FormatException('No es número: $v');
}

@immutable
class TallerSeguimientoRead {
  const TallerSeguimientoRead({
    required this.id,
    required this.nombreComercial,
    required this.telefonoContacto,
    required this.emailContacto,
    required this.direccion,
    required this.ciudad,
  });

  final int id;
  final String nombreComercial;
  final String telefonoContacto;
  final String emailContacto;
  final String direccion;
  final String ciudad;

  factory TallerSeguimientoRead.fromJson(Map<String, dynamic> j) {
    return TallerSeguimientoRead(
      id: j['id'] as int,
      nombreComercial: j['nombre_comercial'] as String,
      telefonoContacto: j['telefono_contacto'] as String,
      emailContacto: j['email_contacto'] as String,
      direccion: j['direccion'] as String,
      ciudad: j['ciudad'] as String,
    );
  }
}

@immutable
class TecnicoSeguimientoRead {
  const TecnicoSeguimientoRead({
    required this.id,
    required this.nombres,
    required this.apellidos,
    required this.telefono,
  });

  final int id;
  final String nombres;
  final String apellidos;
  final String telefono;

  String get nombreCompleto => '$nombres $apellidos'.trim();

  factory TecnicoSeguimientoRead.fromJson(Map<String, dynamic> j) {
    return TecnicoSeguimientoRead(
      id: j['id'] as int,
      nombres: j['nombres'] as String,
      apellidos: j['apellidos'] as String,
      telefono: j['telefono'] as String,
    );
  }
}

@immutable
class SolicitudHistorialEstadoRead {
  const SolicitudHistorialEstadoRead({
    required this.id,
    this.estadoAnterior,
    required this.estadoNuevo,
    this.observacion,
    required this.createdAt,
  });

  final int id;
  final EstadoSolicitudEmergencia? estadoAnterior;
  final EstadoSolicitudEmergencia estadoNuevo;
  final String? observacion;
  final DateTime createdAt;

  factory SolicitudHistorialEstadoRead.fromJson(Map<String, dynamic> j) {
    return SolicitudHistorialEstadoRead(
      id: j['id'] as int,
      estadoAnterior: j['estado_anterior'] != null
          ? EstadoSolicitudEmergencia.parse(j['estado_anterior'] as String)
          : null,
      estadoNuevo: EstadoSolicitudEmergencia.parse(j['estado_nuevo'] as String),
      observacion: j['observacion'] as String?,
      createdAt: _asDateTime(j['created_at']),
    );
  }
}

@immutable
class SolicitudSeguimiento {
  const SolicitudSeguimiento({
    required this.solicitudId,
    required this.estado,
    required this.updatedAt,
    this.tiempoEstimadoMin,
    this.finalizadaAt,
    this.taller,
    this.tecnico,
    required this.historialEstados,
    this.aiPayload,
    this.tieneUbicacionCliente = false,
    this.tieneEvidenciaFoto = false,
    this.tieneEvidenciaAudio = false,
    this.presupuestoBob,
    this.presupuestoRegistradoAt,
    this.minutosRetraso,
    this.servicioRetrasado = false,
    this.etaOrigen,
  });

  final int solicitudId;
  final EstadoSolicitudEmergencia estado;
  final DateTime updatedAt;
  final int? tiempoEstimadoMin;
  final DateTime? finalizadaAt;
  final TallerSeguimientoRead? taller;
  final TecnicoSeguimientoRead? tecnico;
  final List<SolicitudHistorialEstadoRead> historialEstados;
  final SolicitudAiPayloadV1? aiPayload;
  /// Alineado al backend: datos reales de la solicitud (puede contradecir el snapshot de IA al crear).
  final bool tieneUbicacionCliente;
  final bool tieneEvidenciaFoto;
  final bool tieneEvidenciaAudio;
  /// Monto en bolivianos (BOB) indicado por el técnico al iniciar atención en sitio.
  final double? presupuestoBob;
  final DateTime? presupuestoRegistradoAt;
  final int? minutosRetraso;
  final bool servicioRetrasado;
  final String? etaOrigen;

  factory SolicitudSeguimiento.fromJson(Map<String, dynamic> j) {
    return SolicitudSeguimiento(
      solicitudId: j['solicitud_id'] as int,
      estado: EstadoSolicitudEmergencia.parse(j['estado'] as String),
      updatedAt: _asDateTime(j['updated_at']),
      aiPayload: SolicitudAiPayloadV1.tryParse(j['ai_payload']),
      tiempoEstimadoMin: j['tiempo_estimado_min'] as int?,
      finalizadaAt: j['finalizada_at'] != null ? _asDateTime(j['finalizada_at']) : null,
      taller: j['taller'] != null && j['taller'] is Map<String, dynamic>
          ? TallerSeguimientoRead.fromJson(j['taller'] as Map<String, dynamic>)
          : null,
      tecnico: j['tecnico'] != null && j['tecnico'] is Map<String, dynamic>
          ? TecnicoSeguimientoRead.fromJson(j['tecnico'] as Map<String, dynamic>)
          : null,
      historialEstados: [
        for (final e in j['historial_estados'] as List<dynamic>? ?? [])
          if (e is Map<String, dynamic>) SolicitudHistorialEstadoRead.fromJson(e),
      ],
      tieneUbicacionCliente: j['tiene_ubicacion_cliente'] as bool? ?? false,
      tieneEvidenciaFoto: j['tiene_evidencia_foto'] as bool? ?? false,
      tieneEvidenciaAudio: j['tiene_evidencia_audio'] as bool? ?? false,
      presupuestoBob: _asDoubleNullable(j['presupuesto_bob']),
      presupuestoRegistradoAt: j['presupuesto_registrado_at'] != null
          ? _asDateTime(j['presupuesto_registrado_at'])
          : null,
      minutosRetraso: j['minutos_retraso'] as int?,
      servicioRetrasado: j['servicio_retrasado'] as bool? ?? false,
      etaOrigen: j['eta_origen'] as String?,
    );
  }
}
