/// Parsea timestamps del backend asumiendo UTC cuando vienen sin zona.
///
/// El backend serializa `timestamp without time zone` (naive), p. ej.:
/// `2026-04-26T01:38:11.529980`
/// Eso en Dart se interpreta como hora local si no se corrige.
DateTime parseApiDateTime(Object? value) {
  if (value is! String) {
    throw FormatException('No es fecha: $value');
  }
  final raw = value.trim();
  final hasZone = raw.endsWith('Z') || raw.contains(RegExp(r'[+-]\d{2}:\d{2}$'));
  return DateTime.parse(hasZone ? raw : '${raw}Z');
}
