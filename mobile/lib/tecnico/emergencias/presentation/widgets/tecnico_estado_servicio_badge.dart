import 'package:flutter/material.dart';

import '../../../../cliente/emergencias/domain/solicitud_emergencia_models.dart';

/// Badge legible para estados de solicitud en vista técnico (campo).
class TecnicoEstadoServicioBadge extends StatelessWidget {
  const TecnicoEstadoServicioBadge({super.key, required this.estado, this.compact = false});

  final EstadoSolicitudEmergencia estado;
  final bool compact;

  Color _background(ColorScheme scheme) {
    return switch (estado) {
      EstadoSolicitudEmergencia.cancelada => scheme.errorContainer,
      EstadoSolicitudEmergencia.finalizada => scheme.tertiaryContainer,
      EstadoSolicitudEmergencia.registrada ||
      EstadoSolicitudEmergencia.enRevision =>
        scheme.surfaceContainerHighest,
      EstadoSolicitudEmergencia.tallerAsignado ||
      EstadoSolicitudEmergencia.tecnicoAsignado =>
        scheme.secondaryContainer,
      EstadoSolicitudEmergencia.enCamino => scheme.primaryContainer,
      EstadoSolicitudEmergencia.enAtencion => scheme.secondaryContainer,
    };
  }

  Color _foreground(ColorScheme scheme) {
    return switch (estado) {
      EstadoSolicitudEmergencia.cancelada => scheme.onErrorContainer,
      EstadoSolicitudEmergencia.finalizada => scheme.onTertiaryContainer,
      EstadoSolicitudEmergencia.registrada ||
      EstadoSolicitudEmergencia.enRevision =>
        scheme.onSurfaceVariant,
      EstadoSolicitudEmergencia.tallerAsignado ||
      EstadoSolicitudEmergencia.tecnicoAsignado =>
        scheme.onSecondaryContainer,
      EstadoSolicitudEmergencia.enCamino => scheme.onPrimaryContainer,
      EstadoSolicitudEmergencia.enAtencion => scheme.onSecondaryContainer,
    };
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Chip(
      visualDensity: compact ? VisualDensity.compact : VisualDensity.standard,
      padding: compact ? const EdgeInsets.symmetric(horizontal: 4) : null,
      label: Text(
        estado.etiquetaUi,
        style: TextStyle(
          fontSize: compact ? 11 : 13,
          fontWeight: FontWeight.w600,
          color: _foreground(scheme),
        ),
      ),
      side: BorderSide(color: scheme.outline.withValues(alpha: 0.35)),
      backgroundColor: _background(scheme),
    );
  }
}
