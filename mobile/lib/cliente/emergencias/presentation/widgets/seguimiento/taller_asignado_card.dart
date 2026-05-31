import 'package:flutter/material.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../../domain/solicitud_seguimiento_models.dart';

/// CU17 — datos del taller asignado.
class TallerAsignadoCard extends StatelessWidget {
  const TallerAsignadoCard({super.key, required this.taller});

  final TallerSeguimientoRead taller;

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
                Icon(Icons.storefront_outlined, color: scheme.primary),
                const SizedBox(width: 8),
                Text('Taller asignado', style: Theme.of(context).textTheme.titleMedium),
              ],
            ),
            const SizedBox(height: 12),
            Text(taller.nombreComercial, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
            const SizedBox(height: 8),
            _row(Icons.phone_outlined, taller.telefonoContacto),
            _row(Icons.email_outlined, taller.emailContacto),
            _row(Icons.place_outlined, '${taller.direccion}, ${taller.ciudad}'),
          ],
        ),
      ),
    );
  }

  Widget _row(IconData icon, String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 18),
          const SizedBox(width: 8),
          Expanded(child: Text(text, style: const TextStyle(height: 1.35))),
        ],
      ),
    );
  }
}
