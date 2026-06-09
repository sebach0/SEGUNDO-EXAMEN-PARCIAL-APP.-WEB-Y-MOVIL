import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../../application/cliente_injection.dart';
import '../../application/pagos_providers.dart';
import '../../domain/pago_models.dart';
import '../widgets/comprobante_simple_card.dart';

class PagoResultadoScreen extends ConsumerStatefulWidget {
  const PagoResultadoScreen({super.key, required this.solicitudId, required this.pagoInicial});

  final int solicitudId;
  final PagoRead pagoInicial;

  @override
  ConsumerState<PagoResultadoScreen> createState() => _PagoResultadoScreenState();
}

class _PagoResultadoScreenState extends ConsumerState<PagoResultadoScreen> with SingleTickerProviderStateMixin {
  late PagoRead _pago;
  bool _completando = false;
  late final AnimationController _aniCtrl;
  late final Animation<double> _scaleAni;

  @override
  void initState() {
    super.initState();
    _pago = widget.pagoInicial;
    _aniCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 500));
    _scaleAni = CurvedAnimation(parent: _aniCtrl, curve: Curves.elasticOut);
    _aniCtrl.forward();
  }

  @override
  void dispose() {
    _aniCtrl.dispose();
    super.dispose();
  }

  Future<void> _completarSimulado() async {
    setState(() => _completando = true);
    try {
      final p = await ref.read(pagosRepositoryProvider).completarSimulado(
            solicitudId: widget.solicitudId,
            pagoId: _pago.id,
          );
      ref.invalidate(pagosSolicitudProvider(widget.solicitudId));
      if (mounted) {
        setState(() => _pago = p);
        _aniCtrl.forward(from: 0);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString().replaceFirst('Exception: ', ''))),
        );
      }
    } finally {
      if (mounted) setState(() => _completando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = ShadTheme.of(context);
    final cs = theme.colorScheme;

    final ok = _pago.estado == EstadoPago.pagado;
    final pendiente = _pago.estado == EstadoPago.pendiente;
    final mal = _pago.estado == EstadoPago.fallido || _pago.estado == EstadoPago.anulado;

    final Color heroColor = ok
        ? const Color(0xFF15803D)
        : pendiente
            ? Colors.amber.shade700
            : cs.destructive;

    final IconData heroIcon = ok
        ? Icons.check_circle_rounded
        : pendiente
            ? Icons.schedule_rounded
            : Icons.cancel_rounded;

    final String heroTitle = ok
        ? '¡Pago exitoso!'
        : pendiente
            ? 'Pago pendiente'
            : 'Pago no completado';

    final String heroSub = ok
        ? 'Tu pago fue registrado correctamente.'
        : pendiente
            ? 'El pago está en proceso de confirmación.'
            : 'No se pudo completar el cobro.';

    return Scaffold(
      backgroundColor: cs.background,
      appBar: AppBar(
        title: const Text('Resultado del pago'),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => context.go('/cliente/app/emergencias/solicitudes/${widget.solicitudId}'),
        ),
        automaticallyImplyLeading: false,
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
        children: [
          // ── Hero resultado ─────────────────────────────────────────────────
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(vertical: 36, horizontal: 24),
            decoration: BoxDecoration(
              color: heroColor.withValues(alpha: 0.07),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: heroColor.withValues(alpha: 0.25), width: 1.5),
            ),
            child: Column(children: [
              ScaleTransition(
                scale: _scaleAni,
                child: Icon(heroIcon, size: 72, color: heroColor),
              ),
              const SizedBox(height: 14),
              Text(heroTitle, style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: heroColor)),
              const SizedBox(height: 6),
              Text(heroSub, style: theme.textTheme.muted, textAlign: TextAlign.center),
              const SizedBox(height: 12),
              Text(
                'Bs. ${_pago.monto.toStringAsFixed(2)}',
                style: TextStyle(fontSize: 32, fontWeight: FontWeight.w900, color: heroColor),
              ),
            ]),
          ),

          const SizedBox(height: 20),

          // ── Comprobante ────────────────────────────────────────────────────
          if (ok || _pago.referenciaExterna != null) ComprobanteSimpleCard(pago: _pago),

          // ── Pendiente: acción de completar ────────────────────────────────
          if (pendiente) ...[
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: Colors.amber.withValues(alpha: 0.08),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.amber.withValues(alpha: 0.3)),
              ),
              child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Icon(Icons.info_outline_rounded, color: Colors.amber, size: 18),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    'Si elegiste transferencia o efectivo, el taller confirmará tu pago manualmente.',
                    style: theme.textTheme.muted,
                  ),
                ),
              ]),
            ),
            const SizedBox(height: 12),
            ShadButton.outline(
              onPressed: _completando ? null : _completarSimulado,
              child: _completando
                  ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Text('Completar pago (simulado)'),
            ),
          ],

          // ── Fallido: mensaje ───────────────────────────────────────────────
          if (mal) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: cs.destructive.withValues(alpha: 0.07),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                'Revisá el monto y el estado de la solicitud. Si el problema persiste, contactá al taller.',
                style: theme.textTheme.muted,
                textAlign: TextAlign.center,
              ),
            ),
          ],

          const SizedBox(height: 28),

          if (ok)
            ShadButton(
              onPressed: () => context.go('/cliente/app/emergencias/solicitudes/${widget.solicitudId}'),
              child: Row(mainAxisSize: MainAxisSize.min, children: const [
                Icon(Icons.home_rounded, size: 18),
                SizedBox(width: 8),
                Text('Volver al detalle'),
              ]),
            )
          else
            ShadButton(
              onPressed: () => context.go('/cliente/app/emergencias/solicitudes/${widget.solicitudId}/pago/resumen'),
              child: const Text('Reintentar pago'),
            ),

          const SizedBox(height: 10),
          ShadButton.outline(
            onPressed: () => context.go('/cliente/app/emergencias/solicitudes/${widget.solicitudId}/pagos'),
            leading: const Icon(Icons.history_rounded, size: 18),
            child: const Text('Historial de pagos'),
          ),
        ],
      ),
    );
  }
}
