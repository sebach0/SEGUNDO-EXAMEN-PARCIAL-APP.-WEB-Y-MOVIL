import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../../../core/utils/bolivia_time.dart';
import '../../application/emergencias_providers.dart';
import '../../domain/solicitud_emergencia_models.dart';
import '../widgets/seguimiento/estado_solicitud_badge.dart';

/// Lista de solicitudes del cliente — entrada CU16–CU18 vía detalle / seguimiento.
class EmergenciasMisSolicitudesScreen extends ConsumerWidget {
  const EmergenciasMisSolicitudesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(misSolicitudesEmergenciasProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Mis solicitudes'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.canPop() ? context.pop() : context.go('/cliente/app/home'),
        ),
      ),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => _ErrorBody(
          message: e.toString(),
          onRetry: () => ref.invalidate(misSolicitudesEmergenciasProvider),
        ),
        data: (list) {
          if (list.isEmpty) {
            return _EmptyBody(
              onNueva: () => context.push('/cliente/app/emergencias'),
            );
          }
          return RefreshIndicator(
            onRefresh: () async => ref.invalidate(misSolicitudesEmergenciasProvider),
            child: ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: list.length,
              separatorBuilder: (_, __) => const SizedBox(height: 10),
              itemBuilder: (context, i) {
                final s = list[i];
                return _SolicitudTile(solicitud: s);
              },
            ),
          );
        },
      ),
    );
  }
}

class _SolicitudTile extends StatelessWidget {
  const _SolicitudTile({required this.solicitud});

  final SolicitudEmergenciaListItem solicitud;

  String _fecha(DateTime d) {
    return BoliviaTime.format(d, pattern: 'dd/MM/yyyy');
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Material(
      color: scheme.surfaceContainerHighest.withValues(alpha: 0.45),
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () => context.push('/cliente/app/emergencias/solicitudes/${solicitud.id}'),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(Icons.emergency_outlined, color: scheme.primary, size: 28),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Solicitud #${solicitud.id}',
                      style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
                    ),
                    const SizedBox(height: 6),
                    EstadoSolicitudBadge(estado: solicitud.estado, compact: true),
                    const SizedBox(height: 8),
                    Text(
                      'Vehículo #${solicitud.vehiculoId} · ${_fecha(solicitud.createdAt)}',
                      style: TextStyle(fontSize: 12, color: scheme.onSurfaceVariant),
                    ),
                    if (solicitud.tiempoEstimadoMin != null) ...[
                      const SizedBox(height: 4),
                      Text(
                        'ETA: ${solicitud.tiempoEstimadoMin} min',
                        style: TextStyle(fontSize: 12, color: scheme.primary, fontWeight: FontWeight.w600),
                      ),
                    ],
                  ],
                ),
              ),
              Icon(Icons.chevron_right, color: scheme.onSurfaceVariant),
            ],
          ),
        ),
      ),
    );
  }
}

class _EmptyBody extends StatelessWidget {
  const _EmptyBody({required this.onNueva});

  final VoidCallback onNueva;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: ShadCard(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.inbox_outlined, size: 48, color: scheme.onSurfaceVariant),
                const SizedBox(height: 16),
                Text(
                  'No tenés solicitudes aún',
                  style: Theme.of(context).textTheme.titleMedium,
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 8),
                Text(
                  'Cuando reportes una emergencia, aparecerá acá para seguimiento.',
                  style: TextStyle(color: scheme.onSurfaceVariant, height: 1.4),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 20),
                ShadButton(onPressed: onNueva, child: const Text('Reportar emergencia')),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _ErrorBody extends StatelessWidget {
  const _ErrorBody({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(message, textAlign: TextAlign.center, style: TextStyle(color: Theme.of(context).colorScheme.error)),
            const SizedBox(height: 16),
            ShadButton.outline(onPressed: onRetry, child: const Text('Reintentar')),
          ],
        ),
      ),
    );
  }
}
