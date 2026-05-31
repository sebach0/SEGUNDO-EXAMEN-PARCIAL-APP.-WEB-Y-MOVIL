import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/utils/bolivia_time.dart';
import '../../application/tecnico_emergencias_providers.dart';
import '../../domain/tecnico_servicio_models.dart';
import '../widgets/tecnico_estado_servicio_badge.dart';

/// Detalle operativo de un servicio asignado (CU32 + accesos CU33–CU35).
class TecnicoServicioDetalleScreen extends ConsumerWidget {
  const TecnicoServicioDetalleScreen({
    super.key,
    required this.solicitudId,
    this.initial,
  });

  final int solicitudId;
  final ServicioAsignadoTecnico? initial;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final listAsync = ref.watch(tecnicoServiciosAsignadosProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text('Servicio #$solicitudId'),
        leading: BackButton(onPressed: () => context.canPop() ? context.pop() : context.go('/tecnico/app/servicios')),
      ),
      body: listAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => _Msg(
          e.toString().replaceFirst('Exception: ', ''),
          onRetry: () => ref.invalidate(tecnicoServiciosAsignadosProvider),
        ),
        data: (list) {
          ServicioAsignadoTecnico? found;
          for (final x in list) {
            if (x.solicitudId == solicitudId) {
              found = x;
              break;
            }
          }
          final s = found ?? initial;
          if (s == null) {
            return _Msg(
              'No encontramos este servicio en tu bandeja. Puede haber sido reasignado.',
              onRetry: () {
                ref.invalidate(tecnicoServiciosAsignadosProvider);
                if (context.mounted) context.go('/tecnico/app/servicios');
              },
              retryLabel: 'Volver a la lista',
            );
          }
          return _DetalleBody(servicio: s);
        },
      ),
    );
  }
}

class _DetalleBody extends StatelessWidget {
  const _DetalleBody({required this.servicio});

  final ServicioAsignadoTecnico servicio;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 8, 20, 28),
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: Text(
                servicio.clienteNombreCompleto,
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800),
              ),
            ),
            TecnicoEstadoServicioBadge(estado: servicio.estado),
          ],
        ),
        const SizedBox(height: 6),
        _line(Icons.phone_in_talk_outlined, servicio.telefono),
        const SizedBox(height: 20),
        Text('Vehículo', style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w700)),
        const SizedBox(height: 8),
        _line(Icons.directions_car_outlined, servicio.vehiculoLinea),
        if (servicio.tipoVehiculo != null && servicio.tipoVehiculo!.trim().isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: _line(Icons.category_outlined, servicio.tipoVehiculo!.trim()),
          ),
        if (servicio.categoriaUi != null || servicio.prioridadUi != null) ...[
          const SizedBox(height: 12),
          Text('Incidente', style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w700)),
          const SizedBox(height: 8),
          if (servicio.categoriaUi != null) _line(Icons.report_problem_outlined, 'Tipo: ${servicio.categoriaUi}'),
          if (servicio.prioridadUi != null)
            Padding(
              padding: const EdgeInsets.only(top: 6),
              child: _line(Icons.priority_high_rounded, 'Prioridad: ${servicio.prioridadUi}'),
            ),
        ],
        const SizedBox(height: 20),
        Text('Ubicación (última conocida)', style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w700)),
        const SizedBox(height: 8),
        if (servicio.direccionReferencia != null && servicio.direccionReferencia!.trim().isNotEmpty)
          Text(servicio.direccionReferencia!, style: Theme.of(context).textTheme.bodyMedium?.copyWith(height: 1.35)),
        if (servicio.latitud != null && servicio.longitud != null)
          Text(
            '${servicio.latitud!.toStringAsFixed(5)}, ${servicio.longitud!.toStringAsFixed(5)}',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(color: scheme.onSurfaceVariant),
          )
        else
          Text(
            'Sin coordenadas en el listado. Usá “Ver ubicación” para la posición actual del cliente.',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(color: scheme.onSurfaceVariant, height: 1.35),
          ),
        const SizedBox(height: 8),
        Text(
          'Actualizado: ${BoliviaTime.formatWithZone(servicio.updatedAt)}',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(color: scheme.onSurfaceVariant),
        ),
        if (servicio.tiempoEstimadoMin != null) ...[
          const SizedBox(height: 12),
          DecoratedBox(
            decoration: BoxDecoration(
              color: scheme.primaryContainer.withValues(alpha: 0.5),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  Icon(Icons.timer_outlined, color: scheme.primary),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      'Tiempo estimado: ~${servicio.tiempoEstimadoMin} min',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
        const SizedBox(height: 28),
        Text(
          'La app no muestra galería de evidencias en esta versión; si el cliente adjuntó archivos, coordiná con el taller.',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: scheme.onSurfaceVariant,
                height: 1.35,
              ),
        ),
        const SizedBox(height: 24),
        _BigAction(
          icon: Icons.map_outlined,
          label: 'Ver ubicación del cliente',
          onPressed: () => context.push('/tecnico/app/servicios/${servicio.solicitudId}/ubicacion'),
        ),
        const SizedBox(height: 12),
        _BigAction(
          icon: Icons.share_location_rounded,
          label: 'Compartir mi ubicación',
          onPressed: servicio.esTerminal
              ? null
              : () => context.push('/tecnico/app/servicios/${servicio.solicitudId}/compartir-ubicacion'),
        ),
        const SizedBox(height: 12),
        _BigAction(
          icon: Icons.edit_road_rounded,
          label: 'Actualizar estado',
          onPressed: servicio.esTerminal
              ? null
              : () => context.push('/tecnico/app/servicios/${servicio.solicitudId}/estado', extra: servicio),
        ),
        const SizedBox(height: 12),
        _BigAction(
          icon: Icons.chat_bubble_outline_rounded,
          label: 'Chat con el cliente',
          onPressed: () => context.push('/tecnico/app/servicios/${servicio.solicitudId}/chat', extra: servicio),
        ),
      ],
    );
  }

  Widget _line(IconData icon, String text) {
    return Builder(
      builder: (context) {
        return Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, size: 22, color: Theme.of(context).colorScheme.primary),
            const SizedBox(width: 10),
            Expanded(child: Text(text, style: Theme.of(context).textTheme.bodyLarge)),
          ],
        );
      },
    );
  }
}

class _BigAction extends StatelessWidget {
  const _BigAction({
    required this.icon,
    required this.label,
    required this.onPressed,
  });

  final IconData icon;
  final String label;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Semantics(
      label: label,
      button: true,
      enabled: onPressed != null,
      child: FilledButton.icon(
        icon: Icon(icon, size: 22),
        label: Padding(
          padding: const EdgeInsets.symmetric(vertical: 14),
          child: Text(label, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
        ),
        style: FilledButton.styleFrom(
          alignment: Alignment.centerLeft,
          backgroundColor: onPressed == null ? scheme.surfaceContainerHighest : null,
          foregroundColor: onPressed == null ? scheme.onSurfaceVariant : null,
        ),
        onPressed: onPressed,
      ),
    );
  }
}

class _Msg extends StatelessWidget {
  const _Msg(this.text, {this.onRetry, this.retryLabel = 'Reintentar'});

  final String text;
  final VoidCallback? onRetry;
  final String retryLabel;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(text, textAlign: TextAlign.center),
            if (onRetry != null) ...[
              const SizedBox(height: 16),
              FilledButton(onPressed: onRetry, child: Text(retryLabel)),
            ],
          ],
        ),
      ),
    );
  }
}
