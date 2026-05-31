import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../application/pagos_providers.dart';
import '../widgets/comprobante_simple_card.dart';
import '../widgets/estado_pago_badge.dart';

/// Lista de pagos asociados a una solicitud.
class SolicitudPagosHistorialScreen extends ConsumerWidget {
  const SolicitudPagosHistorialScreen({super.key, required this.solicitudId});

  final int solicitudId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(pagosSolicitudProvider(solicitudId));
    final theme = ShadTheme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text('Pagos · solicitud #$solicitudId'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.canPop() ? context.pop() : context.go('/cliente/app/emergencias/solicitudes/$solicitudId'),
        ),
      ),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(e.toString()),
                const SizedBox(height: 16),
                ShadButton.outline(
                  onPressed: () => ref.invalidate(pagosSolicitudProvider(solicitudId)),
                  child: const Text('Reintentar'),
                ),
              ],
            ),
          ),
        ),
        data: (list) {
          if (list.isEmpty) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(32),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.receipt_long_outlined, size: 52, color: theme.colorScheme.mutedForeground),
                    const SizedBox(height: 16),
                    Text('Sin pagos registrados', style: theme.textTheme.large),
                    const SizedBox(height: 8),
                    Text(
                      'Cuando realices un pago, aparecerá acá.',
                      textAlign: TextAlign.center,
                      style: theme.textTheme.muted,
                    ),
                    const SizedBox(height: 20),
                    ShadButton(
                      onPressed: () => context.push('/cliente/app/emergencias/solicitudes/$solicitudId/pago/resumen'),
                      child: const Text('Iniciar pago'),
                    ),
                  ],
                ),
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: () => ref.refresh(pagosSolicitudProvider(solicitudId).future),
            child: ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: list.length,
              separatorBuilder: (_, __) => const SizedBox(height: 12),
              itemBuilder: (context, i) {
                final p = list[i];
                return ShadCard(
                  child: InkWell(
                    onTap: () {
                      showModalBottomSheet<void>(
                        context: context,
                        showDragHandle: true,
                        builder: (ctx) => Padding(
                          padding: const EdgeInsets.all(16),
                          child: SingleChildScrollView(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.stretch,
                              children: [
                                Row(
                                  children: [
                                    Text('Pago #${p.id}', style: theme.textTheme.large),
                                    const Spacer(),
                                    EstadoPagoBadge(estado: p.estado),
                                  ],
                                ),
                                const SizedBox(height: 16),
                                ComprobanteSimpleCard(pago: p),
                                const SizedBox(height: 12),
                                ShadButton.outline(
                                  onPressed: () => Navigator.of(ctx).pop(),
                                  child: const Text('Cerrar'),
                                ),
                              ],
                            ),
                          ),
                        ),
                      );
                    },
                    borderRadius: BorderRadius.circular(12),
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Text('${p.monto.toStringAsFixed(2)} ${p.moneda}', style: theme.textTheme.large),
                              const Spacer(),
                              EstadoPagoBadge(estado: p.estado),
                            ],
                          ),
                          const SizedBox(height: 6),
                          Text(p.metodo.etiquetaUi, style: theme.textTheme.muted),
                          if (p.referenciaExterna != null)
                            Text('Ref: ${p.referenciaExterna}', style: theme.textTheme.small),
                        ],
                      ),
                    ),
                  ),
                );
              },
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.push('/cliente/app/emergencias/solicitudes/$solicitudId/pago/resumen'),
        icon: const Icon(Icons.payment_rounded),
        label: const Text('Nuevo pago'),
      ),
    );
  }
}
