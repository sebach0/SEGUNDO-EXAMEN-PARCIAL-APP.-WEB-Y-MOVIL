import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../application/cliente_injection.dart';
import '../domain/mensaje_solicitud_models.dart';
import '../domain/notificacion_models.dart';

/// Lista de notificaciones (CU19).
final notificacionesClienteProvider =
    FutureProvider.autoDispose.family<List<NotificacionRead>, bool>((ref, soloNoLeidas) async {
  final repo = ref.watch(comunicacionRepositoryProvider);
  return repo.listarNotificaciones(soloNoLeidas: soloNoLeidas);
});

/// Mensajes de una solicitud (CU21).
final mensajesSolicitudProvider =
    FutureProvider.autoDispose.family<List<MensajeSolicitudRead>, int>((ref, solicitudId) async {
  final repo = ref.watch(comunicacionRepositoryProvider);
  return repo.listarMensajesSolicitud(solicitudId);
});
