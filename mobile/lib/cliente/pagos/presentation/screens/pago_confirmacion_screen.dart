import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_stripe/flutter_stripe.dart';
import 'package:go_router/go_router.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../../application/cliente_injection.dart';
import '../../application/pagos_providers.dart';
import '../../../emergencias/application/emergencias_providers.dart';
import '../../domain/pago_models.dart';

/// Paso 3 — confirmación: simulación local o **Stripe PaymentSheet** si el backend devuelve `client_secret`.
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

  double? _montoDraft() {
    return double.tryParse(widget.draft.montoTexto.replaceAll(',', '.'));
  }

  /// Reusa el `POST /pagos` del paso método si coincide solicitud, método y monto (evita filas duplicadas y PI inconsistente).
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
          await repo.iniciarPago(
            solicitudId: widget.solicitudId,
            monto: v,
            metodo: m,
          );

      if (pago.estado == EstadoPago.pagado) {
        await _irAResultado(pago);
        return;
      }

      if (pago.requiereStripePaymentSheet(m)) {
        final pk = pago.stripePublishableKey?.trim();
        final cs = pago.stripeClientSecret?.trim();
        if (pk == null || pk.isEmpty || cs == null || cs.isEmpty) {
          throw Exception('La respuesta de Stripe no incluye claves necesarias para el cobro.');
        }
        final pi = pago.stripePaymentIntentId?.trim();
        if (pi == null || pi.isEmpty) {
          throw Exception(
            'Falta el identificador del intento de pago (payment_intent). '
            'Volvé atrás y elegí de nuevo el método con tarjeta, o reintentá en unos segundos.',
          );
        }
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
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Cobro no completado: $msg')),
          );
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

  @override
  Widget build(BuildContext context) {
    final theme = ShadTheme.of(context);
    final m = widget.draft.metodo;
    final detalle = ref.watch(emergenciaDetailProvider(widget.solicitudId));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Confirmar pago'),
        leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => context.pop()),
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          ShadCard(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Resumen', style: theme.textTheme.large),
                  const SizedBox(height: 12),
                  Text('Solicitud #${widget.solicitudId}', style: theme.textTheme.p),
                  Text('Monto: ${widget.draft.montoTexto} BOB', style: theme.textTheme.p),
                  Text('Método: ${m?.etiquetaUi ?? '—'}', style: theme.textTheme.p),
                  detalle.when(
                    loading: () => const SizedBox.shrink(),
                    error: (_, __) => const SizedBox.shrink(),
                    data: (d) => Text('Estado solicitud: ${d.estado.etiquetaUi}', style: theme.textTheme.muted),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Text(
            m == MetodoPago.tarjeta
                ? 'Si el servidor tiene Stripe configurado, se abrirá la hoja de pago. '
                    'Con otros métodos se confirma sin pasarela de tarjeta.'
                : 'Este método se confirma en el flujo de la app (sin hoja de tarjeta de Stripe).',
            style: theme.textTheme.muted,
          ),
          const SizedBox(height: 24),
          ShadButton(
            onPressed: _busy || m == null ? null : _confirmar,
            child: _busy
                ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2))
                : const Text('Confirmar pago'),
          ),
        ],
      ),
    );
  }
}
