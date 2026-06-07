import 'package:flutter/material.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../../../../core/utils/bolivia_time.dart';
import '../../../../../core/utils/eta_format.dart';

/// CU18 — tiempo estimado de llegada (minutos) y aviso de retraso.
class EtaLlegadaCard extends StatelessWidget {
  const EtaLlegadaCard({
    super.key,
    required this.minutos,
    this.actualizadoEn,
    this.minutosRetraso,
    this.servicioRetrasado = false,
    this.etaOrigen,
  });

  final int? minutos;
  final DateTime? actualizadoEn;
  final int? minutosRetraso;
  final bool servicioRetrasado;
  final String? etaOrigen;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final tiene = minutos != null && minutos! >= 0;
    final retraso = servicioRetrasado || (minutosRetraso != null && minutosRetraso! >= 5);

    return ShadCard(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(
                  retraso ? Icons.warning_amber_rounded : Icons.schedule_outlined,
                  color: retraso ? scheme.error : scheme.primary,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    retraso ? 'Auxilio con demora' : 'Tiempo estimado de llegada',
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
                formatEtaMinutos(minutos),
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800),
              ),
              if (retraso) ...[
                const SizedBox(height: 8),
                Text(
                  'El técnico lleva aproximadamente ${minutosRetraso ?? 'varios'} min de retraso '
                  'respecto al tiempo estimado. Te avisaremos cuando se acerque.',
                  style: TextStyle(color: scheme.error, height: 1.35),
                ),
              ],
              if (actualizadoEn != null) ...[
                const SizedBox(height: 6),
                Text(
                  'Última actualización: ${_fmt(actualizadoEn!)}'
                  '${etaOrigen != null ? ' · origen: $etaOrigen' : ''}',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(color: scheme.onSurfaceVariant),
                ),
              ],
            ],
          ],
        ),
      ),
    );
  }

  String _fmt(DateTime d) => BoliviaTime.formatWithZone(d);
}
