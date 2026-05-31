import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../../application/cliente_injection.dart';
import '../../application/pagos_providers.dart';
import '../../domain/pago_models.dart';
import '../widgets/metodo_pago_selector.dart';

/// Paso 2 — método de pago. Inicia el pago en el servidor y pasa [PagoDraft.pagoIniciado] a confirmación.
class PagoMetodoScreen extends ConsumerStatefulWidget {
  const PagoMetodoScreen({super.key, required this.solicitudId, required this.draft});

  final int solicitudId;
  final PagoDraft draft;

  @override
  ConsumerState<PagoMetodoScreen> createState() => _PagoMetodoScreenState();
}

class _PagoMetodoScreenState extends ConsumerState<PagoMetodoScreen> {
  MetodoPago? _metodo;
  bool _busy = false;

  Future<void> _revisarYConfirmar() async {
    final m = _metodo;
    if (m == null) return;
    final v = double.tryParse(widget.draft.montoTexto.replaceAll(',', '.'));
    if (v == null || v <= 0) return;

    setState(() => _busy = true);
    try {
      final pago = await ref.read(pagosRepositoryProvider).iniciarPago(
            solicitudId: widget.solicitudId,
            monto: v,
            metodo: m,
          );
      ref.invalidate(pagosSolicitudProvider(widget.solicitudId));
      if (!mounted) return;
      final next = widget.draft.copyWith(metodo: m, pagoIniciado: pago);
      context.push(
        '/cliente/app/emergencias/solicitudes/${widget.solicitudId}/pago/confirmar',
        extra: next,
      );
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

    return Scaffold(
      appBar: AppBar(
        title: const Text('Método de pago'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.pop(),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Text('Monto: ${widget.draft.montoTexto} BOB', style: theme.textTheme.large),
          const SizedBox(height: 20),
          MetodoPagoSelector(
            valor: _metodo,
            onChanged: (m) => setState(() => _metodo = m),
          ),
          const SizedBox(height: 28),
          ShadButton(
            onPressed: _metodo == null || _busy ? null : _revisarYConfirmar,
            child: _busy
                ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2))
                : const Text('Revisar y confirmar'),
          ),
        ],
      ),
    );
  }
}
