import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';
import 'package:go_router/go_router.dart';
import 'package:permission_handler/permission_handler.dart';

import '../../application/tecnico_emergencias_providers.dart';

/// Envía la posición GPS actual al servidor para que el cliente pueda verla en seguimiento.
class TecnicoServicioCompartirUbicacionScreen extends ConsumerStatefulWidget {
  const TecnicoServicioCompartirUbicacionScreen({super.key, required this.solicitudId});

  final int solicitudId;

  @override
  ConsumerState<TecnicoServicioCompartirUbicacionScreen> createState() => _TecnicoServicioCompartirUbicacionScreenState();
}

class _TecnicoServicioCompartirUbicacionScreenState extends ConsumerState<TecnicoServicioCompartirUbicacionScreen> {
  bool _busy = false;
  String? _error;

  void _toast(String message) {
    if (!mounted) return;
    final m = ScaffoldMessenger.maybeOf(context);
    if (m == null) return;
    m.hideCurrentSnackBar();
    m.showSnackBar(SnackBar(content: Text(message)));
  }

  Future<bool> _ensureLocationReady() async {
    final svc = await Geolocator.isLocationServiceEnabled();
    if (!svc) {
      _toast('Activá el servicio de ubicación del dispositivo.');
      return false;
    }
    var perm = await Permission.locationWhenInUse.request();
    if (!perm.isGranted) {
      perm = await Permission.location.request();
    }
    if (!perm.isGranted) {
      _toast('Se necesita permiso de ubicación.');
      return false;
    }
    return true;
  }

  Future<void> _enviar() async {
    if (_busy) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      if (!await _ensureLocationReady()) return;
      final p = await Geolocator.getCurrentPosition();
      final repo = ref.read(tecnicoEmergenciasRepositoryProvider);
      await repo.compartirUbicacionTecnico(
        widget.solicitudId,
        latitud: p.latitude,
        longitud: p.longitude,
        precisionMetros: p.accuracy.isFinite ? p.accuracy : null,
      );
      if (!mounted) return;
      _toast('Ubicación compartida con el cliente.');
      context.pop();
    } catch (e) {
      setState(() => _error = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Compartir mi ubicación'),
        leading: BackButton(onPressed: () => context.pop()),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 28),
        children: [
          Text(
            'El cliente podrá ver tu última posición en la pantalla de seguimiento de la solicitud '
            '#${widget.solicitudId}. Podés volver a enviar cuando te muevas.',
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(height: 1.4),
          ),
          if (_error != null) ...[
            const SizedBox(height: 16),
            Text(_error!, style: TextStyle(color: scheme.error, height: 1.35)),
          ],
          const SizedBox(height: 28),
          FilledButton.icon(
            onPressed: _busy ? null : _enviar,
            icon: _busy
                ? SizedBox(
                    width: 22,
                    height: 22,
                    child: CircularProgressIndicator(strokeWidth: 2, color: scheme.onPrimary),
                  )
                : const Icon(Icons.my_location_rounded, size: 22),
            label: Padding(
              padding: const EdgeInsets.symmetric(vertical: 14),
              child: Text(
                _busy ? 'Enviando…' : 'Enviar ubicación actual',
                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
