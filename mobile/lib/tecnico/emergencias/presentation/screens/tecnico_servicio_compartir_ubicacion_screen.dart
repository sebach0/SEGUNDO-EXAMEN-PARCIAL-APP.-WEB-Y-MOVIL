import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';
import 'package:go_router/go_router.dart';
import 'package:permission_handler/permission_handler.dart';

import '../../../../core/utils/bolivia_time.dart';
import '../../application/tecnico_emergencias_providers.dart';

/// Envía la posición GPS actual al servidor para que el cliente pueda verla en seguimiento.
class TecnicoServicioCompartirUbicacionScreen extends ConsumerStatefulWidget {
  const TecnicoServicioCompartirUbicacionScreen({super.key, required this.solicitudId});

  final int solicitudId;

  @override
  ConsumerState<TecnicoServicioCompartirUbicacionScreen> createState() =>
      _TecnicoServicioCompartirUbicacionScreenState();
}

class _TecnicoServicioCompartirUbicacionScreenState
    extends ConsumerState<TecnicoServicioCompartirUbicacionScreen> {
  bool _busy = false;
  String? _error;
  DateTime? _ultimoEnvio;
  double? _ultimaLatitud;
  double? _ultimaLongitud;

  Future<bool> _ensureLocationPermission() async {
    final svcEnabled = await Geolocator.isLocationServiceEnabled();
    if (!svcEnabled) {
      if (mounted) setState(() => _error = 'Activá el servicio de ubicación del dispositivo.');
      return false;
    }
    var perm = await Permission.locationWhenInUse.request();
    if (!perm.isGranted) perm = await Permission.location.request();
    if (!perm.isGranted) {
      if (mounted) setState(() => _error = 'Se necesita permiso de ubicación para continuar.');
      return false;
    }
    return true;
  }

  /// Obtiene posición usando la siguiente estrategia:
  /// 1. Última posición conocida (instantánea, funciona en emuladores con mock location).
  /// 2. Si no hay, obtiene posición actual con precisión baja (red/WiFi, sin GPS).
  /// 3. Si ambas fallan, lanza excepción con mensaje claro.
  Future<Position> _obtenerPosicion() async {
    // Intento 1: última posición conocida (más rápido, funciona en emuladores)
    final ultima = await Geolocator.getLastKnownPosition();
    if (ultima != null) return ultima;

    // Intento 2: posición actual con precisión baja (red, sin GPS satelital)
    try {
      return await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(accuracy: LocationAccuracy.low),
      ).timeout(
        const Duration(seconds: 15),
        onTimeout: () => throw Exception('timeout'),
      );
    } catch (_) {
      throw Exception(
        'No se pudo obtener la ubicación. '
        'Verificá que el GPS o la red de ubicación esté activada.',
      );
    }
  }

  Future<void> _enviar() async {
    if (_busy) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      if (!await _ensureLocationPermission()) return;

      final p = await _obtenerPosicion();

      final repo = ref.read(tecnicoEmergenciasRepositoryProvider);
      await repo.compartirUbicacionTecnico(
        widget.solicitudId,
        latitud: p.latitude,
        longitud: p.longitude,
        precisionMetros: p.accuracy.isFinite ? p.accuracy : null,
      );

      if (!mounted) return;
      setState(() {
        _ultimoEnvio = DateTime.now();
        _ultimaLatitud = p.latitude;
        _ultimaLongitud = p.longitude;
        _error = null;
      });
    } catch (e) {
      if (mounted) {
        setState(() => _error = e.toString().replaceFirst('Exception: ', ''));
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final textTheme = Theme.of(context).textTheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Compartir ubicación'),
        leading: BackButton(onPressed: () => context.pop()),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 28),
        children: [
          Text(
            'El cliente verá tu posición actualizada en la pantalla de seguimiento '
            'de la solicitud #${widget.solicitudId}. '
            'Podés reenviar cuando te muevas.',
            style: textTheme.bodyLarge?.copyWith(height: 1.4),
          ),

          const SizedBox(height: 24),

          // ── Éxito ──────────────────────────────────────────────────────────
          if (_ultimoEnvio != null) ...[
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: scheme.primaryContainer,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.check_circle_rounded, color: scheme.primary, size: 26),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Ubicación enviada al cliente',
                          style: textTheme.titleSmall?.copyWith(
                            color: scheme.onPrimaryContainer,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'Enviada a las ${BoliviaTime.format(_ultimoEnvio!, pattern: 'HH:mm:ss')}',
                          style: textTheme.bodySmall?.copyWith(
                            color: scheme.onPrimaryContainer,
                          ),
                        ),
                        if (_ultimaLatitud != null && _ultimaLongitud != null) ...[
                          const SizedBox(height: 2),
                          Text(
                            '${_ultimaLatitud!.toStringAsFixed(5)}, '
                            '${_ultimaLongitud!.toStringAsFixed(5)}',
                            style: textTheme.bodySmall?.copyWith(
                              color: scheme.onPrimaryContainer.withOpacity(0.75),
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
          ],

          // ── Error ─────────────────────────────────────────────────────────
          if (_error != null) ...[
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: scheme.errorContainer,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.error_outline_rounded, color: scheme.error, size: 22),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      _error!,
                      style: textTheme.bodyMedium?.copyWith(
                        color: scheme.onErrorContainer,
                        height: 1.35,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
          ],

          // ── Botón ─────────────────────────────────────────────────────────
          FilledButton.icon(
            onPressed: _busy ? null : _enviar,
            icon: _busy
                ? SizedBox(
                    width: 22,
                    height: 22,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: scheme.onPrimary,
                    ),
                  )
                : Icon(
                    _ultimoEnvio != null
                        ? Icons.refresh_rounded
                        : Icons.my_location_rounded,
                    size: 22,
                  ),
            label: Padding(
              padding: const EdgeInsets.symmetric(vertical: 14),
              child: Text(
                _busy
                    ? 'Enviando…'
                    : _ultimoEnvio != null
                        ? 'Actualizar mi ubicación'
                        : 'Enviar mi ubicación al cliente',
                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
