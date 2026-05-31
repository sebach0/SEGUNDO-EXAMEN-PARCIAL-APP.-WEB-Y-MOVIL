import 'package:flutter/foundation.dart';
import '../../../core/utils/api_datetime.dart';

double _asDouble(Object? v) {
  if (v is num) return v.toDouble();
  if (v is String) return double.parse(v);
  throw FormatException('No es número: $v');
}

double? _asDoubleNullable(Object? v) {
  if (v == null) return null;
  return _asDouble(v);
}

DateTime _asDateTime(Object? v) {
  return parseApiDateTime(v);
}

/// Respuesta de `GET .../ubicacion-tecnico` (cliente) y `POST .../ubicacion-tecnico` (técnico).
@immutable
final class UbicacionTecnicoCompartida {
  const UbicacionTecnicoCompartida({
    required this.solicitudId,
    required this.latitud,
    required this.longitud,
    this.precisionMetros,
    required this.actualizadoAt,
  });

  final int solicitudId;
  final double latitud;
  final double longitud;
  final double? precisionMetros;
  final DateTime actualizadoAt;

  factory UbicacionTecnicoCompartida.fromJson(Map<String, dynamic> j) {
    return UbicacionTecnicoCompartida(
      solicitudId: j['solicitud_id'] as int,
      latitud: _asDouble(j['latitud']),
      longitud: _asDouble(j['longitud']),
      precisionMetros: j['precision_metros'] != null ? _asDoubleNullable(j['precision_metros']) : null,
      actualizadoAt: _asDateTime(j['actualizado_at']),
    );
  }
}
