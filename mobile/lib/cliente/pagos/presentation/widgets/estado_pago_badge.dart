import 'package:flutter/material.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../domain/pago_models.dart';

class EstadoPagoBadge extends StatelessWidget {
  const EstadoPagoBadge({super.key, required this.estado});

  final EstadoPago estado;

  @override
  Widget build(BuildContext context) {
    final theme = ShadTheme.of(context);
    final (label, color) = switch (estado) {
      EstadoPago.pendiente => ('Pendiente', theme.colorScheme.mutedForeground),
      EstadoPago.pagado => ('Pagado', const Color(0xFF15803D)),
      EstadoPago.fallido => ('Fallido', theme.colorScheme.destructive),
      EstadoPago.anulado => ('Anulado', theme.colorScheme.mutedForeground),
    };

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: color.withValues(alpha: 0.35)),
      ),
      child: Text(
        label,
        style: theme.textTheme.small.copyWith(
          color: color,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}
