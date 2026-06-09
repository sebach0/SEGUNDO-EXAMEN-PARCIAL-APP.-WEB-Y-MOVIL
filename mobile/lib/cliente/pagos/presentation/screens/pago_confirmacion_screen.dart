import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_stripe/flutter_stripe.dart';
import 'package:go_router/go_router.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../../application/cliente_injection.dart';
import '../../application/pagos_providers.dart';
import '../../../emergencias/application/emergencias_providers.dart';
import '../../domain/pago_models.dart';

class PagoConfirmacionScreen extends ConsumerStatefulWidget {
  const PagoConfirmacionScreen({super.key, required this.solicitudId, required this.draft});

  final int solicitudId;
  final PagoDraft draft;

  @override
  ConsumerState<PagoConfirmacionScreen> createState() => _PagoConfirmacionScreenState();
}

class _PagoConfirmacionScreenState extends ConsumerState<PagoConfirmacionScreen> {
  bool _busy = false;
  static const double _montoEpsilon = 0.02;

  double? _montoDraft() => double.tryParse(widget.draft.montoTexto.replaceAll(',', '.'));

  PagoRead? _coherentPagoIniciado(MetodoPago metodo, double monto) {
    final p = widget.draft.pagoIniciado;
    if (p == null) return null;
    if (p.solicitudId != widget.solicitudId) return null;
    if (p.metodo != metodo) return null;
    if ((p.monto - monto).abs() > _montoEpsilon) return null;
    return p;
  }

  Future<void> _irAResultado(PagoRead pago) async {
    ref.invalidate(pagosSolicitudProvider(widget.solicitudId));
    ref.invalidate(emergenciaDetailProvider(widget.solicitudId));
    if (!mounted) return;
    context.pushReplacement(
      '/cliente/app/emergencias/solicitudes/${widget.solicitudId}/pago/resultado',
      extra: pago,
    );
  }

  Future<void> _confirmar() async {
    final m = widget.draft.metodo;
    if (m == null) return;
    final v = _montoDraft();
    if (v == null || v <= 0) return;

    setState(() => _busy = true);
    try {
      final repo = ref.read(pagosRepositoryProvider);
      PagoRead pago = _coherentPagoIniciado(m, v) ??
          await repo.iniciarPago(solicitudId: widget.solicitudId, monto: v, metodo: m);

      if (pago.estado == EstadoPago.pagado) {
        await _irAResultado(pago);
        return;
      }

      if (pago.requiereStripePaymentSheet(m)) {
        final pk = pago.stripePublishableKey?.trim();
        final cs = pago.stripeClientSecret?.trim();
        if (pk == null || pk.isEmpty || cs == null || cs.isEmpty) {
          throw Exception('La respuesta de Stripe no incluye claves necesarias.');
        }
        final pi = pago.stripePaymentIntentId?.trim();
        if (pi == null || pi.isEmpty) throw Exception('Falta el identificador del intento de pago.');

        Stripe.publishableKey = pk;
        await Stripe.instance.applySettings();
        await Stripe.instance.initPaymentSheet(
          paymentSheetParameters: SetupPaymentSheetParameters(
            paymentIntentClientSecret: cs,
            merchantDisplayName: 'Emergencias Viales',
          ),
        );
        try {
          await Stripe.instance.presentPaymentSheet();
        } on StripeException catch (e) {
          if (!mounted) return;
          final msg = e.error.localizedMessage ?? e.error.message ?? e.toString();
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Cobro no completado: $msg')));
          return;
        }
        final confirmado = await repo.confirmarStripe(
          solicitudId: widget.solicitudId,
          pagoId: pago.id,
          paymentIntentId: pi,
        );
        await _irAResultado(confirmado);
        return;
      }

      await _irAResultado(pago);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString().replaceFirst('Exception: ', ''))),
      );
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  IconData _methodIcon(MetodoPago? m) => switch (m) {
        MetodoPago.qr => Icons.qr_code_2_rounded,
        MetodoPago.tarjeta => Icons.credit_card_rounded,
        MetodoPago.transferencia => Icons.swap_horiz_rounded,
        MetodoPago.efectivo => Icons.payments_rounded,
        _ => Icons.more_horiz_rounded,
      };

  @override
  Widget build(BuildContext context) {
    final theme = ShadTheme.of(context);
    final cs = theme.colorScheme;
    final m = widget.draft.metodo;

    return Scaffold(
      backgroundColor: cs.background,
      appBar: AppBar(
        title: const Text('Confirmar pago'),
        leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => context.pop()),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
        children: [
          // ── Resumen del pedido ────────────────────────────────────────────
          Container(
            decoration: BoxDecoration(
              color: cs.card,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: cs.border),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
                  child: Text('Resumen del pago', style: theme.textTheme.large.copyWith(fontWeight: FontWeight.w700)),
                ),
                const Divider(height: 1),
                _SummaryRow(
                  icon: Icons.receipt_long_rounded,
                  label: 'Solicitud',
                  value: '#${widget.solicitudId}',
                ),
                _SummaryRow(
                  icon: _methodIcon(m),
                  label: 'Método',
                  value: m?.etiquetaUi ?? '—',
                ),
                const Divider(height: 1),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                  child: Row(children: [
                    const Icon(Icons.attach_money_rounded, size: 20),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text('Total', style: theme.textTheme.p.copyWith(fontWeight: FontWeight.w600)),
                    ),
                    Text(
                      'Bs. ${widget.draft.montoTexto}',
                      style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: cs.primary),
                    ),
                  ]),
                ),
              ],
            ),
          ),

          const SizedBox(height: 16),

          // ── Nota según método ──────────────────────────────────────────────
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: cs.muted.withValues(alpha: 0.5),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Icon(Icons.info_outline_rounded, size: 18, color: cs.mutedForeground),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  m == MetodoPago.tarjeta
                      ? 'Se abrirá la pasarela segura de Stripe para completar el cobro con tarjeta.'
                      : m == MetodoPago.qr
                          ? 'Tras confirmar, se registrará el cobro. El pago QR se coordina con el taller.'
                          : m == MetodoPago.transferencia || m == MetodoPago.efectivo
                              ? 'El taller o administrador verificará el pago manualmente y lo confirmará.'
                              : 'El pago se registrará con el método seleccionado.',
                  style: theme.textTheme.muted,
                ),
              ),
            ]),
          ),

          const SizedBox(height: 28),

          ShadButton(
            onPressed: _busy || m == null ? null : _confirmar,
            child: _busy
                ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                : Row(mainAxisSize: MainAxisSize.min, children: [
                    Icon(_methodIcon(m), size: 18),
                    const SizedBox(width: 8),
                    const Text('Confirmar y pagar'),
                  ]),
          ),

          const SizedBox(height: 10),
          ShadButton.outline(
            onPressed: _busy ? null : () => context.pop(),
            child: const Text('Cambiar método'),
          ),
        ],
      ),
    );
  }
}

class _SummaryRow extends StatelessWidget {
  const _SummaryRow({required this.icon, required this.label, required this.value});

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final theme = ShadTheme.of(context);
    final cs = theme.colorScheme;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 11),
      child: Row(children: [
        Icon(icon, size: 18, color: cs.mutedForeground),
        const SizedBox(width: 10),
        SizedBox(width: 72, child: Text(label, style: theme.textTheme.muted)),
        Expanded(child: Text(value, style: theme.textTheme.p.copyWith(fontWeight: FontWeight.w500))),
      ]),
    );
  }
}
