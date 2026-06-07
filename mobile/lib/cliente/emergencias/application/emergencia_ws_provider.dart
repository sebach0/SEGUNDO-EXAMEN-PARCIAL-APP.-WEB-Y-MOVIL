// Provider Riverpod para el seguimiento WS de una solicitud.
//
// Uso en la pantalla:
//   ref.listen(emergenciaWsProvider(solicitudId), (_, event) {
//     if (event != null) ref.invalidate(emergenciaSeguimientoProvider(solicitudId));
//   });

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/emergencia_ws_service.dart';

/// Provider que emite el último [WsSolicitudEvent] recibido para la solicitud.
/// autoDispose: desconecta el WS cuando la pantalla se cierra.
final emergenciaWsProvider = StreamProvider.autoDispose
    .family<WsSolicitudEvent, int>((ref, solicitudId) {
  final service = EmergenciaWsService(solicitudId: solicitudId);
  service.connect();

  ref.onDispose(service.dispose);

  return service.events;
});
