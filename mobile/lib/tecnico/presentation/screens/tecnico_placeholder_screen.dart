import 'package:flutter/material.dart';

/// Placeholder reutilizable para funciones futuras del módulo técnico.
class TecnicoPlaceholderScreen extends StatelessWidget {
  const TecnicoPlaceholderScreen({
    super.key,
    required this.title,
    required this.message,
    this.icon = Icons.construction_rounded,
  });

  final String title;
  final String message;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 64, color: scheme.primary.withValues(alpha: 0.85)),
            const SizedBox(height: 24),
            if (title.trim().isNotEmpty) ...[
              Text(
                title,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w600),
              ),
              const SizedBox(height: 12),
            ],
            Text(
              message,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: scheme.onSurface.withValues(alpha: 0.75),
                    height: 1.4,
                  ),
            ),
          ],
        ),
      ),
    );
  }
}
