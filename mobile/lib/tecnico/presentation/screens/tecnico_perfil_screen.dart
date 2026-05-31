import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../application/tecnico_auth_provider.dart';

/// Perfil técnico en lectura; edición preparada (sin persistencia aún).
class TecnicoPerfilScreen extends ConsumerWidget {
  const TecnicoPerfilScreen({super.key});

  Future<void> _confirmLogout(BuildContext context, WidgetRef ref) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Cerrar sesión'),
        content: const Text('¿Querés salir de la app técnico?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Salir')),
        ],
      ),
    );
    if (ok == true && context.mounted) {
      await ref.read(tecnicoAuthNotifierProvider.notifier).logout();
      if (context.mounted) context.go('/modo');
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final perfil = ref.watch(tecnicoAuthNotifierProvider).perfil;
    final scheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(title: const Text('Perfil')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
        children: [
        Text(
          'Tu perfil',
          style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700),
        ),
        const SizedBox(height: 8),
        Text(
          'Datos sincronizados con el servidor. La edición avanzada llegará en ciclos posteriores.',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: scheme.onSurface.withValues(alpha: 0.7),
                height: 1.35,
              ),
        ),
        const SizedBox(height: 20),
        _FieldBlock(label: 'Nombre', value: perfil?.nombreCompleto ?? '—'),
        _FieldBlock(label: 'Correo', value: perfil?.email ?? '—'),
        _FieldBlock(label: 'Teléfono', value: perfil?.telefono ?? '—'),
        _FieldBlock(label: 'Especialidad', value: perfil?.especialidadNombre ?? '—'),
        _FieldBlock(label: 'Taller asociado', value: perfil?.tallerNombre ?? '—'),
        _FieldBlock(label: 'Estado', value: perfil?.estadoEtiqueta ?? '—'),
        _FieldBlock(
          label: 'Disponibilidad',
          value: (perfil?.disponibilidad?.trim().isNotEmpty ?? false)
              ? perfil!.disponibilidad!.trim()
              : 'Sin definir',
        ),
        const SizedBox(height: 20),
        FilledButton.tonal(
          onPressed: () {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('La edición de perfil se habilitará en un ciclo posterior.'),
              ),
            );
          },
          child: const Text('Guardar cambios'),
        ),
        const SizedBox(height: 16),
        OutlinedButton.icon(
          onPressed: () => _confirmLogout(context, ref),
          icon: const Icon(Icons.logout_rounded),
          label: const Text('Cerrar sesión'),
        ),
      ],
      ),
    );
  }
}

class _FieldBlock extends StatelessWidget {
  const _FieldBlock({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: DecoratedBox(
        decoration: BoxDecoration(
          color: scheme.surfaceContainerHighest.withValues(alpha: 0.45),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: scheme.outline.withValues(alpha: 0.18)),
        ),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: Theme.of(context).textTheme.labelMedium?.copyWith(
                      color: scheme.onSurface.withValues(alpha: 0.65),
                    ),
              ),
              const SizedBox(height: 4),
              Text(value, style: Theme.of(context).textTheme.bodyLarge?.copyWith(fontWeight: FontWeight.w500)),
            ],
          ),
        ),
      ),
    );
  }
}
