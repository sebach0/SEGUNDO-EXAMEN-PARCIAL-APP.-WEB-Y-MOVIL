/// Formatea minutos de ETA para lectura humana.
/// - Menos de 60 min → "45 min"
/// - 60 min o más → "1 hora", "1 hora 15 min", "2 horas 5 min", etc.
String formatEtaMinutos(int? minutos, {bool approximate = false}) {
  if (minutos == null || minutos < 0) return '—';

  final prefix = approximate ? '~' : '';

  if (minutos >= 60) {
    final horas = minutos ~/ 60;
    final mins = minutos % 60;
    final horaLabel = horas == 1 ? '1 hora' : '$horas horas';
    if (mins == 0) return '$prefix$horaLabel';
    return '$prefix$horaLabel $mins min';
  }

  return '$prefix$minutos min';
}
