import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../application/client_auth_provider.dart';
import '../../application/vehiculos_providers.dart';

class ClienteHomeScreen extends ConsumerWidget {
  const ClienteHomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final profile = ref.watch(clientAuthNotifierProvider).profile;
    final vehiculos = ref.watch(vehiculosMineProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Inicio')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Text(
            'Hola, ${profile?.nombres ?? 'cliente'}',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 6),
          Text(
            'Resumen de tu cuenta',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
          ),
          const SizedBox(height: 8),
          if (profile != null)
            Text(
              profile.email,
              style: Theme.of(context).textTheme.labelLarge,
            ),
          const SizedBox(height: 24),
          vehiculos.when(
            loading: () => const Center(child: Padding(padding: EdgeInsets.all(24), child: CircularProgressIndicator())),
            error: (e, _) => _ErrorCard(message: e.toString()),
            data: (list) {
              if (list.isEmpty) {
                return _EmptyVehiculos(onRegistrar: () => context.push('/cliente/app/vehiculos/nuevo'));
              }
              return _HasVehiculos(count: list.length);
            },
          ),
          const SizedBox(height: 20),
          _QuickTile(
            icon: Icons.emergency_share_rounded,
            title: 'Reportar emergencia',
            subtitle: 'Ubicación, fotos, audio y detalle',
            onTap: () => context.push('/cliente/app/emergencias'),
          ),
          const SizedBox(height: 12),
          _QuickTile(
            icon: Icons.timeline,
            title: 'Mis solicitudes',
            subtitle: 'Estado, taller, técnico y ETA',
            onTap: () => context.push('/cliente/app/emergencias/solicitudes'),
          ),
          const SizedBox(height: 12),
          _QuickTile(
            icon: Icons.notifications_none_rounded,
            title: 'Notificaciones',
            subtitle: 'Novedades de tus solicitudes y mensajes',
            onTap: () => context.push('/cliente/app/notificaciones'),
          ),
          const SizedBox(height: 12),
          _QuickTile(
            icon: Icons.directions_car,
            title: 'Mis vehículos',
            subtitle: 'Ver y administrar tu flota',
            onTap: () => context.go('/cliente/app/vehiculos'),
          ),
          const SizedBox(height: 12),
          _QuickTile(
            icon: Icons.add_road,
            title: 'Registrar vehículo',
            subtitle: 'Añade placa, marca y modelo',
            onTap: () => context.push('/cliente/app/vehiculos/nuevo'),
          ),
          const SizedBox(height: 12),
          _QuickTile(
            icon: Icons.person,
            title: 'Perfil',
            subtitle: 'Datos de contacto y sesión',
            onTap: () => context.go('/cliente/app/perfil'),
          ),
        ],
      ),
    );
  }
}

class _EmptyVehiculos extends StatelessWidget {
  const _EmptyVehiculos({required this.onRegistrar});

  final VoidCallback onRegistrar;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return ShadCard(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.inbox_outlined, color: scheme.secondary),
                const SizedBox(width: 8),
                Text('Sin vehículos aún', style: Theme.of(context).textTheme.titleMedium),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'Registra al menos un vehículo para estar listo ante una emergencia.',
              style: TextStyle(color: scheme.onSurfaceVariant),
            ),
            const SizedBox(height: 16),
            ShadButton(onPressed: onRegistrar, child: const Text('Registrar vehículo')),
          ],
        ),
      ),
    );
  }
}

class _HasVehiculos extends StatelessWidget {
  const _HasVehiculos({required this.count});

  final int count;

  @override
  Widget build(BuildContext context) {
    return ShadCard(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            const Icon(Icons.check_circle_outline),
            const SizedBox(width: 12),
            Expanded(child: Text('Tienes $count vehículo(s) registrados.')),
          ],
        ),
      ),
    );
  }
}

class _ErrorCard extends StatelessWidget {
  const _ErrorCard({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return ShadCard(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Text(message, style: TextStyle(color: Theme.of(context).colorScheme.error)),
      ),
    );
  }
}

class _QuickTile extends StatelessWidget {
  const _QuickTile({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Material(
      color: scheme.surfaceContainerHighest.withValues(alpha: 0.55),
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Icon(icon, color: scheme.primary),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
                    Text(subtitle, style: TextStyle(fontSize: 12, color: scheme.onSurfaceVariant)),
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
