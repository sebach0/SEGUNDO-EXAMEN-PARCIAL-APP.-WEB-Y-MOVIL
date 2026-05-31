import 'package:flutter/material.dart';

import '../../../../../core/utils/bolivia_time.dart';
import '../../../domain/solicitud_seguimiento_models.dart';
import 'estado_solicitud_badge.dart';

/// Línea de tiempo del historial de estados.
class SeguimientoTimeline extends StatelessWidget {
  const SeguimientoTimeline({super.key, required this.items});

  final List<SolicitudHistorialEstadoRead> items;

  /// Quita códigos de caso de uso antiguos guardados en BD, p. ej. "(CU11)".
  static String _limpiarObservacion(String s) {
    return s.replaceAll(RegExp(r'\s*\(CU\d+\)'), '');
  }

  String _fmt(DateTime d) {
    return BoliviaTime.formatWithZone(d);
  }

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) {
      return Text(
        'Sin movimientos de estado registrados.',
        style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant),
      );
    }
    final scheme = Theme.of(context).colorScheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (var i = 0; i < items.length; i++) ...[
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SizedBox(
                width: 22,
                child: Column(
                  children: [
                    Container(
                      width: 12,
                      height: 12,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: scheme.primary,
                        border: Border.all(color: scheme.surface, width: 2),
                      ),
                    ),
                    if (i < items.length - 1)
                      Container(
                        width: 2,
                        height: 44,
                        color: scheme.outlineVariant,
                      ),
                  ],
                ),
              ),
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.only(left: 4, bottom: 8),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Flexible(child: EstadoSolicitudBadge(estado: items[i].estadoNuevo, compact: true)),
                          const SizedBox(width: 8),
                          Text(
                            _fmt(items[i].createdAt),
                            style: Theme.of(context).textTheme.labelSmall?.copyWith(
                                  color: scheme.onSurfaceVariant,
                                ),
                          ),
                        ],
                      ),
                      if (items[i].estadoAnterior != null) ...[
                        const SizedBox(height: 4),
                        Text(
                          'Desde: ${items[i].estadoAnterior!.etiquetaUi}',
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: scheme.onSurfaceVariant,
                              ),
                        ),
                      ],
                      if (items[i].observacion != null && items[i].observacion!.trim().isNotEmpty) ...[
                        const SizedBox(height: 4),
                        Text(
                          _limpiarObservacion(items[i].observacion!),
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                    ],
                  ),
                ),
              ),
            ],
          ),
        ],
      ],
    );
  }
}
