import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../application/cotizacion_providers.dart';
import '../../domain/cotizacion_models.dart';
import '../../../../core/utils/eta_format.dart';

/// Pantalla donde el cliente compara cotizaciones y selecciona una.
class CotizacionesListScreen extends ConsumerStatefulWidget {
  const CotizacionesListScreen({super.key, required this.solicitudId});

  final int solicitudId;

  @override
  ConsumerState<CotizacionesListScreen> createState() =>
      _CotizacionesListScreenState();
}

class _CotizacionesListScreenState
    extends ConsumerState<CotizacionesListScreen> {
  int? _selectedId;
  bool _confirming = false;

  @override
  Widget build(BuildContext context) {
    final asyncList = ref.watch(cotizacionesBySolicitudProvider(widget.solicitudId));
    final selAsync = ref.watch(seleccionarCotizacionProvider);

    ref.listen<AsyncValue<Cotizacion?>>(seleccionarCotizacionProvider, (_, next) {
      if (next is AsyncData && next.value != null) {
        if (mounted) {
          ShadToaster.of(context).show(
            const ShadToast(
              title: Text('Cotización aceptada'),
              description: Text('El taller ha sido notificado. ¡Tu solicitud está en marcha!'),
            ),
          );
          ref.invalidate(cotizacionesBySolicitudProvider(widget.solicitudId));
          if (context.canPop()) context.pop();
        }
      }
      if (next is AsyncError && mounted) {
        ShadToaster.of(context).show(
          ShadToast.destructive(
            title: const Text('Error al seleccionar'),
            description: Text(next.error.toString()),
          ),
        );
      }
    });

    return Scaffold(
      appBar: AppBar(
        title: const Text('Cotizaciones'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () =>
              context.canPop() ? context.pop() : context.go('/cliente/app/emergencias/solicitudes'),
        ),
      ),
      body: asyncList.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => _ErrorBody(
          message: e.toString(),
          onRetry: () => ref.invalidate(
            cotizacionesBySolicitudProvider(widget.solicitudId),
          ),
        ),
        data: (cotizaciones) {
          if (cotizaciones.isEmpty) {
            return const _EmptyBody();
          }

          // Hay cotización aceptada → mostrarla en primer lugar
          final aceptada = cotizaciones
              .where((c) => c.estado == EstadoCotizacion.aceptada)
              .firstOrNull;
          final activas = cotizaciones
              .where((c) => c.estado == EstadoCotizacion.enviada)
              .toList();
          final otras = cotizaciones
              .where((c) =>
                  c.estado != EstadoCotizacion.aceptada &&
                  c.estado != EstadoCotizacion.enviada)
              .toList();

          final yaSeleccionada = aceptada != null;

          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              if (yaSeleccionada) ...[
                const _InfoBanner(
                  icon: Icons.check_circle_rounded,
                  color: Colors.green,
                  message:
                      'Ya seleccionaste una cotización. Las demás han sido descartadas.',
                ),
                const SizedBox(height: 16),
                _CotizacionCard(
                  cotizacion: aceptada,
                  isSelected: true,
                  isDisabled: false,
                  onSeleccionar: null,
                ),
              ] else ...[
                if (activas.isEmpty)
                  const _InfoBanner(
                    icon: Icons.info_outline_rounded,
                    color: Colors.orange,
                    message: 'No hay cotizaciones activas por el momento. Intenta de nuevo más tarde.',
                  )
                else ...[
                  Text(
                    'Comparar cotizaciones (${activas.length})',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Compará talleres por precio, distancia y servicios. Orden sugerido: más cercano primero.',
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                      fontSize: 13,
                    ),
                  ),
                  const SizedBox(height: 16),
                  for (final c in activas) ...[
                    _CotizacionCard(
                      cotizacion: c,
                      isSelected: _selectedId == c.id,
                      isDisabled: _confirming || selAsync is AsyncLoading,
                      onSeleccionar: () => _confirmarSeleccion(context, c),
                    ),
                    const SizedBox(height: 12),
                  ],
                ],
              ],
              if (otras.isNotEmpty) ...[
                const SizedBox(height: 16),
                Text(
                  'Otras cotizaciones (${otras.length})',
                  style: Theme.of(context)
                      .textTheme
                      .labelMedium
                      ?.copyWith(color: Theme.of(context).colorScheme.outline),
                ),
                const SizedBox(height: 8),
                for (final c in otras) ...[
                  _CotizacionCard(
                    cotizacion: c,
                    isSelected: false,
                    isDisabled: true,
                    onSeleccionar: null,
                  ),
                  const SizedBox(height: 8),
                ],
              ],
            ],
          );
        },
      ),
    );
  }

  Future<void> _confirmarSeleccion(
      BuildContext context, Cotizacion cotizacion) async {
    final ok = await showDialog<bool>(
      context: context,
      useRootNavigator: true,
      barrierDismissible: true,
      builder: (dialogContext) => AlertDialog(
        title: const Text('¿Aceptar esta cotización?'),
        content: Text(
          'Taller: ${cotizacion.tallerNombre ?? 'Sin nombre'}\n'
          'Total: Bs. ${cotizacion.montoTotal.toStringAsFixed(2)}\n\n'
          'Las demás cotizaciones serán descartadas.',
        ),
        actions: [
          TextButton(
            onPressed: () =>
                Navigator.of(dialogContext, rootNavigator: true).pop(false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () =>
                Navigator.of(dialogContext, rootNavigator: true).pop(true),
            child: const Text('Sí, aceptar'),
          ),
        ],
      ),
    );
    if (ok != true || !mounted) return;
    setState(() {
      _selectedId = cotizacion.id;
      _confirming = true;
    });
    await ref.read(seleccionarCotizacionProvider.notifier).seleccionar(
          solicitudId: widget.solicitudId,
          cotizacionId: cotizacion.id,
        );
    if (mounted) setState(() => _confirming = false);
  }
}

// ── _CotizacionCard ─────────────────────────────────────────────────────────

class _CotizacionCard extends StatelessWidget {
  const _CotizacionCard({
    required this.cotizacion,
    required this.isSelected,
    required this.isDisabled,
    required this.onSeleccionar,
  });

  final Cotizacion cotizacion;
  final bool isSelected;
  final bool isDisabled;
  final VoidCallback? onSeleccionar;

  @override
  Widget build(BuildContext context) {
    final c = cotizacion;
    final scheme = Theme.of(context).colorScheme;

    final isInactive = c.estado == EstadoCotizacion.expirada ||
        c.estado == EstadoCotizacion.rechazada;

    return Opacity(
      opacity: isInactive ? 0.5 : 1.0,
      child: ShadCard(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        c.tallerNombre ?? 'Taller #${c.tallerId}',
                        style: Theme.of(context)
                            .textTheme
                            .titleSmall
                            ?.copyWith(fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 2),
                      _EstadoBadge(estado: c.estado),
                    ],
                  ),
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      'Bs. ${c.montoTotal.toStringAsFixed(2)}',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            color: scheme.primary,
                            fontWeight: FontWeight.bold,
                          ),
                    ),
                    Text(
                      c.costoTraslado > 0 ? 'Total (servicio + traslado)' : 'Total estimado',
                      style: Theme.of(context).textTheme.labelSmall,
                    ),
                  ],
                ),
              ],
            ),
            const Divider(height: 20),
            if (c.distanciaKm != null)
              _Row(
                label: 'Distancia',
                value: '${c.distanciaKm!.toStringAsFixed(1)} km',
              ),
            if (c.costoTraslado > 0) ...[
              _Row(
                label: 'Traslado técnico',
                value: 'Bs. ${c.costoTraslado.toStringAsFixed(2)}',
              ),
              if (c.montoServicio > 0 && c.montoServicio < c.montoTotal)
                _Row(
                  label: 'Servicio',
                  value: 'Bs. ${c.montoServicio.toStringAsFixed(2)}',
                ),
            ],
            _Row(label: 'Daño', value: c.descripcionDanio),
            _Row(label: 'Servicio', value: c.detalleServicio),
            if (c.serviciosOfrecidos.isNotEmpty) ...[
              const SizedBox(height: 8),
              Wrap(
                spacing: 6,
                runSpacing: 6,
                children: [
                  for (final s in c.serviciosOfrecidos)
                    Chip(
                      label: Text(s.nombre, style: const TextStyle(fontSize: 11)),
                      visualDensity: VisualDensity.compact,
                      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                ],
              ),
            ],
            if (c.tiempoEstimadoLlegadaMin != null)
              _Row(label: 'ETA llegada', value: formatEtaMinutos(c.tiempoEstimadoLlegadaMin)),
            if (c.tiempoEstimadoReparacionMin != null)
              _Row(label: 'Reparación est.', value: formatEtaMinutos(c.tiempoEstimadoReparacionMin)),
            _Row(
              label: 'Grúa incluida',
              value: c.incluyeGrua ? 'Sí' : 'No',
              valueColor: c.incluyeGrua ? Colors.green : null,
            ),
            if (c.garantiaDescripcion != null)
              _Row(label: 'Garantía', value: c.garantiaDescripcion!),
            if (c.comentarios != null && c.comentarios!.isNotEmpty)
              _Row(label: 'Comentarios', value: c.comentarios!),
            // Ítems
            if (c.items.isNotEmpty) ...[
              const SizedBox(height: 12),
              Text('Desglose', style: Theme.of(context).textTheme.labelMedium),
              const SizedBox(height: 6),
              for (final item in c.items)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 2),
                  child: Row(
                    children: [
                      Expanded(
                        child: Text(
                          '${item.cantidad.toStringAsFixed(0)} × ${item.descripcion}',
                          style: const TextStyle(fontSize: 13),
                        ),
                      ),
                      Text(
                        'Bs. ${item.subtotal.toStringAsFixed(2)}',
                        style: TextStyle(
                            fontSize: 13,
                            fontWeight: item == c.itemTraslado
                                ? FontWeight.w600
                                : FontWeight.w500,
                            color: item == c.itemTraslado
                                ? scheme.primary
                                : null),
                      ),
                    ],
                  ),
                ),
            ],
            // Botón seleccionar
            if (onSeleccionar != null) ...[
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: ShadButton(
                  onPressed: isDisabled ? null : onSeleccionar,
                  child: isDisabled && isSelected
                      ? const Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            ),
                            SizedBox(width: 8),
                            Text('Procesando...'),
                          ],
                        )
                      : const Text('Seleccionar esta cotización'),
                ),
              ),
            ],
            if (isSelected && onSeleccionar == null) ...[
              const SizedBox(height: 12),
              Row(
                children: [
                  const Icon(Icons.check_circle, color: Colors.green, size: 18),
                  const SizedBox(width: 6),
                  Text(
                    'Cotización seleccionada',
                    style: TextStyle(
                      color: Colors.green.shade700,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}

// ── Helpers ──────────────────────────────────────────────────────────────────

class _Row extends StatelessWidget {
  const _Row({required this.label, required this.value, this.valueColor});

  final String label;
  final String value;
  final Color? valueColor;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              label,
              style: TextStyle(
                fontSize: 13,
                color: Theme.of(context).colorScheme.outline,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w500,
                color: valueColor,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _EstadoBadge extends StatelessWidget {
  const _EstadoBadge({required this.estado});
  final EstadoCotizacion estado;

  Color get _color => switch (estado) {
        EstadoCotizacion.enviada   => Colors.blue,
        EstadoCotizacion.aceptada  => Colors.green,
        EstadoCotizacion.rechazada => Colors.red,
        EstadoCotizacion.expirada  => Colors.grey,
      };

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: _color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: _color.withValues(alpha: 0.4)),
      ),
      child: Text(
        estado.etiqueta,
        style: TextStyle(
          color: _color,
          fontSize: 11,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }
}

class _InfoBanner extends StatelessWidget {
  const _InfoBanner({
    required this.icon,
    required this.color,
    required this.message,
  });

  final IconData icon;
  final Color color;
  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Row(
        children: [
          Icon(icon, color: color, size: 20),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              message,
              style: TextStyle(color: color.withValues(alpha: 0.9), fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }
}

class _EmptyBody extends StatelessWidget {
  const _EmptyBody();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.receipt_long_outlined,
              size: 56,
              color: Theme.of(context).colorScheme.outlineVariant,
            ),
            const SizedBox(height: 16),
            Text(
              'Sin cotizaciones aún',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            Text(
              'Los talleres cercanos enviarán propuestas con precio y servicios. '
              'Volvé aquí para comparar y elegir la más conveniente.',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ErrorBody extends StatelessWidget {
  const _ErrorBody({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              message,
              textAlign: TextAlign.center,
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
            const SizedBox(height: 16),
            ShadButton.outline(
                onPressed: onRetry, child: const Text('Reintentar')),
          ],
        ),
      ),
    );
  }
}
