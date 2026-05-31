import 'package:flutter/material.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../../domain/solicitud_seguimiento_models.dart';

/// Técnico asignado (CU17 ext.).
class TecnicoAsignadoCard extends StatelessWidget {
  const TecnicoAsignadoCard({super.key, required this.tecnico});

  final TecnicoSeguimientoRead tecnico;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return ShadCard(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.engineering_outlined, color: scheme.primary),
                const SizedBox(width: 8),
                Text('Técnico asignado', style: Theme.of(context).textTheme.titleMedium),
              ],
            ),
            const SizedBox(height: 12),
            Text(tecnico.nombreCompleto, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
            const SizedBox(height: 8),
            Row(
              children: [
                const Icon(Icons.phone_outlined, size: 18),
                const SizedBox(width: 8),
                Text(tecnico.telefono),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
