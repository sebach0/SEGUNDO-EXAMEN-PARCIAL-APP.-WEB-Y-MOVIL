// Providers Riverpod — cotizaciones (cliente).
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../application/cliente_injection.dart';
import '../data/cotizacion_repository.dart';
import '../domain/cotizacion_models.dart';

final cotizacionRepositoryProvider = Provider<CotizacionRepository>((ref) {
  return CotizacionRepository(ref.watch(dioProvider));
});

/// Lista de cotizaciones para una solicitud. Se puede invalidar para refrescar.
final cotizacionesBySolicitudProvider =
    FutureProvider.autoDispose.family<List<Cotizacion>, int>((ref, solicitudId) async {
  return ref.watch(cotizacionRepositoryProvider).listBySolicitud(solicitudId);
});

// ── Notifier para selección de cotización ─────────────────────────────────────

class SeleccionarCotizacionNotifier extends AsyncNotifier<Cotizacion?> {
  @override
  Future<Cotizacion?> build() async => null;

  Future<void> seleccionar({
    required int solicitudId,
    required int cotizacionId,
  }) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(
      () => ref
          .read(cotizacionRepositoryProvider)
          .seleccionar(solicitudId, cotizacionId),
    );
  }
}

final seleccionarCotizacionProvider =
    AsyncNotifierProvider<SeleccionarCotizacionNotifier, Cotizacion?>(
  SeleccionarCotizacionNotifier.new,
);
