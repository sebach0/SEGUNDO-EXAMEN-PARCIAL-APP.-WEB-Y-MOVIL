// Obtención de GPS con límite de tiempo y respaldo (evita cuelgues en emulador/dispositivo).
import 'dart:async';

import 'package:geolocator/geolocator.dart';

/// Intenta la posición actual con [timeLimit]; si falla o expira, usa la última conocida.
Future<Position> obtainDevicePosition({
  Duration timeLimit = const Duration(seconds: 12),
  LocationAccuracy accuracy = LocationAccuracy.medium,
}) async {
  try {
    return await Geolocator.getCurrentPosition(
      locationSettings: LocationSettings(
        accuracy: accuracy,
        timeLimit: timeLimit,
      ),
    );
  } on TimeoutException {
    final last = await Geolocator.getLastKnownPosition();
    if (last != null) return last;
    throw Exception(
      'No se pudo obtener la ubicación a tiempo. '
      'En el emulador, configurá una ubicación simulada (Extended Controls → Location).',
    );
  } catch (e) {
    final last = await Geolocator.getLastKnownPosition();
    if (last != null) return last;
    rethrow;
  }
}
