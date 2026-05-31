import 'package:flutter/material.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../../emergencias/domain/solicitud_emergencia_models.dart';
import '../../../emergencias/presentation/widgets/seguimiento/estado_solicitud_badge.dart';

/// Encabezado del chat: solicitud y estado (reutiliza badge de emergencias).
class SolicitudChatHeader extends StatelessWidget {
  const SolicitudChatHeader({
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
        padding: const EdgeInsets.all(14),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Solicitud #$solicitudId', style: theme.textTheme.large),
                  if (subtitulo != null) ...[
                    const SizedBox(height: 4),
                    Text(subtitulo!, style: theme.textTheme.muted),
                  ],
                ],
              ),
            ),
            EstadoSolicitudBadge(estado: estado),
          ],
        ),
      ),
    );
  }
}
