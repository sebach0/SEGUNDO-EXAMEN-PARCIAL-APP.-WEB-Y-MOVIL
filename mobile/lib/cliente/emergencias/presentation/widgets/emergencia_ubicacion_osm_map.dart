import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';

/// Vista de mapa con tiles de [OpenStreetMap](https://www.openstreetmap.org/) vía [flutter_map](https://pub.dev/packages/flutter_map).
///
/// Si [routeToLatitude] y [routeToLongitude] están definidos, dibuja un segmento recto
/// (no sigue calles; es la opción más simple sin API de routing tipo OSRM/GraphHopper).
class EmergenciaUbicacionOsmMap extends StatelessWidget {
  const EmergenciaUbicacionOsmMap({
    super.key,
    required this.latitude,
    required this.longitude,
    this.routeToLatitude,
    this.routeToLongitude,
    this.height = 220,
    this.initialZoom = 15,
  });

  final double latitude;
  final double longitude;
  /// Segundo extremo del segmento (p. ej. ubicación del cliente si el primero es el técnico).
  final double? routeToLatitude;
  final double? routeToLongitude;
  final double height;
  final double initialZoom;

  static const _osmTemplate = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';

  @override
  Widget build(BuildContext context) {
    final point = LatLng(latitude, longitude);
    final LatLng? routeEnd = routeToLatitude != null && routeToLongitude != null
        ? LatLng(routeToLatitude!, routeToLongitude!)
        : null;

    final MapOptions mapOptions;
    if (routeEnd != null) {
      final bounds = LatLngBounds.fromPoints([point, routeEnd]);
      mapOptions = MapOptions(
        initialCameraFit: CameraFit.bounds(
          bounds: bounds,
          padding: const EdgeInsets.fromLTRB(24, 24, 24, 48),
        ),
        interactionOptions: const InteractionOptions(
          flags: InteractiveFlag.all & ~InteractiveFlag.rotate,
        ),
      );
    } else {
      mapOptions = MapOptions(
        initialCenter: point,
        initialZoom: initialZoom,
        interactionOptions: const InteractionOptions(
          flags: InteractiveFlag.all & ~InteractiveFlag.rotate,
        ),
      );
    }

    final markers = <Marker>[
      Marker(
        point: point,
        width: 48,
        height: 48,
        alignment: Alignment.center,
        child: Icon(
          routeEnd != null ? Icons.engineering : Icons.location_on,
          color: routeEnd != null ? const Color(0xFF1565C0) : const Color(0xFFE53935),
          size: 44,
        ),
      ),
    ];
    if (routeEnd != null) {
      markers.add(
        Marker(
          point: routeEnd,
          width: 48,
          height: 48,
          alignment: Alignment.center,
          child: const Icon(Icons.location_on, color: Color(0xFFE53935), size: 44),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SizedBox(
          height: height,
          child: ClipRRect(
            borderRadius: BorderRadius.circular(12),
            child: FlutterMap(
              options: mapOptions,
              children: [
                TileLayer(
                  urlTemplate: _osmTemplate,
                  userAgentPackageName: 'mobile_emergencias',
                ),
                if (routeEnd != null)
                  PolylineLayer(
                    polylines: [
                      Polyline(
                        points: [point, routeEnd],
                        strokeWidth: 4,
                        color: const Color(0xFF1565C0).withValues(alpha: 0.85),
                      ),
                    ],
                  ),
                MarkerLayer(markers: markers),
              ],
            ),
          ),
        ),
        const SizedBox(height: 4),
        Text(
          routeEnd != null
              ? 'Línea aproximada entre puntos (no sigue calles). Mapa © OpenStreetMap'
              : 'Mapa © colaboradores de OpenStreetMap',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }
}
