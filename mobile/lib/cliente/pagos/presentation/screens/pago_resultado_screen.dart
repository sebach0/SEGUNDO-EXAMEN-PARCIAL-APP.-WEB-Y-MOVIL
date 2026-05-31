import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../../application/cliente_injection.dart';
import '../../application/pagos_providers.dart';
import '../../domain/pago_models.dart';
import '../widgets/comprobante_simple_card.dart';
import '../widgets/estado_pago_badge.dart';

/// Paso 4 — resultado y comprobante. Si queda `PENDIENTE`, ofrece completar (modo 2 pasos backend).
class PagoResultadoScreen extends ConsumerStatefulWidget {
  const PagoResultadoScreen({super.key, required this.solicitudId, required this.pagoInicial});

  final int solicitudId;
  final PagoRead pagoInicial;

  @override
  ConsumerState<PagoResultadoScreen> createState() => _PagoResultadoScreenState();
}

class _PagoResultadoScreenState extends ConsumerState<PagoResultadoScreen> {
  late PagoRead _pago;
  bool _completando = false;

  @override
  void initState() {
    super.initState();
    _pago = widget.pagoInicial;
  }

  Future<void> _completarSimulado() async {
    setState(() => _completando = true);
    try {
      final p = await ref.read(pagosRepositoryProvider).completarSimulado(
            solicitudId: widget.solicitudId,
            pagoId: _pago.id,
          );
      ref.invalidate(pagosSolicitudProvider(widget.solicitudId));
      if (mounted) setState(() => _pago = p);
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
    final ok = _pago.estado == EstadoPago.pagado;
    final pendiente = _pago.estado == EstadoPago.pendiente;
    final mal = _pago.estado == EstadoPago.fallido || _pago.estado == EstadoPago.anulado;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Resultado del pago'),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => context.go('/cliente/app/emergencias/solicitudes/${widget.solicitudId}'),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Icon(
            ok ? Icons.check_circle_rounded : (pendiente ? Icons.schedule_rounded : Icons.error_outline_rounded),
            size: 56,
            color: ok
                ? const Color(0xFF15803D)
                : (pendiente ? theme.colorScheme.primary : theme.colorScheme.destructive),
          ),
          const SizedBox(height: 12),
          Text(
            ok
                ? 'Pago registrado'
                : pendiente
                    ? 'Pago pendiente de confirmación'
                    : 'No se pudo completar el pago',
            style: theme.textTheme.h4,
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Center(child: EstadoPagoBadge(estado: _pago.estado)),
          const SizedBox(height: 24),
          if (ok || _pago.referenciaExterna != null) ComprobanteSimpleCard(pago: _pago),
          if (pendiente) ...[
            const SizedBox(height: 16),
            Text(
              'El servidor dejó el cobro pendiente (p. ej. pasarela en dos pasos). '
              'Podés intentar completar la simulación.',
              style: theme.textTheme.muted,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            ShadButton(
              onPressed: _completando ? null : _completarSimulado,
              child: _completando
                  ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Text('Completar pago (simulado)'),
            ),
          ],
          if (mal) ...[
            const SizedBox(height: 12),
            Text(
              'Revisá el monto y el estado de la solicitud, o contactá al taller.',
              style: theme.textTheme.muted,
              textAlign: TextAlign.center,
            ),
          ],
          const SizedBox(height: 28),
          ShadButton.outline(
            onPressed: () => context.go('/cliente/app/emergencias/solicitudes/${widget.solicitudId}/pagos'),
            child: const Text('Historial de pagos'),
          ),
          const SizedBox(height: 8),
          ShadButton.outline(
            onPressed: () => context.go('/cliente/app/emergencias/solicitudes/${widget.solicitudId}'),
            child: const Text('Volver al detalle'),
          ),
        ],
      ),
    );
  }
}
