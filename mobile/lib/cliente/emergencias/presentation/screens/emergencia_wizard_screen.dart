// Asistente CU11–CU15: crear solicitud, ubicación, foto, audio, texto y confirmación.
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:path_provider/path_provider.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:record/record.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../../application/vehiculos_providers.dart';
import '../../application/emergencias_providers.dart';
import '../../data/emergencias_repository.dart';
import '../../domain/solicitud_emergencia_models.dart';
import '../widgets/emergencia_ubicacion_osm_map.dart';

String _mimeFromPath(String path) {
  final e = path.split('.').last.toLowerCase();
  return switch (e) {
    'jpg' || 'jpeg' => 'image/jpeg',
    'png' => 'image/png',
    'webp' => 'image/webp',
    'm4a' => 'audio/mp4',
    'aac' => 'audio/aac',
    _ => 'application/octet-stream',
  };
}

class EmergenciaWizardScreen extends ConsumerStatefulWidget {
  const EmergenciaWizardScreen({super.key, required this.vehiculoId});

  final int vehiculoId;

  @override
  ConsumerState<EmergenciaWizardScreen> createState() => _EmergenciaWizardScreenState();
}

class _EmergenciaWizardScreenState extends ConsumerState<EmergenciaWizardScreen> {
  static const _totalSteps = 6;

  int _step = 0;
  int? _solicitudId;
  SolicitudEmergenciaDetail? _detail;
  bool _busy = false;
  String? _error;

  /// Context bajo el `body` del [Scaffold] (tiene [ScaffoldMessenger] correcto con shell + go_router).
  BuildContext? _scaffoldBodyContext;

  final _descInicial = TextEditingController();
  final _urlFotoManual = TextEditingController();
  final _urlAudioManual = TextEditingController();
  final _textoAdicional = TextEditingController();

  final _picker = ImagePicker();
  final _recorder = AudioRecorder();
  bool _recording = false;

  /// Solo vista previa local (paso ubicación); no implica envío al API.
  double? _mapPreviewLat;
  double? _mapPreviewLng;

  SolicitudUbicacionRead? get _ultimaUbicacionRegistrada {
    final list = _detail?.ubicaciones;
    if (list == null || list.isEmpty) return null;
    return list.last;
  }

  @override
  void dispose() {
    _descInicial.dispose();
    _urlFotoManual.dispose();
    _urlAudioManual.dispose();
    _textoAdicional.dispose();
    _recorder.dispose();
    super.dispose();
  }

  EmergenciasRepository get _repo => ref.read(emergenciasRepositoryProvider);

  Future<bool> _ensureLocationReady() async {
    final svc = await Geolocator.isLocationServiceEnabled();
    if (!svc) {
      if (mounted) _toast('Activá el servicio de ubicación del dispositivo.');
      return false;
    }
    var perm = await Permission.locationWhenInUse.request();
    if (!perm.isGranted) {
      perm = await Permission.location.request();
    }
    if (!perm.isGranted) {
      if (mounted) _toast('Se necesita permiso de ubicación.');
      return false;
    }
    return true;
  }

  void _toast(String message) {
    final c = _scaffoldBodyContext;
    if (!mounted || c == null) return;
    final m = ScaffoldMessenger.maybeOf(c);
    if (m == null) return;
    m.hideCurrentSnackBar();
    m.showSnackBar(SnackBar(content: Text(message)));
  }

  Future<void> _guard(Future<void> Function() fn) async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await fn();
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _crearSolicitud() async {
    final t = _descInicial.text.trim();
    await _guard(() async {
      final d = await _repo.create(
        vehiculoId: widget.vehiculoId,
        descripcionTexto: t.isEmpty ? null : t,
      );
      setState(() {
        _solicitudId = d.id;
        _detail = d;
        _step = 1;
      });
    });
  }

  Future<void> _enviarUbicacion() async {
    final sid = _solicitudId;
    if (sid == null) return;
    if (!await _ensureLocationReady()) return;

    await _guard(() async {
      final p = await Geolocator.getCurrentPosition();
      final d = await _repo.postUbicacion(
        sid,
        latitud: p.latitude,
        longitud: p.longitude,
        precisionMetros: p.accuracy.isFinite ? p.accuracy : null,
        esActual: true,
      );
      if (!mounted) return;
      setState(() {
        _detail = d;
        _step = 2;
        _mapPreviewLat = null;
        _mapPreviewLng = null;
      });
      _toast(
        'Ubicación enviada (${p.latitude.toStringAsFixed(5)}, ${p.longitude.toStringAsFixed(5)}). '
        'En el servidor hay ${d.ubicaciones.length} registro(s) de ubicación.',
      );
    });
  }

  Future<void> _verPosicionEnMapaSinEnviar() async {
    if (!await _ensureLocationReady()) return;
    await _guard(() async {
      final p = await Geolocator.getCurrentPosition();
      if (!mounted) return;
      setState(() {
        _mapPreviewLat = p.latitude;
        _mapPreviewLng = p.longitude;
      });
      _toast(
        'Vista previa en mapa (no enviada). Coordenadas: '
        '${p.latitude.toStringAsFixed(5)}, ${p.longitude.toStringAsFixed(5)}.',
      );
    });
  }

  Future<void> _omitirUbicacion() async {
    setState(() => _step = 2);
  }

  Future<void> _adjuntarFotoDesdeGaleria() async {
    final sid = _solicitudId;
    if (sid == null) return;
    final perm = await Permission.photos.request();
    if (!perm.isGranted) {
      await Permission.storage.request();
    }
    final x = await _picker.pickImage(source: ImageSource.gallery, imageQuality: 85);
    if (x == null) return;
    await _procesarArchivoEvidencia(
      sid: sid,
      tipoApi: 'FOTO',
      path: x.path,
      mime: _mimeFromPath(x.path),
      nombre: x.name,
    );
  }

  Future<void> _tomarFotoCamara() async {
    final sid = _solicitudId;
    if (sid == null) return;
    final cam = await Permission.camera.request();
    if (!cam.isGranted && mounted) {
      _toast('Se necesita permiso de cámara.');
      return;
    }
    final x = await _picker.pickImage(source: ImageSource.camera, imageQuality: 85);
    if (x == null) return;
    await _procesarArchivoEvidencia(
      sid: sid,
      tipoApi: 'FOTO',
      path: x.path,
      mime: _mimeFromPath(x.path),
      nombre: x.name,
    );
  }

  Future<void> _procesarArchivoEvidencia({
    required int sid,
    required String tipoApi,
    required String path,
    required String mime,
    required String nombre,
  }) async {
    await _guard(() async {
      final d = await _repo.postEvidenciaArchivo(
        sid,
        tipoApi: tipoApi,
        filePath: path,
        filename: nombre.isNotEmpty ? nombre : 'foto.jpg',
        mimeType: mime == 'application/octet-stream' ? null : mime,
      );
      if (!mounted) return;
      setState(() {
        _detail = d;
        _step = 3;
      });
      _toast('Foto registrada.');
    });
  }

  Future<void> _grabarAudio() async {
    final sid = _solicitudId;
    if (sid == null) return;
    final mic = await Permission.microphone.request();
    if (!mic.isGranted && mounted) {
      _toast('Se necesita permiso de micrófono.');
      return;
    }
    if (!_recording) {
      final dir = await getTemporaryDirectory();
      final path = '${dir.path}/em_audio_${DateTime.now().millisecondsSinceEpoch}.m4a';
      if (await _recorder.hasPermission()) {
        await _recorder.start(const RecordConfig(encoder: AudioEncoder.aacLc), path: path);
        setState(() => _recording = true);
        if (mounted) {
          _toast('Grabando… tocá de nuevo para detener.');
        }
      }
      return;
    }

    final path = await _recorder.stop();
    setState(() => _recording = false);
    if (path == null || path.isEmpty) return;
    await _guard(() async {
      final d = await _repo.postEvidenciaArchivo(
        sid,
        tipoApi: 'AUDIO',
        filePath: path,
        filename: 'grabacion.m4a',
        mimeType: 'audio/mp4',
      );
      if (!mounted) return;
      setState(() {
        _detail = d;
        _step = 4;
      });
      _toast('Audio registrado.');
    });
  }

  Future<void> _enviarFotoPorUrlManual() async {
    final sid = _solicitudId;
    if (sid == null) return;
    final raw = _urlFotoManual.text.trim();
    if (!raw.toLowerCase().startsWith('https://')) {
      setState(() => _error = 'La URL debe comenzar con https://');
      return;
    }
    await _guard(() async {
      final d = await _repo.postEvidencia(
        sid,
        tipoApi: 'FOTO',
        archivoUrl: raw,
        mimeType: 'image/jpeg',
        nombreArchivo: 'evidencia.jpg',
      );
      setState(() {
        _detail = d;
        _step = 3;
      });
    });
  }

  Future<void> _enviarAudioPorUrlManual() async {
    final sid = _solicitudId;
    if (sid == null) return;
    final raw = _urlAudioManual.text.trim();
    if (!raw.toLowerCase().startsWith('https://')) {
      setState(() => _error = 'La URL debe comenzar con https://');
      return;
    }
    await _guard(() async {
      final d = await _repo.postEvidencia(
        sid,
        tipoApi: 'AUDIO',
        archivoUrl: raw,
        mimeType: 'audio/mp4',
        nombreArchivo: 'evidencia.m4a',
      );
      setState(() {
        _detail = d;
        _step = 4;
      });
    });
  }

  Future<void> _guardarTextoAdicional() async {
    final sid = _solicitudId;
    if (sid == null) return;
    final t = _textoAdicional.text.trim();
    await _guard(() async {
      final d = await _repo.patchTexto(sid, descripcionTexto: t.isEmpty ? null : t);
      setState(() {
        _detail = d;
        _step = 5;
      });
    });
  }

  Future<void> _omitirFoto() async => setState(() => _step = 3);
  Future<void> _omitirAudio() async => setState(() => _step = 4);

  @override
  Widget build(BuildContext context) {
    final vehiculos = ref.watch(vehiculosMineProvider);
    final placa = vehiculos.maybeWhen(
      data: (list) {
        try {
          return list.firstWhere((e) => e.id == widget.vehiculoId).placa;
        } catch (_) {
          return 'Vehículo #${widget.vehiculoId}';
        }
      },
      orElse: () => 'Vehículo #${widget.vehiculoId}',
    );

    return Scaffold(
      appBar: AppBar(
        title: Text('Emergencia · $placa'),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => context.canPop() ? context.pop() : context.go('/cliente/app/emergencias'),
        ),
      ),
      body: Builder(
        builder: (bodyContext) {
          _scaffoldBodyContext = bodyContext;
          return Stack(
            children: [
              ListView(
                padding: const EdgeInsets.all(20),
                children: [
                  _StepIndicator(step: _step, total: _totalSteps),
                  const SizedBox(height: 20),
                  if (_error != null)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: Text(_error!, style: TextStyle(color: Theme.of(bodyContext).colorScheme.error)),
                    ),
                  ..._buildStepContent(bodyContext, placa),
                ],
              ),
              if (_busy)
                const ColoredBox(
                  color: Color(0x66000000),
                  child: Center(child: CircularProgressIndicator()),
                ),
            ],
          );
        },
      ),
    );
  }

  List<Widget> _buildStepContent(BuildContext context, String placa) {
    switch (_step) {
      case 0:
        return [
          Text('Paso 1 — Inicio del reporte', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          Text(
            'Vehículo $placa. Podés describir lo que ocurre (opcional). Luego se creará la solicitud en el servidor.',
            style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _descInicial,
            maxLines: 4,
            decoration: const InputDecoration(
              labelText: 'Descripción inicial',
              border: OutlineInputBorder(),
              alignLabelWithHint: true,
            ),
          ),
          const SizedBox(height: 20),
          ShadButton(onPressed: _busy ? null : _crearSolicitud, child: const Text('Crear solicitud de emergencia')),
        ];
      case 1:
        return [
          Text('Paso 2 — Ubicación', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          Text(
            'Enviá tu posición al servidor. «Ver en mapa» usa OpenStreetMap solo en el teléfono; '
            'el envío real ocurre con «Enviar ubicación actual» (respuesta 200 y contador en el aviso).',
            style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant),
          ),
          const SizedBox(height: 16),
          if (_mapPreviewLat != null && _mapPreviewLng != null) ...[
            EmergenciaUbicacionOsmMap(latitude: _mapPreviewLat!, longitude: _mapPreviewLng!),
            const SizedBox(height: 16),
          ],
          ShadButton(onPressed: _busy ? null : _enviarUbicacion, child: const Text('Enviar ubicación actual')),
          const SizedBox(height: 12),
          ShadButton.outline(
            onPressed: _busy ? null : _verPosicionEnMapaSinEnviar,
            child: const Text('Ver en mapa (sin enviar)'),
          ),
          const SizedBox(height: 12),
          ShadButton.outline(onPressed: _busy ? null : _omitirUbicacion, child: const Text('Omitir por ahora')),
        ];
      case 2:
        final uReg = _ultimaUbicacionRegistrada;
        return [
          Text('Paso 3 — Foto', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          Text(
            'Elegí de la galería o sacá una foto: se sube al servidor y queda asociada a la solicitud. '
            'Si ya tenés la imagen en un bucket, podés pegar una URL HTTPS abajo.',
            style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant),
          ),
          if (uReg != null) ...[
            const SizedBox(height: 16),
            Text(
              'Ubicación ya registrada en esta solicitud: '
              '${uReg.latitud.toStringAsFixed(6)}, ${uReg.longitud.toStringAsFixed(6)}',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: 12),
            EmergenciaUbicacionOsmMap(latitude: uReg.latitud, longitude: uReg.longitud, height: 200),
          ],
          const SizedBox(height: 16),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              ShadButton(onPressed: _busy ? null : _adjuntarFotoDesdeGaleria, child: const Text('Galería')),
              ShadButton.outline(onPressed: _busy ? null : _tomarFotoCamara, child: const Text('Cámara')),
            ],
          ),
          const SizedBox(height: 20),
          TextField(
            controller: _urlFotoManual,
            decoration: const InputDecoration(
              labelText: 'O pegá URL HTTPS',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
          ShadButton.outline(
            onPressed: _busy ? null : _enviarFotoPorUrlManual,
            child: const Text('Registrar foto por URL'),
          ),
          const SizedBox(height: 12),
          ShadButton.ghost(onPressed: _busy ? null : _omitirFoto, child: const Text('Omitir foto')),
        ];
      case 3:
        return [
          Text('Paso 4 — Audio', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          Text(
            _recording
                ? 'Grabando… tocá «Detener y subir» para finalizar.'
                : 'Tocá «Grabar» para iniciar; tocá de nuevo para detener y subir el audio al servidor.',
            style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant),
          ),
          const SizedBox(height: 16),
          ShadButton(
            onPressed: _busy ? null : _grabarAudio,
            child: Text(_recording ? 'Detener y subir' : 'Grabar audio'),
          ),
          const SizedBox(height: 20),
          TextField(
            controller: _urlAudioManual,
            decoration: const InputDecoration(
              labelText: 'O pegá URL HTTPS del audio',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
          ShadButton.outline(
            onPressed: _busy ? null : _enviarAudioPorUrlManual,
            child: const Text('Registrar audio por URL'),
          ),
          const SizedBox(height: 12),
          ShadButton.ghost(onPressed: _busy ? null : _omitirAudio, child: const Text('Omitir audio')),
        ];
      case 4:
        return [
          Text('Paso 5 — Texto adicional', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          Text(
            'Completá o ajustá el relato. Podés dejar vacío para omitir cambios.',
            style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _textoAdicional,
            maxLines: 5,
            decoration: const InputDecoration(
              labelText: 'Detalle para el taller',
              border: OutlineInputBorder(),
              alignLabelWithHint: true,
            ),
          ),
          const SizedBox(height: 20),
          ShadButton(onPressed: _busy ? null : _guardarTextoAdicional, child: const Text('Guardar y continuar')),
        ];
      case 5:
      default:
        final d = _detail;
        final uFin = d?.ubicaciones.isNotEmpty == true ? d!.ubicaciones.last : null;
        return [
          Icon(Icons.check_circle_outline, size: 56, color: Theme.of(context).colorScheme.primary),
          const SizedBox(height: 12),
          Text('Solicitud registrada', style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 8),
          if (d != null) ...[
            Text('ID solicitud: ${d.id}', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            Text('Estado: ${d.estado.apiValue}'),
            Text('Ubicaciones: ${d.ubicaciones.length} · Evidencias: ${d.evidencias.length}'),
            if (uFin != null) ...[
              const SizedBox(height: 12),
              Text(
                'Última ubicación: ${uFin.latitud.toStringAsFixed(6)}, ${uFin.longitud.toStringAsFixed(6)}',
              ),
              const SizedBox(height: 12),
              EmergenciaUbicacionOsmMap(latitude: uFin.latitud, longitude: uFin.longitud, height: 240),
            ],
          ],
          const SizedBox(height: 24),
          ShadButton(
            onPressed: () => context.go('/cliente/app/home'),
            child: const Text('Volver al inicio'),
          ),
          if (d != null) ...[
            const SizedBox(height: 12),
            ShadButton.outline(
              onPressed: () => context.push('/cliente/app/emergencias/solicitudes/${d.id}/seguimiento'),
              child: const Text('Ver seguimiento'),
            ),
          ],
        ];
    }
  }
}

class _StepIndicator extends StatelessWidget {
  const _StepIndicator({required this.step, required this.total});

  final int step;
  final int total;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Paso ${step + 1} de $total', style: Theme.of(context).textTheme.labelLarge),
        const SizedBox(height: 6),
        LinearProgressIndicator(value: (step + 1) / total),
      ],
    );
  }
}
