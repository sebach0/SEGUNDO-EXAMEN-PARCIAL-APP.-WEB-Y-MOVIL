import 'package:flutter/material.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../../emergencias/domain/solicitud_emergencia_models.dart';
import '../../../emergencias/presentation/widgets/seguimiento/estado_solicitud_badge.dart';

/// Resumen del servicio a cobrar (solicitud + estado).
class ResumenCobroCard extends StatelessWidget {
  const ResumenCobroCard({
    super.key,
    required this.solicitudId,
    required this.estado,
    this.subtitulo,
  });

  final int solicitudId;
  final EstadoSolicitudEmergencia estado;
  final String? subtitulo;

  @override
  Widget build(BuildContext context) {
    final theme = ShadTheme.of(context);

    return ShadCard(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text('Solicitud #$solicitudId', style: theme.textTheme.large),
                ),
                EstadoSolicitudBadge(estado: estado),
              ],
            ),
            if (subtitulo != null) ...[
              const SizedBox(height: 8),
              Text(subtitulo!, style: theme.textTheme.muted),
            ],
            const SizedBox(height: 12),
            Text(
              'El monto lo confirma el taller o tu acuerdo de servicio. Ingresalo para continuar.',
              style: theme.textTheme.small,
            ),
          ],
        ),
      ),
    );
  }
}
