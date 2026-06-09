import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../../emergencias/application/emergencias_providers.dart';
import '../../domain/pago_eligibility.dart';
import '../../domain/pago_models.dart';

class PagoResumenScreen extends ConsumerWidget {
  const PagoResumenScreen({super.key, required this.solicitudId});

  final int solicitudId;

  void _continuar(BuildContext context, WidgetRef ref, double presupuesto) {
    final draft = PagoDraft(solicitudId: solicitudId, montoTexto: presupuesto.toStringAsFixed(2));
    context.push('/cliente/app/emergencias/solicitudes/$solicitudId/pago/metodo', extra: draft);
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(emergenciaDetailProvider(solicitudId));
    final theme = ShadTheme.of(context);
    final cs = theme.colorScheme;

    return Scaffold(
      backgroundColor: cs.background,
      appBar: AppBar(
        title: const Text('Resumen del pago'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.canPop() ? context.pop() : context.go('/cliente/app/emergencias/solicitudes/$solicitudId'),
        ),
        actions: [
          IconButton(
            tooltip: 'Actualizar',
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.invalidate(emergenciaDetailProvider(solicitudId)),
          ),
        ],
      ),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              Icon(Icons.error_outline_rounded, size: 48, color: cs.destructive),
              const SizedBox(height: 12),
              Text(e.toString(), textAlign: TextAlign.center),
              const SizedBox(height: 16),
              ShadButton.outline(onPressed: () => ref.invalidate(emergenciaDetailProvider(solicitudId)), child: const Text('Reintentar')),
            ]),
          ),
        ),
        data: (d) {
          if (!solicitudPermitePago(d.estado)) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(32),
                child: Column(mainAxisSize: MainAxisSize.min, children: [
                  Icon(Icons.block_rounded, size: 52, color: cs.mutedForeground),
                  const SizedBox(height: 16),
                  Text('Esta solicitud no admite pago en este momento.', textAlign: TextAlign.center, style: theme.textTheme.large),
                  const SizedBox(height: 20),
                  ShadButton.outline(onPressed: () => context.pop(), child: const Text('Volver')),
                ]),
              ),
            );
          }

          final presupuesto = d.presupuestoBob;
          final tieneMonto = presupuesto != null && presupuesto > 0;

          return RefreshIndicator(
            onRefresh: () => ref.refresh(emergenciaDetailProvider(solicitudId).future),
            child: ListView(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
              children: [
                // ── Hero: monto ───────────────────────────────────────────────
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(vertical: 36, horizontal: 24),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [cs.primary, cs.primary.withValues(alpha: 0.75)],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Column(children: [
                    Text('Total a pagar', style: theme.textTheme.muted.copyWith(color: cs.primaryForeground.withValues(alpha: 0.8))),
                    const SizedBox(height: 8),
                    tieneMonto
                        ? Text(
                            'Bs. ${presupuesto!.toStringAsFixed(2)}',
                            style: TextStyle(fontSize: 40, fontWeight: FontWeight.w800, color: cs.primaryForeground),
                          )
                        : Text('— pendiente —', style: TextStyle(fontSize: 28, fontWeight: FontWeight.w600, color: cs.primaryForeground.withValues(alpha: 0.7))),
                    const SizedBox(height: 4),
                    Text('Bolivianos (BOB)', style: TextStyle(fontSize: 13, color: cs.primaryForeground.withValues(alpha: 0.7))),
                  ]),
                ),

                const SizedBox(height: 20),

                // ── Detalle de la solicitud ────────────────────────────────────
                Container(
                  decoration: BoxDecoration(
                    color: cs.card,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: cs.border),
                  ),
                  child: Column(children: [
                    _InfoRow(icon: Icons.receipt_long_rounded, label: 'Solicitud', value: '#$solicitudId'),
                    Divider(height: 1, color: cs.border),
                    _InfoRow(icon: Icons.car_repair_rounded, label: 'Estado', value: d.estado.etiquetaUi),
                    Divider(height: 1, color: cs.border),
                    _InfoRow(
                      icon: tieneMonto ? Icons.lock_rounded : Icons.schedule_rounded,
                      label: 'Monto',
                      value: tieneMonto ? 'Bs. ${presupuesto!.toStringAsFixed(2)} (fijado por técnico)' : 'Pendiente de asignación',
                      valueColor: tieneMonto ? null : cs.mutedForeground,
                    ),
                  ]),
                ),

                const SizedBox(height: 16),

                if (!tieneMonto)
                  Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: Colors.amber.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: Colors.amber.withValues(alpha: 0.4)),
                    ),
                    child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      const Icon(Icons.info_outline_rounded, color: Colors.amber, size: 20),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          'El técnico aún no definió el monto. Cuando lo registre, el botón "Continuar" se habilitará.',
                          style: theme.textTheme.muted,
                        ),
                      ),
                    ]),
                  ),

                const SizedBox(height: 28),

                ShadButton(
                  onPressed: tieneMonto ? () => _continuar(context, ref, presupuesto!) : null,
                  child: Row(mainAxisSize: MainAxisSize.min, children: const [
                    Icon(Icons.arrow_forward_rounded, size: 18),
                    SizedBox(width: 8),
                    Text('Continuar al pago'),
                  ]),
                ),
                const SizedBox(height: 10),
                ShadButton.outline(
                  onPressed: () => context.push('/cliente/app/emergencias/solicitudes/$solicitudId/pagos'),
                  child: const Text('Historial de pagos'),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({required this.icon, required this.label, required this.value, this.valueColor});

  final IconData icon;
  final String label;
  final String value;
  final Color? valueColor;

  @override
  Widget build(BuildContext context) {
    final theme = ShadTheme.of(context);
    final cs = theme.colorScheme;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(children: [
        Icon(icon, size: 18, color: cs.mutedForeground),
        const SizedBox(width: 10),
        SizedBox(width: 80, child: Text(label, style: theme.textTheme.muted)),
        Expanded(child: Text(value, style: theme.textTheme.p.copyWith(fontWeight: FontWeight.w600, color: valueColor))),
      ]),
    );
  }
}
