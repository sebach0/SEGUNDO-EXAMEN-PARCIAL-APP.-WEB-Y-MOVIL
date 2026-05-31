import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../application/tecnico_auth_provider.dart';
import '../../domain/models/tecnico_perfil.dart';
import '../../emergencias/application/tecnico_emergencias_providers.dart';
import '../../emergencias/domain/tecnico_servicio_models.dart';
import '../../../cliente/emergencias/domain/solicitud_emergencia_models.dart';

/// Home técnico — resumen operativo (sin casos reales aún).
class TecnicoHomeScreen extends ConsumerWidget {
  const TecnicoHomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(tecnicoAuthNotifierProvider);
    final perfil = auth.perfil;
    final serviciosAsync = ref.watch(tecnicoServiciosAsignadosProvider);
    final scheme = Theme.of(context).colorScheme;
    final primerNombre = _primerNombre(perfil?.nombres);
    final tallerLine = () {
      final tn = perfil?.tallerNombre?.trim();
      if (tn != null && tn.isNotEmpty) return 'Resumen de tu cuenta en $tn';
      return 'Resumen de tu cuenta';
    }();

    return Scaffold(
      appBar: AppBar(title: const Text('Inicio')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
        children: [
        Text(
          'Hola, $primerNombre',
          style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700),
        ),
        const SizedBox(height: 6),
        Text(
          tallerLine,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: scheme.onSurface.withValues(alpha: 0.72),
              ),
        ),
        const SizedBox(height: 20),
        _ResumenServiciosCard(asyncServicios: serviciosAsync),
        const SizedBox(height: 16),
        _EstadoCard(perfil: perfil),
        const SizedBox(height: 16),
        _DisponibilidadCard(perfil: perfil),
        const SizedBox(height: 24),
        serviciosAsync.when(
          data: (list) {
            final recientes = list
                .where((s) => s.estado == EstadoSolicitudEmergencia.finalizada)
                .toList()
              ..sort((a, b) => b.updatedAt.compareTo(a.updatedAt));
            final top = recientes.take(3).toList();
            if (top.isEmpty) return const SizedBox.shrink();
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Últimos finalizados',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 10),
                ...top.map(
                  (s) => Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: _RecentTile(
                      title: s.clienteNombreCompleto,
                      subtitle: s.placa,
                      onTap: () => context.push('/tecnico/app/servicios/${s.solicitudId}', extra: s),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
              ],
            );
          },
          loading: () => const SizedBox.shrink(),
          error: (_, __) => const SizedBox.shrink(),
        ),
        Text(
          'Accesos rápidos',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600),
        ),
        const SizedBox(height: 12),
        _QuickTile(
          icon: Icons.assignment_outlined,
          title: 'Servicios asignados',
          subtitle: 'Ver pendientes y en curso',
          onTap: () => context.go('/tecnico/app/servicios'),
        ),
        const SizedBox(height: 10),
        _QuickTile(
          icon: Icons.history_rounded,
          title: 'Historial',
          subtitle: 'Servicios finalizados',
          onTap: () => context.push('/tecnico/app/historial'),
        ),
        const SizedBox(height: 10),
        _QuickTile(
          icon: Icons.person_outline,
          title: 'Perfil',
          subtitle: 'Datos y disponibilidad',
          onTap: () => context.go('/tecnico/app/perfil'),
        ),
      ],
      ),
    );
  }
}

String _primerNombre(String? nombres) {
  final t = nombres?.trim() ?? '';
  if (t.isEmpty) return 'Técnico';
  return t.split(RegExp(r'\s+')).first;
}

class _ResumenServiciosCard extends StatelessWidget {
  const _ResumenServiciosCard({required this.asyncServicios});

  final AsyncValue<List<ServicioAsignadoTecnico>> asyncServicios;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return asyncServicios.when(
      loading: () => _InfoCard(
        title: 'Servicios de hoy',
        child: Row(
          children: [
            SizedBox(
              width: 22,
              height: 22,
              child: CircularProgressIndicator(strokeWidth: 2, color: scheme.primary),
            ),
            const SizedBox(width: 12),
            Text('Cargando bandeja…', style: Theme.of(context).textTheme.bodyMedium),
          ],
        ),
      ),
      error: (e, _) => _InfoCard(
        title: 'Servicios de hoy',
        child: Text(
          e.toString().replaceFirst('Exception: ', ''),
          style: Theme.of(context).textTheme.bodySmall?.copyWith(color: scheme.error),
        ),
      ),
      data: (list) {
        final activos = list
            .where(
              (s) =>
                  s.estado != EstadoSolicitudEmergencia.finalizada &&
                  s.estado != EstadoSolicitudEmergencia.cancelada,
            )
            .length;
        return _InfoCard(
          title: 'Servicios de hoy',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '$activos activos',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 4),
              Text(
                '${list.length} asignados en total (incluye cerrados)',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: scheme.onSurface.withValues(alpha: 0.72),
                    ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _RecentTile extends StatelessWidget {
  const _RecentTile({
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  final String title;
  final String subtitle;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Material(
      color: scheme.surfaceContainerHighest.withValues(alpha: 0.4),
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          child: Row(
            children: [
              Icon(Icons.check_circle_outline_rounded, color: scheme.tertiary, size: 26),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15)),
                    Text(subtitle, style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 13)),
                  ],
                ),
              ),
              Icon(Icons.chevron_right_rounded, color: scheme.onSurfaceVariant),
            ],
          ),
        ),
      ),
    );
  }
}

class _EstadoCard extends StatelessWidget {
  const _EstadoCard({required this.perfil});

  final TecnicoPerfil? perfil;

  @override
  Widget build(BuildContext context) {
    final estado = perfil?.estadoEtiqueta ?? '—';
    final roles = perfil?.roles.join(', ') ?? '—';
    return _InfoCard(
      title: 'Estado de cuenta',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _kv(context, 'Estado', estado),
          const SizedBox(height: 8),
          _kv(context, 'Roles', roles),
        ],
      ),
    );
  }

  Widget _kv(BuildContext context, String k, String v) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 88,
          child: Text(
            k,
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
                  color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.65),
                ),
          ),
        ),
        Expanded(
          child: Text(v, style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w500)),
        ),
      ],
    );
  }
}

class _DisponibilidadCard extends StatelessWidget {
  const _DisponibilidadCard({required this.perfil});

  final TecnicoPerfil? perfil;

  @override
  Widget build(BuildContext context) {
    final disp = perfil?.disponibilidad;
    final text = (disp != null && disp.trim().isNotEmpty) ? disp : 'Sin preferencia registrada';
    return _InfoCard(
      title: 'Disponibilidad',
      child: Text(
        text,
        style: Theme.of(context).textTheme.bodyMedium?.copyWith(height: 1.35),
      ),
    );
  }
}

class _InfoCard extends StatelessWidget {
  const _InfoCard({required this.title, required this.child});

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return DecoratedBox(
      decoration: BoxDecoration(
        color: scheme.surfaceContainerHighest.withValues(alpha: 0.55),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: scheme.outline.withValues(alpha: 0.2)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
            const SizedBox(height: 10),
            child,
          ],
        ),
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
      color: scheme.surfaceContainerHighest.withValues(alpha: 0.45),
      borderRadius: BorderRadius.circular(14),
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          child: Row(
            children: [
              Icon(icon, color: scheme.primary, size: 28),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 16)),
                    const SizedBox(height: 2),
                    Text(subtitle, style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 13)),
                  ],
                ),
              ),
              Icon(Icons.chevron_right_rounded, color: scheme.onSurfaceVariant),
            ],
          ),
        ),
      ),
    );
  }
}
