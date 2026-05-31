import 'package:flutter/foundation.dart';
import '../../../core/utils/api_datetime.dart';

DateTime _asDateTime(Object? v) {
  return parseApiDateTime(v);
}

@immutable
final class MensajeSolicitudRead {
  const MensajeSolicitudRead({
    required this.id,
    required this.solicitudId,
    required this.emisorUsuarioId,
    required this.receptorUsuarioId,
    required this.mensaje,
    required this.createdAt,
    this.leidoAt,
  });

  final int id;
  final int solicitudId;
  final int emisorUsuarioId;
  final int receptorUsuarioId;
  final String mensaje;
  final DateTime createdAt;
  final DateTime? leidoAt;

  factory MensajeSolicitudRead.fromJson(Map<String, dynamic> j) {
    return MensajeSolicitudRead(
      id: j['id'] as int,
      solicitudId: j['solicitud_id'] as int,
      emisorUsuarioId: j['emisor_usuario_id'] as int,
      receptorUsuarioId: j['receptor_usuario_id'] as int,
      mensaje: j['mensaje'] as String,
      createdAt: _asDateTime(j['created_at']),
      leidoAt: j['leido_at'] != null ? _asDateTime(j['leido_at']) : null,
    );
  }
}
