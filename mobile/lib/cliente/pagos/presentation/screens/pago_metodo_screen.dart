import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../../application/cliente_injection.dart';
import '../../application/pagos_providers.dart';
import '../../domain/pago_models.dart';
import '../widgets/metodo_pago_selector.dart';

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
    final cs = theme.colorScheme;

    return Scaffold(
      backgroundColor: cs.background,
      appBar: AppBar(
        title: const Text('Método de pago'),
        leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => context.pop()),
      ),
      body: Column(
        children: [
          // ── Monto fijo en la parte superior ────────────────────────────────
          Container(
            width: double.infinity,
            margin: const EdgeInsets.fromLTRB(16, 12, 16, 0),
            padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 20),
            decoration: BoxDecoration(
              color: cs.card,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: cs.border),
            ),
            child: Row(children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(color: cs.primary.withValues(alpha: 0.1), shape: BoxShape.circle),
                child: Icon(Icons.receipt_rounded, color: cs.primary, size: 22),
              ),
              const SizedBox(width: 14),
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('Total a pagar', style: theme.textTheme.muted),
                Text(
                  'Bs. ${widget.draft.montoTexto}',
                  style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: cs.primary),
                ),
              ]),
            ]),
          ),

          const SizedBox(height: 4),

          // ── Selector de métodos (scrollable) ───────────────────────────────
          Expanded(
            child: ListView(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 100),
              children: [
                MetodoPagoSelector(
                  valor: _metodo,
                  onChanged: (m) => setState(() => _metodo = m),
                ),
              ],
            ),
          ),
        ],
      ),

      // ── Botón flotante inferior ─────────────────────────────────────────────
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
          child: ShadButton(
            onPressed: _metodo == null || _busy ? null : _revisarYConfirmar,
            child: _busy
                ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                : Row(mainAxisSize: MainAxisSize.min, children: const [
                    Icon(Icons.arrow_forward_rounded, size: 18),
                    SizedBox(width: 8),
                    Text('Revisar y confirmar'),
                  ]),
          ),
        ),
      ),
    );
  }
}
