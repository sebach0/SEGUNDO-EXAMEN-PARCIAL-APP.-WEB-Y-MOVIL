import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../../emergencias/application/emergencias_providers.dart';
import '../../domain/pago_eligibility.dart';
import '../../domain/pago_models.dart';
import '../widgets/resumen_cobro_card.dart';

/// Paso 1 — monto a pagar + contexto de la solicitud.
class PagoResumenScreen extends ConsumerStatefulWidget {
  const PagoResumenScreen({super.key, required this.solicitudId});

  final int solicitudId;

  @override
  ConsumerState<PagoResumenScreen> createState() => _PagoResumenScreenState();
}

class _PagoResumenScreenState extends ConsumerState<PagoResumenScreen> {
  void _continuar() {
    final detalle = ref.read(emergenciaDetailProvider(widget.solicitudId)).asData?.value;
    final presupuesto = detalle?.presupuestoBob;
    final montoFijadoPorTecnico = presupuesto != null && presupuesto > 0;
    if (!montoFijadoPorTecnico) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Aún no hay monto definido por el técnico/mecánico.'),
        ),
      );
      return;
    }

    final montoT = presupuesto.toStringAsFixed(2);
    final draft = PagoDraft(solicitudId: widget.solicitudId, montoTexto: montoT);
    context.push('/cliente/app/emergencias/solicitudes/${widget.solicitudId}/pago/metodo', extra: draft);
  }

  @override
  Widget build(BuildContext context) {
    final async = ref.watch(emergenciaDetailProvider(widget.solicitudId));
    final theme = ShadTheme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Pagar servicio'),
        actions: [
          IconButton(
            tooltip: 'Actualizar monto',
            onPressed: () => ref.invalidate(emergenciaDetailProvider(widget.solicitudId)),
            icon: const Icon(Icons.refresh),
          ),
        ],
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.canPop() ? context.pop() : context.go('/cliente/app/emergencias/solicitudes/${widget.solicitudId}'),
        ),
      ),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Padding(padding: const EdgeInsets.all(24), child: Text(e.toString()))),
        data: (d) {
          final montoFijadoPorTecnico = d.presupuestoBob != null && d.presupuestoBob! > 0;
          if (!solicitudPermitePago(d.estado)) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      'En este estado la solicitud no admite pago desde la app.',
                      textAlign: TextAlign.center,
                      style: theme.textTheme.large,
                    ),
                    const SizedBox(height: 16),
                    ShadButton.outline(
                      onPressed: () => context.pop(),
                      child: const Text('Volver'),
                    ),
                  ],
                ),
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: () => ref.refresh(emergenciaDetailProvider(widget.solicitudId).future),
            child: ListView(
              padding: const EdgeInsets.all(20),
              children: [
                ResumenCobroCard(
                  solicitudId: widget.solicitudId,
                  estado: d.estado,
                ),
                const SizedBox(height: 20),
                if (montoFijadoPorTecnico) ...[
                  ShadCard(
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Text(
                        'Monto acordado por el técnico/mecánico: Bs. ${d.presupuestoBob!.toStringAsFixed(2)}.',
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Text('Monto a pagar', style: theme.textTheme.large),
                  const SizedBox(height: 8),
                  ShadCard(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Row(
                        children: [
                          Icon(Icons.lock_outline, size: 22, color: theme.colorScheme.primary),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              'Bs. ${d.presupuestoBob!.toStringAsFixed(2)} (fijado por técnico)',
                              style: theme.textTheme.p,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ] else ...[
                  ShadCard(
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Text(
                        'El técnico/mecánico aún no definió el monto. Cuando lo registre, podrás continuar con el pago.',
                        style: theme.textTheme.muted,
                      ),
                    ),
                  ),
                ],
                const SizedBox(height: 8),
                Text('Moneda por defecto: BOB (según backend).', style: theme.textTheme.muted),
                const SizedBox(height: 28),
                ShadButton(
                  onPressed: montoFijadoPorTecnico ? _continuar : null,
                  child: const Text('Continuar'),
                ),
                const SizedBox(height: 12),
                ShadButton.outline(
                  onPressed: () => context.push('/cliente/app/emergencias/solicitudes/${widget.solicitudId}/pagos'),
                  child: const Text('Ver historial de pagos'),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}
