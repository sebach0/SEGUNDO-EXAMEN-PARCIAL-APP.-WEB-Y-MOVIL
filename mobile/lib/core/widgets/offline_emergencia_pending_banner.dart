import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../services/offline_emergencia_providers.dart';

/// Banner compacto: solicitudes guardadas offline pendientes de sync.
class OfflineEmergenciaPendingBanner extends ConsumerWidget {
  const OfflineEmergenciaPendingBanner({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pendingAsync = ref.watch(offlineEmergenciaPendingProvider);
    return pendingAsync.when(
      loading: () => const SizedBox.shrink(),
      error: (_, __) => const SizedBox.shrink(),
      data: (pending) {
        if (pending.isEmpty) return const SizedBox.shrink();
        final scheme = Theme.of(context).colorScheme;
        return Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
          child: Material(
            color: scheme.tertiaryContainer.withValues(alpha: 0.85),
            borderRadius: BorderRadius.circular(12),
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.cloud_off_outlined, color: scheme.onTertiaryContainer),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '${pending.length} reporte(s) offline pendiente(s)',
                          style: TextStyle(
                            fontWeight: FontWeight.w700,
                            color: scheme.onTertiaryContainer,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'Se enviarán automáticamente al reconectar. '
                          'También podés forzar la sincronización ahora.',
                          style: TextStyle(
                            fontSize: 12,
                            color: scheme.onTertiaryContainer,
                            height: 1.35,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 8),
                  ShadButton.outline(
                    size: ShadButtonSize.sm,
                    onPressed: () async {
                      final sync = ref.read(offlineEmergenciaSyncProvider);
                      final messenger = ScaffoldMessenger.maybeOf(context);
                      messenger?.showSnackBar(
                        const SnackBar(content: Text('Sincronizando reportes offline…')),
                      );
                      final r = await sync();
                      if (!context.mounted) return;
                      messenger?.hideCurrentSnackBar();
                      if (r.synced > 0) {
                        messenger?.showSnackBar(
                          SnackBar(content: Text('${r.synced} reporte(s) sincronizado(s).')),
                        );
                      } else if (r.failed > 0) {
                        messenger?.showSnackBar(
                          SnackBar(
                            content: Text(r.errors.isEmpty ? 'Error al sincronizar' : r.errors.first),
                          ),
                        );
                      } else {
                        messenger?.showSnackBar(
                          const SnackBar(content: Text('Sin conexión con el servidor.')),
                        );
                      }
                    },
                    child: const Text('Sync'),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}
