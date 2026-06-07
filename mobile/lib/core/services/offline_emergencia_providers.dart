import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../cliente/emergencias/application/emergencias_providers.dart';
import '../../cliente/application/cliente_injection.dart';
import 'offline_emergencia_queue.dart';

final offlineEmergenciaQueueProvider = Provider<OfflineEmergenciaQueue>((ref) {
  return OfflineEmergenciaQueue(
    ref.watch(dioProvider),
    ref.watch(emergenciasRepositoryProvider),
  );
});

/// Borradores pendientes de sincronizar (wizard completado offline o parcial online).
final offlineEmergenciaPendingProvider =
    FutureProvider<List<OfflineEmergenciaDraft>>((ref) async {
  return ref.watch(offlineEmergenciaQueueProvider).listPending();
});

final offlineEmergenciaPendingCountProvider = Provider<int>((ref) {
  return ref.watch(offlineEmergenciaPendingProvider).maybeWhen(
        data: (list) => list.length,
        orElse: () => 0,
      );
});

/// Dispara sincronización manual y refresca listas.
final offlineEmergenciaSyncProvider = Provider<Future<OfflineSyncResult> Function()>((ref) {
  return () async {
    final result = await ref.read(offlineEmergenciaQueueProvider).syncPending();
    ref.invalidate(offlineEmergenciaPendingProvider);
    ref.invalidate(misSolicitudesEmergenciasProvider);
    return result;
  };
});
