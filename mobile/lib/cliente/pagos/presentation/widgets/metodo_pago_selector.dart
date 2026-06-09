import 'package:flutter/material.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../domain/pago_models.dart';

IconData _iconForMetodo(MetodoPago m) => switch (m) {
      MetodoPago.qr => Icons.qr_code_2_rounded,
      MetodoPago.tarjeta => Icons.credit_card_rounded,
      MetodoPago.transferencia => Icons.swap_horiz_rounded,
      MetodoPago.efectivo => Icons.payments_rounded,
      MetodoPago.otro => Icons.more_horiz_rounded,
    };

String _descForMetodo(MetodoPago m) => switch (m) {
      MetodoPago.qr => 'Escaneá el QR con tu billetera digital',
      MetodoPago.tarjeta => 'Débito o crédito — procesado por Stripe',
      MetodoPago.transferencia => 'Transferencia bancaria — confirmación manual',
      MetodoPago.efectivo => 'Pagás en efectivo al técnico o en el taller',
      MetodoPago.otro => 'Coordinar con el taller',
    };

class MetodoPagoSelector extends StatelessWidget {
  const MetodoPagoSelector({
    super.key,
    required this.valor,
    required this.onChanged,
  });

  final MetodoPago? valor;
  final ValueChanged<MetodoPago> onChanged;

  @override
  Widget build(BuildContext context) {
    final theme = ShadTheme.of(context);
    final cs = theme.colorScheme;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Elegí cómo pagar', style: theme.textTheme.large.copyWith(fontWeight: FontWeight.w700)),
        const SizedBox(height: 12),
        ...MetodoPago.values.map((m) {
          final sel = valor == m;
          return Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 150),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(14),
                border: Border.all(
                  color: sel ? cs.primary : cs.border,
                  width: sel ? 2 : 1,
                ),
                color: sel ? cs.primary.withValues(alpha: 0.07) : cs.card,
                boxShadow: sel
                    ? [BoxShadow(color: cs.primary.withValues(alpha: 0.12), blurRadius: 8, offset: const Offset(0, 2))]
                    : [],
              ),
              child: Material(
                color: Colors.transparent,
                borderRadius: BorderRadius.circular(14),
                child: InkWell(
                  onTap: () => onChanged(m),
                  borderRadius: BorderRadius.circular(14),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                    child: Row(
                      children: [
                        Container(
                          width: 44,
                          height: 44,
                          decoration: BoxDecoration(
                            color: sel ? cs.primary : cs.muted,
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Icon(
                            _iconForMetodo(m),
                            size: 24,
                            color: sel ? cs.primaryForeground : cs.mutedForeground,
                          ),
                        ),
                        const SizedBox(width: 14),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(m.etiquetaUi,
                                  style: theme.textTheme.p.copyWith(
                                    fontWeight: FontWeight.w600,
                                    color: sel ? cs.primary : cs.foreground,
                                  )),
                              const SizedBox(height: 2),
                              Text(_descForMetodo(m),
                                  style: theme.textTheme.muted.copyWith(fontSize: 12)),
                            ],
                          ),
                        ),
                        Icon(
                          sel ? Icons.radio_button_checked : Icons.radio_button_off,
                          size: 20,
                          color: sel ? cs.primary : cs.mutedForeground,
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          );
        }),
      ],
    );
  }
}
