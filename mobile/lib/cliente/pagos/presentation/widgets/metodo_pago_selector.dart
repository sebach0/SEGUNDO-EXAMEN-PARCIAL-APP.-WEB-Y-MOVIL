import 'package:flutter/material.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../domain/pago_models.dart';

/// Selector de método de pago (UI lista; la pasarela real reemplazará el flujo de captura).
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

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Método de pago', style: theme.textTheme.large),
        const SizedBox(height: 12),
        ...MetodoPago.values.map((m) {
          final sel = valor == m;
          return Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Material(
              color: Colors.transparent,
              child: InkWell(
                onTap: () => onChanged(m),
                borderRadius: BorderRadius.circular(12),
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: sel ? theme.colorScheme.primary : theme.colorScheme.border,
                      width: sel ? 2 : 1,
                    ),
                    color: sel ? theme.colorScheme.primary.withValues(alpha: 0.06) : null,
                  ),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                    child: Row(
                      children: [
                        Icon(
                          sel ? Icons.radio_button_checked : Icons.radio_button_off,
                          size: 22,
                          color: sel ? theme.colorScheme.primary : theme.colorScheme.mutedForeground,
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(m.etiquetaUi, style: theme.textTheme.p.copyWith(fontWeight: FontWeight.w600)),
                        ),
                        Text(m.apiValue, style: theme.textTheme.muted),
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
