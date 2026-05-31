import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../../core/utils/bolivia_time.dart';
import '../../application/emergencias_providers.dart';
import '../../domain/solicitud_emergencia_models.dart';
import '../widgets/emergencia_ubicacion_osm_map.dart';

/// Mapa y datos de la última posición compartida por el técnico asignado.
class EmergenciaUbicacionTecnicoScreen extends ConsumerWidget {
  const EmergenciaUbicacionTecnicoScreen({super.key, required this.solicitudId});

  final int solicitudId;

  Future<void> _abrirNavegacionExterna(double lat, double lng) async {
    final uri = Uri.parse('https://www.google.com/maps/search/?api=1&query=$lat,$lng');
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  static SolicitudUbicacionRead? _ubicacionActualCliente(SolicitudEmergenciaDetail d) {
    for (final u in d.ubicaciones) {
      if (u.esActual) return u;
    }
    return null;
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(emergenciaUbicacionTecnicoProvider(solicitudId));
    final detailAsync = ref.watch(emergenciaDetailProvider(solicitudId));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Ubicación del técnico'),
        leading: BackButton(onPressed: () => context.pop()),
      ),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => _UbicacionError(
          message: e.toString().replaceFirst('Exception: ', ''),
          onRetry: () => ref.invalidate(emergenciaUbicacionTecnicoProvider(solicitudId)),
        ),
        data: (u) {
          final scheme = Theme.of(context).colorScheme;
          final clienteUb = detailAsync.maybeWhen(
            data: _ubicacionActualCliente,
            orElse: () => null,
          );
          return ListView(
            padding: const EdgeInsets.fromLTRB(20, 12, 20, 28),
            children: [
              EmergenciaUbicacionOsmMap(
                latitude: u.latitud,
                longitude: u.longitud,
                routeToLatitude: clienteUb?.latitud,
                routeToLongitude: clienteUb?.longitud,
                height: 260,
              ),
              if (clienteUb != null) ...[
                const SizedBox(height: 8),
                Text(
                  'Línea azul: aproximación directa técnico → tu última ubicación compartida en la solicitud.',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: scheme.onSurfaceVariant,
                        height: 1.35,
                      ),
                ),
              ],
              const SizedBox(height: 16),
              Text(
                'Coordenadas',
                style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 6),
              SelectableText(
                '${u.latitud.toStringAsFixed(6)}, ${u.longitud.toStringAsFixed(6)}',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              if (u.precisionMetros != null) ...[
                const SizedBox(height: 8),
                Text(
                  'Precisión aprox.: ${u.precisionMetros!.toStringAsFixed(0)} m',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(color: scheme.onSurfaceVariant),
                ),
              ],
              const SizedBox(height: 8),
              Text(
                'Actualizado: ${BoliviaTime.formatWithZone(u.actualizadoAt)}',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(color: scheme.onSurfaceVariant),
              ),
              const SizedBox(height: 24),
              FilledButton.icon(
                icon: const Icon(Icons.navigation_rounded),
                label: const Padding(
                  padding: EdgeInsets.symmetric(vertical: 14),
                  child: Text('Abrir en mapas', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                ),
                onPressed: () => _abrirNavegacionExterna(u.latitud, u.longitud),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _UbicacionError extends StatelessWidget {
  const _UbicacionError({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.location_off_outlined, size: 52, color: scheme.onSurfaceVariant),
            const SizedBox(height: 16),
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            FilledButton(onPressed: onRetry, child: const Text('Reintentar')),
          ],
        ),
      ),
    );
  }
}
