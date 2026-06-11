import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../cliente/comunicacion/domain/mensaje_solicitud_models.dart';
import '../../application/tecnico_injection.dart';
import '../data/tecnico_emergencias_repository.dart';
import '../domain/tecnico_servicio_models.dart';

final tecnicoEmergenciasRepositoryProvider = Provider<TecnicoEmergenciasRepository>((ref) {
  return TecnicoEmergenciasRepository(ref.watch(tecnicoDioProvider));
});

/// CU32 — solo servicios asignados al técnico autenticado.
final tecnicoServiciosAsignadosProvider =
    FutureProvider.autoDispose<List<ServicioAsignadoTecnico>>((ref) async {
  return ref.watch(tecnicoEmergenciasRepositoryProvider).listarServiciosAsignados();
});

/// Historial de servicios finalizados/cancelados del técnico.
final tecnicoHistorialProvider =
    FutureProvider.autoDispose<List<ServicioAsignadoTecnico>>((ref) async {
  return ref.watch(tecnicoEmergenciasRepositoryProvider).listarHistorial();
});

/// CU33
final tecnicoUbicacionClienteProvider =
    FutureProvider.autoDispose.family<UbicacionClienteActual, int>((ref, solicitudId) async {
  return ref.watch(tecnicoEmergenciasRepositoryProvider).obtenerUbicacionCliente(solicitudId);
});

/// CU35
final tecnicoMensajesSolicitudProvider =
    FutureProvider.autoDispose.family<List<MensajeSolicitudRead>, int>((ref, solicitudId) async {
  return ref.watch(tecnicoEmergenciasRepositoryProvider).listarMensajes(solicitudId);
});

/// Comprobante y cobro del servicio (técnico).
final tecnicoComprobanteSolicitudProvider =
    FutureProvider.autoDispose.family<ComprobanteTecnico, int>((ref, solicitudId) async {
  return ref.watch(tecnicoEmergenciasRepositoryProvider).obtenerComprobante(solicitudId);
});
