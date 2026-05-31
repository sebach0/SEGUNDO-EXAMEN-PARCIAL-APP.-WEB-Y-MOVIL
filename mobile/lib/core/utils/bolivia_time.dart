import 'package:intl/intl.dart';

/// Utilidad de hora Bolivia (Santa Cruz) con offset fijo UTC-04:00.
final class BoliviaTime {
  static const Duration _offset = Duration(hours: -4);

  static DateTime asSantaCruz(DateTime value) {
    final utc = value.isUtc ? value : value.toUtc();
    return utc.add(_offset);
  }

  static String format(DateTime value, {String pattern = 'dd/MM/yyyy HH:mm'}) {
    final dt = asSantaCruz(value);
    return DateFormat(pattern, 'es_BO').format(dt);
  }

  static String formatWithZone(DateTime value, {String pattern = 'dd/MM/yyyy HH:mm'}) {
    return '${format(value, pattern: pattern)} BOT';
  }
}
