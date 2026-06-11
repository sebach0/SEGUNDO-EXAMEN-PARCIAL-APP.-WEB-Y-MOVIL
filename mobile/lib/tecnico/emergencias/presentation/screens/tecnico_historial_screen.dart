import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/utils/bolivia_time.dart';
import '../../application/tecnico_emergencias_providers.dart';
import '../../domain/tecnico_servicio_models.dart';
import '../widgets/tecnico_estado_servicio_badge.dart';

/// Historial de servicios finalizados/cancelados del técnico.
class TecnicoHistorialScreen extends ConsumerWidget {
  const TecnicoHistorialScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(tecnicoHistorialProvider);
    final scheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Historial de servicios'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            tooltip: 'Actualizar',
            onPressed: () => ref.invalidate(tecnicoHistorialProvider),
          ),
        ],
      ),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => _ErrorBody(
          message: e.toString().replaceFirst('Exception: ', ''),
          onRetry: () => ref.invalidate(tecnicoHistorialProvider),
        ),
        data: (items) {
          if (items.isEmpty) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(28),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.history_rounded, size: 56, color: scheme.onSurfaceVariant),
                    const SizedBox(height: 16),
                    Text(
                      'Sin servicios finalizados aún',
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Aquí aparecerán los servicios que hayas completado o cancelado.',
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: scheme.onSurface.withValues(alpha: 0.7),
                            height: 1.4,
                          ),
                    ),
                  ],
                ),
              ),
            );
          }
          return RefreshIndicator(
            onRefresh: () => ref.refresh(tecnicoHistorialProvider.future),
            child: ListView.separated(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
              itemCount: items.length,
              separatorBuilder: (_, __) => const SizedBox(height: 10),
              itemBuilder: (context, i) => _HistorialCard(
                servicio: items[i],
                onTap: () => context.push(
                  '/tecnico/app/servicios/${items[i].solicitudId}/comprobante',
                  extra: items[i],
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

// ── Tarjeta de historial ─────────────────────────────────────────────────────

class _HistorialCard extends StatelessWidget {
  const _HistorialCard({required this.servicio, required this.onTap});

  final ServicioAsignadoTecnico servicio;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final tt = Theme.of(context).textTheme;
    final finalizado = servicio.estado == EstadoSolicitudEmergencia.finalizada;

    return Material(
      color: scheme.surfaceContainerHighest.withValues(alpha: 0.5),
      borderRadius: BorderRadius.circular(14),
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: finalizado
                      ? scheme.primaryContainer
                      : scheme.errorContainer,
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  finalizado ? Icons.check_circle_rounded : Icons.cancel_rounded,
                  size: 22,
                  color: finalizado ? scheme.primary : scheme.error,
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            servicio.clienteNombreCompleto,
                            style: tt.titleSmall?.copyWith(fontWeight: FontWeight.w700),
                          ),
                        ),
                        TecnicoEstadoServicioBadge(estado: servicio.estado, compact: true),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      servicio.vehiculoLinea,
                      style: tt.bodySmall?.copyWith(color: scheme.onSurfaceVariant),
                    ),
                    const SizedBox(height: 6),
                    Row(
                      children: [
                        Icon(Icons.calendar_today_rounded, size: 14, color: scheme.onSurfaceVariant),
                        const SizedBox(width: 4),
                        Text(
                          BoliviaTime.formatWithZone(servicio.updatedAt, pattern: 'dd/MM/yyyy HH:mm'),
                          style: tt.labelSmall?.copyWith(color: scheme.onSurfaceVariant),
                        ),
                        if (servicio.presupuestoBob != null) ...[
                          const SizedBox(width: 14),
                          Icon(Icons.attach_money_rounded, size: 14, color: scheme.primary),
                          Text(
                            'Bs. ${servicio.presupuestoBob!.toStringAsFixed(2)}',
                            style: tt.labelSmall?.copyWith(
                              color: scheme.primary,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ],
                      ],
                    ),
                    if (servicio.categoriaUi != null) ...[
                      const SizedBox(height: 4),
                      Text(
                        servicio.categoriaUi!,
                        style: tt.labelSmall?.copyWith(color: scheme.onSurfaceVariant),
                      ),
                    ],
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Icon(Icons.chevron_right_rounded, color: scheme.onSurfaceVariant),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Error ─────────────────────────────────────────────────────────────────────

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
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            FilledButton(onPressed: onRetry, child: const Text('Reintentar')),
          ],
        ),
      ),
    );
  }
}
