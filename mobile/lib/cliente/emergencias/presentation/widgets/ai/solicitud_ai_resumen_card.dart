import 'package:flutter/material.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../../domain/solicitud_ai_payload.dart';

/// Tarjeta informativa del análisis asistido (IA) guardado en la solicitud.
///
/// [tieneUbicacionServidor] / [tieneFotoServidor] / [tieneAudioServidor] reflejan
/// lo que realmente hay en la API (evidencias y ubicaciones). El `ai_payload` solo
/// captura el estado al **crear** la solicitud, por eso la ficha puede mostrar
/// "no" aunque el cliente haya subido archivos después.
class SolicitudAiResumenCard extends StatelessWidget {
  const SolicitudAiResumenCard({
    super.key,
    required this.payload,
    this.tieneUbicacionServidor,
    this.tieneFotoServidor,
    this.tieneAudioServidor,
  });

  final SolicitudAiPayloadV1? payload;
  final bool? tieneUbicacionServidor;
  final bool? tieneFotoServidor;
  final bool? tieneAudioServidor;

  @override
  Widget build(BuildContext context) {
    final raw = payload;
    if (raw == null || !raw.tieneContenidoUtil) {
      return ShadCard(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(Icons.psychology_outlined, color: Theme.of(context).colorScheme.onSurfaceVariant),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  'El análisis asistido no está disponible todavía (sin datos de IA o el servicio estaba apagado).',
                  style: TextStyle(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                    height: 1.4,
                  ),
                ),
              ),
            ],
          ),
        ),
      );
    }

    final p = raw;
    final scheme = Theme.of(context).colorScheme;
    return ShadCard(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Icon(Icons.auto_awesome, size: 22, color: scheme.primary),
                const SizedBox(width: 8),
                Text(
                  'Análisis asistido (IA)',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
                ),
              ],
            ),
            if (p.clasificacion != null) ...[
              const SizedBox(height: 12),
              _kv(
                context,
                'Categoría',
                '${etiquetaCategoriaIa(p.clasificacion!.categoria)} '
                '(${(p.clasificacion!.confianza * 100).toStringAsFixed(0)}%)',
              ),
              if (p.clasificacion!.damages.isNotEmpty) ...[
                const SizedBox(height: 8),
                Text('Daños IA', style: Theme.of(context).textTheme.labelLarge),
                const SizedBox(height: 4),
                ...p.clasificacion!.damages.map(
                  (d) => Padding(
                    padding: const EdgeInsets.only(bottom: 6),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '· ${d.lineaPrincipal}',
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: scheme.onSurfaceVariant,
                                height: 1.35,
                                fontWeight: FontWeight.w600,
                              ),
                        ),
                        if (d.reasons.isNotEmpty) ...[
                          const SizedBox(height: 2),
                          ...d.reasons.map(
                            (r) => Text(
                              '  · $r',
                              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                    color: scheme.onSurfaceVariant,
                                    height: 1.3,
                                  ),
                            ),
                          ),
                        ],
                        if (d.conflictHasConflict) ...[
                          const SizedBox(height: 2),
                          Text(
                            d.conflictDetails.isNotEmpty
                                ? '  Conflicto: ${d.conflictDetails.join(" · ")}'
                                : '  Posible conflicto entre evidencias.',
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                  color: scheme.tertiary,
                                  height: 1.3,
                                ),
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
              ],
              if (p.clasificacion!.requiresManualReview) ...[
                const SizedBox(height: 4),
                Text(
                  'La IA recomienda revisión manual.',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: scheme.tertiary,
                        fontWeight: FontWeight.w600,
                      ),
                ),
              ],
              if (p.clasificacion!.conflictNotes.isNotEmpty) ...[
                const SizedBox(height: 4),
                Text(
                  p.clasificacion!.conflictNotes.join(' · '),
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: scheme.onSurfaceVariant,
                        height: 1.35,
                      ),
                ),
              ],
            ],
            if (p.prioridad != null) ...[
              const SizedBox(height: 8),
              _kv(
                context,
                'Prioridad sugerida',
                etiquetaPrioridadIa(p.prioridad!.nivelPrioridad),
              ),
              if (p.prioridad!.motivo.isNotEmpty) ...[
                const SizedBox(height: 4),
                Text(
                  p.prioridad!.motivo.join(' · '),
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: scheme.onSurfaceVariant,
                        height: 1.35,
                      ),
                ),
              ],
              if (p.prioridad!.score != null) ...[
                const SizedBox(height: 4),
                Text(
                  'Score: ${p.prioridad!.score!.toStringAsFixed(2)}',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: scheme.onSurfaceVariant,
                        height: 1.35,
                      ),
                ),
              ],
              if (p.prioridad!.damagesConsiderados.isNotEmpty) ...[
                const SizedBox(height: 4),
                Text(
                  'Daños considerados: ${p.prioridad!.damagesConsiderados.join(", ")}',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: scheme.onSurfaceVariant,
                        height: 1.35,
                      ),
                ),
              ],
            ],
            if (p.resumenEstructurado != null) ...[
              const SizedBox(height: 12),
              Text('Resumen', style: Theme.of(context).textTheme.labelLarge),
              const SizedBox(height: 4),
              Text(
                p.resumenEstructurado!.resumen,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(height: 1.4),
              ),
              if (p.resumenEstructurado!.danosDetectados.isNotEmpty) ...[
                const SizedBox(height: 6),
                Text(
                  'Daños detectados: ${p.resumenEstructurado!.danosDetectados.join(", ")}',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: scheme.onSurfaceVariant,
                        height: 1.35,
                      ),
                ),
              ],
            ],
            if (p.resumenEstructurado?.ficha != null ||
                tieneUbicacionServidor != null ||
                tieneFotoServidor != null ||
                tieneAudioServidor != null) ...[
              const SizedBox(height: 10),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  _chip(
                    context,
                    'Ubicación',
                    tieneUbicacionServidor ?? p.resumenEstructurado?.ficha?.ubicacionValida ?? false,
                  ),
                  _chip(
                    context,
                    'Audio',
                    tieneAudioServidor ?? p.resumenEstructurado?.ficha?.evidenciaAudio ?? false,
                  ),
                  _chip(
                    context,
                    'Imagen',
                    tieneFotoServidor ?? p.resumenEstructurado?.ficha?.evidenciaImagen ?? false,
                  ),
                ],
              ),
            ],
            if (p.hallazgosVision.isNotEmpty) ...[
              const SizedBox(height: 10),
              Text('Hallazgos (visión)', style: Theme.of(context).textTheme.labelLarge),
              const SizedBox(height: 4),
              ...p.hallazgosVision.map(
                (h) => Padding(
                  padding: const EdgeInsets.only(bottom: 4),
                  child: Text('· $h', style: TextStyle(color: scheme.onSurfaceVariant, height: 1.3)),
                ),
              ),
            ],
            if (p.hallazgosVisionPorImagen.isNotEmpty) ...[
              const SizedBox(height: 10),
              Text('Hallazgos por imagen', style: Theme.of(context).textTheme.labelLarge),
              const SizedBox(height: 4),
              ...p.hallazgosVisionPorImagen.asMap().entries.map(
                (entry) => Padding(
                  padding: const EdgeInsets.only(bottom: 4),
                  child: Text(
                    'Imagen ${entry.key + 1}: ${entry.value.join(", ")}',
                    style: TextStyle(color: scheme.onSurfaceVariant, height: 1.3),
                  ),
                ),
              ),
            ],
            if (p.transcripcionAudio != null && p.transcripcionAudio!.trim().isNotEmpty) ...[
              const SizedBox(height: 10),
              Text('Transcripción de audio', style: Theme.of(context).textTheme.labelLarge),
              const SizedBox(height: 4),
              Text(
                p.transcripcionAudio!,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: scheme.onSurfaceVariant,
                      height: 1.35,
                    ),
              ),
            ],
            const SizedBox(height: 8),
            Text(
              'Sugerencia automática: puede requerir validación humana en taller.',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: scheme.onSurfaceVariant,
                    fontStyle: FontStyle.italic,
                  ),
            ),
          ],
        ),
      ),
    );
  }

  static Widget _kv(BuildContext context, String k, String v) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 150,
          child: Text(
            k,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
          ),
        ),
        Expanded(child: Text(v, style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600))),
      ],
    );
  }

  static Widget _chip(BuildContext context, String label, bool value) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        '$label: ${value ? "sí" : "no"}',
        style: Theme.of(context).textTheme.labelSmall,
      ),
    );
  }
}
