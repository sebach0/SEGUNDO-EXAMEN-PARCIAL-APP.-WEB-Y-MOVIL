import 'package:flutter/material.dart';

import '../../../domain/solicitud_emergencia_models.dart';

/// Badge de estado actual (CU16) — color accesible según severidad del flujo.
class EstadoSolicitudBadge extends StatelessWidget {
  const EstadoSolicitudBadge({super.key, required this.estado, this.compact = false});

  final EstadoSolicitudEmergencia estado;
  final bool compact;

  Color _background(ColorScheme scheme) {
    return switch (estado) {
      EstadoSolicitudEmergencia.cancelada => scheme.errorContainer,
      EstadoSolicitudEmergencia.finalizada => scheme.tertiaryContainer,
      EstadoSolicitudEmergencia.registrada => scheme.primaryContainer,
      EstadoSolicitudEmergencia.enRevision => scheme.secondaryContainer,
      EstadoSolicitudEmergencia.tallerAsignado => scheme.primaryContainer,
      EstadoSolicitudEmergencia.tecnicoAsignado => scheme.secondaryContainer,
      EstadoSolicitudEmergencia.enCamino => scheme.primaryContainer,
      EstadoSolicitudEmergencia.enAtencion => scheme.secondaryContainer,
    };
  }

  Color _foreground(ColorScheme scheme) {
    return switch (estado) {
      EstadoSolicitudEmergencia.cancelada => scheme.onErrorContainer,
      EstadoSolicitudEmergencia.finalizada => scheme.onTertiaryContainer,
      EstadoSolicitudEmergencia.registrada => scheme.onPrimaryContainer,
      EstadoSolicitudEmergencia.enRevision => scheme.onSecondaryContainer,
      EstadoSolicitudEmergencia.tallerAsignado => scheme.onPrimaryContainer,
      EstadoSolicitudEmergencia.tecnicoAsignado => scheme.onSecondaryContainer,
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
