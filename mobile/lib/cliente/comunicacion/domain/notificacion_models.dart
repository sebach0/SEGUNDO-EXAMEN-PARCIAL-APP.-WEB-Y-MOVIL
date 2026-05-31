import 'package:flutter/foundation.dart';
import '../../../core/utils/api_datetime.dart';

enum TipoNotificacion {
  solicitudCreada('SOLICITUD_CREADA'),
  estadoActualizado('ESTADO_ACTUALIZADO'),
  tallerAsignado('TALLER_ASIGNADO'),
  tecnicoAsignado('TECNICO_ASIGNADO'),
  mensajeNuevo('MENSAJE_NUEVO');

  const TipoNotificacion(this.apiValue);
  final String apiValue;

  static TipoNotificacion parse(String s) {
    return TipoNotificacion.values.firstWhere(
      (e) => e.apiValue == s,
      orElse: () => TipoNotificacion.estadoActualizado,
    );
  }
}

DateTime _asDateTime(Object? v) {
  return parseApiDateTime(v);
}

@immutable
final class NotificacionRead {
  const NotificacionRead({
    required this.id,
    required this.usuarioId,
    required this.solicitudId,
    required this.tipo,
    required this.titulo,
    required this.mensaje,
    required this.leida,
    required this.createdAt,
    this.leidaAt,
  });

  final int id;
  final int usuarioId;
  final int? solicitudId;
  final TipoNotificacion tipo;
  final String titulo;
  final String mensaje;
  final bool leida;
  final DateTime createdAt;
  final DateTime? leidaAt;

  factory NotificacionRead.fromJson(Map<String, dynamic> j) {
    return NotificacionRead(
      id: j['id'] as int,
      usuarioId: j['usuario_id'] as int,
      solicitudId: j['solicitud_id'] as int?,
      tipo: TipoNotificacion.parse(j['tipo'] as String),
      titulo: j['titulo'] as String,
      mensaje: j['mensaje'] as String,
      leida: j['leida'] as bool,
      createdAt: _asDateTime(j['created_at']),
      leidaAt: j['leida_at'] != null ? _asDateTime(j['leida_at']) : null,
    );
  }
}
