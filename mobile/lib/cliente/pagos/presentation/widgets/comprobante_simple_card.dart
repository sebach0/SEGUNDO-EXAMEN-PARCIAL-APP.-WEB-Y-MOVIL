import 'package:flutter/material.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../../../core/utils/bolivia_time.dart';
import '../../domain/pago_models.dart';

class ComprobanteSimpleCard extends StatelessWidget {
  const ComprobanteSimpleCard({super.key, required this.pago});

  final PagoRead pago;

  String _fmt(DateTime? d) => d == null ? '—' : BoliviaTime.formatWithZone(d);

  @override
  Widget build(BuildContext context) {
    final theme = ShadTheme.of(context);
    final cs = theme.colorScheme;

    return Container(
      decoration: BoxDecoration(
        color: cs.card,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: cs.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Encabezado ──────────────────────────────────────────────────
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: cs.muted.withValues(alpha: 0.5),
              borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
            ),
            child: Row(children: [
              Icon(Icons.receipt_long_rounded, size: 18, color: cs.mutedForeground),
              const SizedBox(width: 8),
              Text('Comprobante de pago', style: theme.textTheme.p.copyWith(fontWeight: FontWeight.w700)),
            ]),
          ),

          // ── Monto destacado ─────────────────────────────────────────────
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Monto pagado', style: theme.textTheme.muted),
                Text(
                  '${pago.monto.toStringAsFixed(2)} ${pago.moneda}',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: const Color(0xFF15803D)),
                ),
              ],
            ),
          ),

          Divider(height: 1, color: cs.border),

          // ── Detalles ────────────────────────────────────────────────────
          _Row(label: 'Solicitud', value: '#${pago.solicitudId}'),
          _Row(label: 'Método', value: pago.metodo.etiquetaUi),
          _Row(label: 'Proveedor', value: pago.proveedor),
          if (pago.referenciaExterna != null)
            _Row(label: 'Referencia', value: pago.referenciaExterna!, mono: true),
          _Row(label: 'Registrado', value: _fmt(pago.createdAt)),
          if (pago.pagadoAt != null) _Row(label: 'Confirmado', value: _fmt(pago.pagadoAt)),

          const SizedBox(height: 8),
        ],
      ),
    );
  }
}

class _Row extends StatelessWidget {
  const _Row({required this.label, required this.value, this.mono = false});

  final String label;
  final String value;
  final bool mono;

  @override
  Widget build(BuildContext context) {
    final theme = ShadTheme.of(context);
    final cs = theme.colorScheme;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(width: 90, child: Text(label, style: theme.textTheme.muted)),
          Expanded(
            child: Text(
              value,
              style: mono
                  ? TextStyle(fontFamily: 'monospace', fontSize: 13, color: cs.foreground)
                  : theme.textTheme.p.copyWith(fontWeight: FontWeight.w500),
            ),
          ),
        ],
      ),
    );
  }
}
