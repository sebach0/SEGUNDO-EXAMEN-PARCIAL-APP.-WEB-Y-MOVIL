import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/config/app_env.dart';

/// Selector de actor: cliente / técnico (placeholder).
class ActorSelectScreen extends StatelessWidget {
  const ActorSelectScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(title: Text(AppEnv.appName)),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              '¿Cómo vas a usar la app?',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 8),
            Text(
              'Elige tu perfil. Más adelante podrás cambiar de modo desde ajustes.',
              style: TextStyle(color: scheme.onSurfaceVariant),
            ),
            const SizedBox(height: 32),
            _ActorCard(
              title: 'Cliente',
              subtitle: 'Registro, vehículos y perfil',
              icon: Icons.person_search,
              onTap: () => context.go('/cliente/login'),
            ),
            const SizedBox(height: 16),
            _ActorCard(
              title: 'Técnico / mecánico',
              subtitle: 'Inicio de sesión, perfil y base operativa',
              icon: Icons.build_circle_outlined,
              accentIcon: true,
              onTap: () => context.go('/tecnico/splash'),
            ),
          ],
        ),
      ),
    );
  }
}

class _ActorCard extends StatelessWidget {
  const _ActorCard({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.onTap,
    this.accentIcon = false,
  });

  final String title;
  final String subtitle;
  final IconData icon;
  final VoidCallback onTap;
  final bool accentIcon;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Material(
      color: scheme.surfaceContainerHighest.withValues(alpha: 0.6),
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Row(
            children: [
              Icon(icon, size: 40, color: accentIcon ? scheme.secondary : scheme.primary),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 18)),
                    const SizedBox(height: 4),
                    Text(subtitle, style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 13)),
                  ],
                ),
              ),
              Icon(Icons.chevron_right, color: scheme.onSurfaceVariant),
            ],
          ),
        ),
      ),
    );
  }
}
