// Sincroniza la cola offline al iniciar, al volver al foreground y periódicamente.
import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../cliente/application/client_auth_provider.dart';
import 'offline_emergencia_providers.dart';

/// Envuelve la app y dispara sync de borradores pendientes.
class OfflineEmergenciaSyncListener extends ConsumerStatefulWidget {
  const OfflineEmergenciaSyncListener({super.key, required this.child});

  final Widget child;

  @override
  ConsumerState<OfflineEmergenciaSyncListener> createState() =>
      _OfflineEmergenciaSyncListenerState();
}

class _OfflineEmergenciaSyncListenerState
    extends ConsumerState<OfflineEmergenciaSyncListener>
    with WidgetsBindingObserver {
  Timer? _pollTimer;
  bool _syncing = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    WidgetsBinding.instance.addPostFrameCallback((_) => _syncPending());
    _pollTimer = Timer.periodic(const Duration(seconds: 25), (_) => _syncPending());
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _syncPending();
    }
  }

  Future<void> _syncPending() async {
    if (_syncing || !mounted) return;
    final auth = ref.read(clientAuthNotifierProvider);
    if (!auth.isAuthenticated) return;

    final pending = await ref.read(offlineEmergenciaQueueProvider).listPending();
    if (pending.isEmpty) return;

    _syncing = true;
    try {
      final result = await ref.read(offlineEmergenciaSyncProvider)();
      if (!mounted || !result.hasWork) return;
      ref.invalidate(offlineEmergenciaPendingProvider);
      final messenger = ScaffoldMessenger.maybeOf(context);
      if (result.synced > 0) {
        messenger?.showSnackBar(
          SnackBar(
            content: Text(
              result.failed > 0
                  ? '${result.synced} solicitud(es) sincronizada(s); ${result.failed} con error.'
                  : '${result.synced} solicitud(es) sincronizada(s) desde modo offline.',
            ),
          ),
        );
      } else if (result.failed > 0) {
        messenger?.showSnackBar(
          SnackBar(
            content: Text(
              result.errors.isEmpty ? 'Error al sincronizar' : result.errors.first,
            ),
          ),
        );
      }
    } catch (_) {
      // Sin red o sin sesión: reintenta en el próximo ciclo.
    } finally {
      _syncing = false;
    }
  }

  @override
  Widget build(BuildContext context) => widget.child;
}
