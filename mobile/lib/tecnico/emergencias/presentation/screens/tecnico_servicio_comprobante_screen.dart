import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/utils/bolivia_time.dart';
import '../../../../../cliente/emergencias/domain/solicitud_emergencia_models.dart'
    show EstadoSolicitudEmergencia;
import '../../application/tecnico_emergencias_providers.dart';
import '../../domain/tecnico_servicio_models.dart';

/// Comprobante del servicio: costo, cotización, finalización y cobro al cliente.
class TecnicoServicioComprobanteScreen extends ConsumerStatefulWidget {
  const TecnicoServicioComprobanteScreen({super.key, required this.solicitudId});

  final int solicitudId;

  @override
  ConsumerState<TecnicoServicioComprobanteScreen> createState() =>
      _TecnicoServicioComprobanteScreenState();
}

class _TecnicoServicioComprobanteScreenState
    extends ConsumerState<TecnicoServicioComprobanteScreen> {
  bool _finalizando = false;
  bool _cobrando = false;
  String? _accionError;

  Future<void> _finalizar(ComprobanteTecnico comprobante) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Finalizar servicio'),
        content: const Text(
          '¿Confirmás que el servicio fue completado? '
          'El estado pasará a Finalizado.',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Finalizar')),
        ],
      ),
    );
    if (ok != true || !mounted) return;

    setState(() {
      _finalizando = true;
      _accionError = null;
    });
    try {
      final repo = ref.read(tecnicoEmergenciasRepositoryProvider);
      await repo.actualizarEstado(
        solicitudId: widget.solicitudId,
        nuevoEstado: EstadoSolicitudEmergencia.finalizada,
      );
      ref.invalidate(tecnicoServiciosAsignadosProvider);
      ref.invalidate(tecnicoComprobanteSolicitudProvider(widget.solicitudId));
    } catch (e) {
      if (mounted) {
        setState(() => _accionError = e.toString().replaceFirst('Exception: ', ''));
      }
    } finally {
      if (mounted) setState(() => _finalizando = false);
    }
  }

  Future<void> _cobrar(ComprobanteTecnico comprobante, String metodo) async {
    final montoStr = comprobante.montoACobrar!.toStringAsFixed(2);
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Confirmar cobro'),
        content: Text(
          '¿Registrar cobro de Bs. $montoStr en $metodo?\n\n'
          'Esto marcará el pago como completado.',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Confirmar')),
        ],
      ),
    );
    if (ok != true || !mounted) return;

    setState(() {
      _cobrando = true;
      _accionError = null;
    });
    try {
      final repo = ref.read(tecnicoEmergenciasRepositoryProvider);
      await repo.registrarCobro(widget.solicitudId, metodo: metodo);
      ref.invalidate(tecnicoComprobanteSolicitudProvider(widget.solicitudId));
    } catch (e) {
      if (mounted) {
        setState(() => _accionError = e.toString().replaceFirst('Exception: ', ''));
      }
    } finally {
      if (mounted) setState(() => _cobrando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final async = ref.watch(tecnicoComprobanteSolicitudProvider(widget.solicitudId));

    return Scaffold(
      appBar: AppBar(
        title: Text('Comprobante #${widget.solicitudId}'),
        leading: BackButton(onPressed: () => context.pop()),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            tooltip: 'Actualizar',
            onPressed: () =>
                ref.invalidate(tecnicoComprobanteSolicitudProvider(widget.solicitudId)),
          ),
        ],
      ),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => _ErrorView(
          message: e.toString().replaceFirst('Exception: ', ''),
          onRetry: () =>
              ref.invalidate(tecnicoComprobanteSolicitudProvider(widget.solicitudId)),
        ),
        data: (c) => _ComprobanteBody(
          comprobante: c,
          finalizando: _finalizando,
          cobrando: _cobrando,
          accionError: _accionError,
          onFinalizar: () => _finalizar(c),
          onCobrar: (metodo) => _cobrar(c, metodo),
          onEditarCotizacion: c.puedeEditarCotizacion
              ? () => context.push(
                    '/tecnico/app/servicios/${widget.solicitudId}/cotizacion/editar',
                    extra: c,
                  )
              : null,
        ),
      ),
    );
  }
}

// ── Cuerpo principal ─────────────────────────────────────────────────────────

class _ComprobanteBody extends StatelessWidget {
  const _ComprobanteBody({
    required this.comprobante,
    required this.finalizando,
    required this.cobrando,
    required this.accionError,
    required this.onFinalizar,
    required this.onCobrar,
    this.onEditarCotizacion,
  });

  final ComprobanteTecnico comprobante;
  final bool finalizando;
  final bool cobrando;
  final String? accionError;
  final VoidCallback onFinalizar;
  final void Function(String metodo) onCobrar;
  final VoidCallback? onEditarCotizacion;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme; // usado en card de pago + acciones
    final tt = Theme.of(context).textTheme;
    final c = comprobante;

    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
      children: [
        // ── Cliente y vehículo ───────────────────────────────────────────────
        _SectionCard(
          icon: Icons.person_outline_rounded,
          title: 'Cliente',
          children: [
            _InfoRow(label: 'Nombre', value: c.clienteNombre),
            _InfoRow(label: 'Vehículo', value: c.vehiculoDescripcion),
            _InfoRow(label: 'Estado', value: c.estado.etiquetaUi),
            if (c.finalizadaAt != null)
              _InfoRow(
                label: 'Finalizado',
                value: BoliviaTime.formatWithZone(c.finalizadaAt!),
              ),
          ],
        ),

        const SizedBox(height: 14),

        // ── Costo del servicio ───────────────────────────────────────────────
        _SectionCard(
          icon: Icons.receipt_long_rounded,
          title: 'Detalle del costo',
          children: [
            if (c.cotizacionId != null) ...[
              if (c.cotizacionDescripcionDanio != null)
                Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: Text(
                    c.cotizacionDescripcionDanio!,
                    style: tt.bodyMedium?.copyWith(height: 1.4),
                  ),
                ),
              if (c.cotizacionItems.isNotEmpty) ...[
                const Divider(height: 1),
                const SizedBox(height: 10),
                for (final item in c.cotizacionItems)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                item.descripcion,
                                style: tt.bodySmall?.copyWith(
                                    height: 1.35, fontWeight: FontWeight.w500),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                '${item.cantidad % 1 == 0 ? item.cantidad.toInt() : item.cantidad.toStringAsFixed(1)} uds × Bs. ${item.precioUnitario.toStringAsFixed(2)}',
                                style: tt.labelSmall
                                    ?.copyWith(color: scheme.onSurfaceVariant),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 12),
                        Text(
                          'Bs. ${item.subtotal.toStringAsFixed(2)}',
                          style: tt.bodySmall
                              ?.copyWith(fontWeight: FontWeight.w600),
                        ),
                      ],
                    ),
                  ),
                const Divider(height: 12),
              ],
            ] else if (c.presupuestoBob != null) ...[
              _InfoRow(
                label: 'Presupuesto registrado',
                value: 'Bs. ${c.presupuestoBob!.toStringAsFixed(2)}',
              ),
            ] else ...[
              Text(
                'Sin costo definido aún.',
                style: tt.bodyMedium?.copyWith(color: scheme.onSurfaceVariant),
              ),
            ],

            // Editar ítems (solo EN_ATENCION, con cotización, sin pago)
            if (onEditarCotizacion != null) ...[
              const SizedBox(height: 10),
              OutlinedButton.icon(
                onPressed: onEditarCotizacion,
                icon: const Icon(Icons.edit_note_rounded, size: 20),
                label: const Text('Editar ítems de cotización'),
                style: OutlinedButton.styleFrom(
                  minimumSize: const Size.fromHeight(42),
                ),
              ),
            ],

            // Total
            if (c.montoACobrar != null || c.cotizacionItems.isNotEmpty) ...[
              Container(
                margin: const EdgeInsets.only(top: 8),
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                decoration: BoxDecoration(
                  color: scheme.primaryContainer,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      c.montoACobrar != null ? 'TOTAL A COBRAR' : 'TOTAL ESTIMADO',
                      style: tt.titleSmall?.copyWith(
                          color: scheme.onPrimaryContainer,
                          fontWeight: FontWeight.w800),
                    ),
                    Text(
                      'Bs. ${(c.montoACobrar ?? c.cotizacionItems.fold(0.0, (s, i) => s + i.subtotal)).toStringAsFixed(2)}',
                      style: tt.titleMedium?.copyWith(
                          color: scheme.primary, fontWeight: FontWeight.w900),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),

        const SizedBox(height: 14),

        // ── Estado de pago ───────────────────────────────────────────────────
        if (c.pagoRealizado) ...[
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: scheme.primaryContainer,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                Icon(Icons.check_circle_rounded, color: scheme.primary, size: 28),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Pago registrado',
                        style: tt.titleSmall?.copyWith(
                            color: scheme.onPrimaryContainer,
                            fontWeight: FontWeight.w700),
                      ),
                      if (c.pagoMonto != null)
                        Text(
                          'Bs. ${c.pagoMonto!.toStringAsFixed(2)} · ${c.pagoMetodo ?? ''}',
                          style: tt.bodySmall?.copyWith(
                              color: scheme.onPrimaryContainer),
                        ),
                      if (c.pagadoAt != null)
                        Text(
                          BoliviaTime.formatWithZone(c.pagadoAt!),
                          style: tt.bodySmall?.copyWith(
                              color: scheme.onPrimaryContainer.withOpacity(0.75)),
                        ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),
        ],

        // ── Error de acción ──────────────────────────────────────────────────
        if (accionError != null) ...[
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: scheme.errorContainer,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.error_outline_rounded, color: scheme.error, size: 20),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(accionError!,
                      style: tt.bodyMedium?.copyWith(
                          color: scheme.onErrorContainer, height: 1.35)),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
        ],

        // ── Acciones ─────────────────────────────────────────────────────────
        if (c.puedeFinalizarse) ...[
          FilledButton.icon(
            onPressed: finalizando ? null : onFinalizar,
            icon: finalizando
                ? SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(
                        strokeWidth: 2, color: scheme.onPrimary),
                  )
                : const Icon(Icons.check_circle_outline_rounded, size: 22),
            label: Padding(
              padding: const EdgeInsets.symmetric(vertical: 14),
              child: Text(
                finalizando ? 'Finalizando…' : 'Finalizar servicio',
                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
              ),
            ),
          ),
          const SizedBox(height: 12),
        ],

        if (c.puedeCobrar) ...[
          _CobrarButton(
            monto: c.montoACobrar!,
            cobrando: cobrando,
            onCobrar: onCobrar,
          ),
        ],
      ],
    );
  }
}

// ── Botón de cobro con selector de método ────────────────────────────────────

class _CobrarButton extends StatefulWidget {
  const _CobrarButton({
    required this.monto,
    required this.cobrando,
    required this.onCobrar,
  });

  final double monto;
  final bool cobrando;
  final void Function(String metodo) onCobrar;

  @override
  State<_CobrarButton> createState() => _CobrarButtonState();
}

class _CobrarButtonState extends State<_CobrarButton> {
  String _metodo = 'EFECTIVO';

  static const _metodos = [
    ('EFECTIVO', 'Efectivo'),
    ('QR', 'QR / Tigo Money'),
    ('TRANSFERENCIA', 'Transferencia bancaria'),
  ];

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final tt = Theme.of(context).textTheme;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text('Método de cobro',
            style: tt.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          children: _metodos.map((m) {
            final selected = _metodo == m.$1;
            return ChoiceChip(
              label: Text(m.$2),
              selected: selected,
              onSelected: widget.cobrando ? null : (_) => setState(() => _metodo = m.$1),
            );
          }).toList(),
        ),
        const SizedBox(height: 12),
        FilledButton.tonalIcon(
          onPressed: widget.cobrando ? null : () => widget.onCobrar(_metodo),
          icon: widget.cobrando
              ? SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(
                      strokeWidth: 2, color: scheme.onSecondaryContainer),
                )
              : const Icon(Icons.payments_rounded, size: 22),
          label: Padding(
            padding: const EdgeInsets.symmetric(vertical: 14),
            child: Text(
              widget.cobrando
                  ? 'Registrando cobro…'
                  : 'Cobrar Bs. ${widget.monto.toStringAsFixed(2)}',
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
            ),
          ),
        ),
      ],
    );
  }
}

// ── Widgets auxiliares ────────────────────────────────────────────────────────

class _SectionCard extends StatelessWidget {
  const _SectionCard({
    required this.icon,
    required this.title,
    required this.children,
  });

  final IconData icon;
  final String title;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final tt = Theme.of(context).textTheme;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: scheme.surfaceContainerLow,
        borderRadius: BorderRadius.circular(14),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 20, color: scheme.primary),
              const SizedBox(width: 8),
              Text(title,
                  style: tt.titleSmall?.copyWith(fontWeight: FontWeight.w700)),
            ],
          ),
          const SizedBox(height: 12),
          ...children,
        ],
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final tt = Theme.of(context).textTheme;
    final scheme = Theme.of(context).colorScheme;

    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 110,
            child: Text(label,
                style: tt.bodySmall?.copyWith(color: scheme.onSurfaceVariant)),
          ),
          Expanded(
            child: Text(value, style: tt.bodyMedium?.copyWith(fontWeight: FontWeight.w500)),
          ),
        ],
      ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  const _ErrorView({required this.message, required this.onRetry});

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
            Icon(Icons.error_outline_rounded,
                size: 48, color: Theme.of(context).colorScheme.error),
            const SizedBox(height: 12),
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            FilledButton(onPressed: onRetry, child: const Text('Reintentar')),
          ],
        ),
      ),
    );
  }
}
