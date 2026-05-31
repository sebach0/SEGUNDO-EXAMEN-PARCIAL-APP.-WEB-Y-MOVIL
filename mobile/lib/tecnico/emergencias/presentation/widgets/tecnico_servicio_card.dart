import 'package:flutter/material.dart';

import '../../../../core/utils/bolivia_time.dart';
import '../../domain/tecnico_servicio_models.dart';
import 'tecnico_estado_servicio_badge.dart';

/// Tarjeta táctil grande para lista de servicios asignados (CU32).
class TecnicoServicioCard extends StatelessWidget {
  const TecnicoServicioCard({
    super.key,
    required this.servicio,
    required this.onTap,
  });

  final ServicioAsignadoTecnico servicio;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Semantics(
      label: 'Servicio ${servicio.solicitudId}, ${servicio.estado.etiquetaUi}, ${servicio.clienteNombreCompleto}',
      button: true,
      child: Material(
        color: scheme.surfaceContainerHighest.withValues(alpha: 0.55),
        borderRadius: BorderRadius.circular(16),
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 14, 12, 14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      child: Text(
                        servicio.clienteNombreCompleto,
                        style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 17),
                      ),
                    ),
                    TecnicoEstadoServicioBadge(estado: servicio.estado, compact: true),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  servicio.vehiculoLinea,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: scheme.onSurface.withValues(alpha: 0.85),
                      ),
                ),
                if (servicio.categoriaUi != null || servicio.prioridadUi != null) ...[
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      if (servicio.categoriaUi != null) _chip(context, 'Tipo: ${servicio.categoriaUi}'),
                      if (servicio.prioridadUi != null) _chip(context, 'Prioridad: ${servicio.prioridadUi}'),
                    ],
                  ),
                ],
                if (servicio.presupuestoBob != null) ...[
                  const SizedBox(height: 8),
                  Text(
                    'Presupuesto: Bs. ${servicio.presupuestoBob!.toStringAsFixed(2)}',
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                          color: scheme.primary,
                          fontWeight: FontWeight.w700,
                        ),
                  ),
                ],
                const SizedBox(height: 6),
                Row(
                  children: [
                    Icon(Icons.schedule_rounded, size: 18, color: scheme.onSurfaceVariant),
                    const SizedBox(width: 6),
                    Text(
                      BoliviaTime.formatWithZone(servicio.updatedAt, pattern: 'dd/MM/yy HH:mm'),
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: scheme.onSurfaceVariant,
                            fontWeight: FontWeight.w500,
                          ),
                    ),
                    if (servicio.tiempoEstimadoMin != null) ...[
                      const SizedBox(width: 12),
                      Icon(Icons.timer_outlined, size: 18, color: scheme.primary),
                      const SizedBox(width: 4),
                      Text(
                        '~${servicio.tiempoEstimadoMin} min',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: scheme.primary,
                              fontWeight: FontWeight.w600,
                            ),
                      ),
                    ],
                  ],
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Text(
                      'Ver detalle',
                      style: TextStyle(
                        color: scheme.primary,
                        fontWeight: FontWeight.w600,
                        fontSize: 15,
                      ),
                    ),
                    Icon(Icons.chevron_right_rounded, color: scheme.primary),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _chip(BuildContext context, String text) {
    final scheme = Theme.of(context).colorScheme;
    return DecoratedBox(
      decoration: BoxDecoration(
        color: scheme.surfaceContainer.withValues(alpha: 0.65),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: scheme.outline.withValues(alpha: 0.25)),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        child: Text(
          text,
          style: Theme.of(context).textTheme.labelSmall?.copyWith(fontWeight: FontWeight.w600),
        ),
      ),
    );
  }
}
