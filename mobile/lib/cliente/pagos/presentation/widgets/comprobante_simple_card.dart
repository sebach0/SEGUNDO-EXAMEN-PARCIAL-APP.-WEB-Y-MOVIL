import 'package:flutter/material.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../../../core/utils/bolivia_time.dart';
import '../../domain/pago_models.dart';

/// Comprobante mínimo (referencia, monto, fechas). Listo para ampliar con PDF/QR de pasarela.
class ComprobanteSimpleCard extends StatelessWidget {
  const ComprobanteSimpleCard({super.key, required this.pago});

  final PagoRead pago;

  String _fmtFecha(DateTime? d) {
    if (d == null) return '—';
    return BoliviaTime.formatWithZone(d);
  }

  @override
  Widget build(BuildContext context) {
    final theme = ShadTheme.of(context);
    final montoStr = '${pago.monto.toStringAsFixed(2)} ${pago.moneda}';

    return ShadCard(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Comprobante', style: theme.textTheme.large),
            const SizedBox(height: 12),
            _Row(label: 'Solicitud', value: '#${pago.solicitudId}'),
            _Row(label: 'Monto', value: montoStr),
            _Row(label: 'Método', value: pago.metodo.etiquetaUi),
            _Row(label: 'Proveedor', value: pago.proveedor),
            _Row(label: 'Referencia', value: pago.referenciaExterna ?? '—'),
            _Row(label: 'Registrado', value: _fmtFecha(pago.createdAt)),
            if (pago.pagadoAt != null) _Row(label: 'Pagado', value: _fmtFecha(pago.pagadoAt)),
          ],
        ),
      ),
    );
  }
}

class _Row extends StatelessWidget {
  const _Row({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final theme = ShadTheme.of(context);
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 100,
            child: Text(label, style: theme.textTheme.muted),
          ),
          Expanded(child: Text(value, style: theme.textTheme.p)),
        ],
      ),
    );
  }
}
