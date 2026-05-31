import 'package:flutter/material.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../../../../core/utils/bolivia_time.dart';

/// CU18 — tiempo estimado de llegada (minutos).
class EtaLlegadaCard extends StatelessWidget {
  const EtaLlegadaCard({super.key, required this.minutos, this.actualizadoEn});

  final int? minutos;
  final DateTime? actualizadoEn;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final tiene = minutos != null && minutos! >= 0;
    return ShadCard(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.schedule_outlined, color: scheme.primary),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Tiempo estimado de llegada',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            if (!tiene)
              Text(
                'Aún no hay ETA publicada. El taller la actualizará cuando asigne la movilización.',
                style: TextStyle(color: scheme.onSurfaceVariant, height: 1.4),
              )
            else ...[
              Text(
                '$minutos min',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800),
              ),
              if (actualizadoEn != null) ...[
                const SizedBox(height: 6),
                Text(
                  'Última actualización del servidor: ${_fmt(actualizadoEn!)}',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(color: scheme.onSurfaceVariant),
                ),
              ],
            ],
          ],
        ),
      ),
    );
  }

  String _fmt(DateTime d) {
    return BoliviaTime.formatWithZone(d);
  }
}
