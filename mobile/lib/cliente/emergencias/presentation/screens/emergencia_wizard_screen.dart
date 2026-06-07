// Asistente CU11–CU15: crear solicitud, ubicación, foto, audio, texto y confirmación.
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:path_provider/path_provider.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:record/record.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../../../core/network/api_error.dart';
import '../../../../core/services/offline_emergencia_providers.dart';
import '../../../../core/services/offline_emergencia_queue.dart';
import '../../../../core/services/offline_emergencia_storage.dart';
import '../../../../core/utils/geolocation_helper.dart';
import '../../../application/vehiculos_providers.dart';
import '../../application/emergencias_providers.dart';
import '../../data/ai_transcribe_repository.dart';
import '../../data/emergencias_repository.dart';
import '../../domain/audio_transcribe_models.dart';
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

enum _AudioRecordingTarget { none, descripcion, evidencia }

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
  String? _busyLabel;
  String? _error;

  bool _offlineMode = false;
  late final String _clientUuid = newClientUuid();
  Map<String, dynamic>? _offlineUbicacion;
  final List<OfflineEvidenciaPendiente> _offlineEvidencias = [];

  /// Context bajo el `body` del [Scaffold] (tiene [ScaffoldMessenger] correcto con shell + go_router).
  BuildContext? _scaffoldBodyContext;

  final _descInicial = TextEditingController();
  final _urlFotoManual = TextEditingController();
  final _urlAudioManual = TextEditingController();
  final _textoAdicional = TextEditingController();

  final _picker = ImagePicker();
  final _recorder = AudioRecorder();
  _AudioRecordingTarget _recordingTarget = _AudioRecordingTarget.none;
  String? _ultimaTranscripcion;
  double? _ultimaConfianzaTranscripcion;

  bool get _recording => _recordingTarget != _AudioRecordingTarget.none;

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

  AiTranscribeRepository get _transcribeRepo => ref.read(aiTranscribeRepositoryProvider);

  OfflineEmergenciaQueue get _queue => ref.read(offlineEmergenciaQueueProvider);

  Future<void> _persistOfflineDraft({bool completado = false}) async {
    final t = _descInicial.text.trim();
    final extra = _textoAdicional.text.trim();
    await _queue.upsert(
      OfflineEmergenciaDraft(
        clientUuid: _clientUuid,
        vehiculoId: widget.vehiculoId,
        descripcionTexto: t.isEmpty ? null : t,
        ubicacionInicial: _offlineUbicacion,
        textoAdicional: extra.isEmpty ? null : extra,
        evidenciasPendientes: List.of(_offlineEvidencias),
        solicitudIdRemota: _solicitudId,
        wizardCompletado: completado,
        registradoLocalEn: DateTime.now().toUtc().toIso8601String(),
      ),
    );
    ref.invalidate(offlineEmergenciaPendingProvider);
  }

  void _enterOfflineMode(String message) {
    setState(() => _offlineMode = true);
    _toast(message);
  }

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

  Future<void> _guard(Future<void> Function() fn, {String? busyLabel}) async {
    setState(() {
      _busy = true;
      _busyLabel = busyLabel;
      _error = null;
    });
    try {
      await fn();
    } catch (e) {
      setState(() => _error = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) {
        setState(() {
          _busy = false;
          _busyLabel = null;
        });
      }
    }
  }

  Future<bool> _ensureMicrophoneReady() async {
    final mic = await Permission.microphone.request();
    if (!mic.isGranted && mounted) {
      _toast('Se necesita permiso de micrófono.');
      return false;
    }
    if (!await _recorder.hasPermission()) {
      if (mounted) _toast('No se pudo acceder al micrófono.');
      return false;
    }
    return true;
  }

  Future<AudioTranscribeResult?> _transcribirArchivoLocal({
    required String path,
    required String filename,
    required String mime,
  }) async {
    if (_offlineMode) {
      _toast('La transcripción por voz requiere conexión a internet.');
      return null;
    }
    try {
      return await _transcribeRepo.transcribeFile(
        filePath: path,
        filename: filename,
        mimeType: mime,
      );
    } on DioException catch (e) {
      if (isNetworkFailure(e)) {
        _toast('Sin conexión: no se pudo transcribir el audio.');
      } else {
        _toast('No se pudo transcribir: ${messageFromDio(e)}');
      }
      return null;
    } catch (e) {
      _toast('No se pudo transcribir: ${e.toString().replaceFirst('Exception: ', '')}');
      return null;
    }
  }

  void _aplicarTranscripcion(String text, {required bool soloDescripcionInicial}) {
    final t = text.trim();
    if (t.isEmpty) return;
    if (soloDescripcionInicial || _descInicial.text.trim().isEmpty) {
      _descInicial.text = t;
    } else {
      final prev = _textoAdicional.text.trim();
      _textoAdicional.text = prev.isEmpty ? t : '$prev\n\n$t';
    }
    setState(() {
      _ultimaTranscripcion = t;
    });
  }

  Widget _buildTranscripcionCard(BuildContext context) {
    final t = _ultimaTranscripcion;
    if (t == null || t.isEmpty) return const SizedBox.shrink();
    final conf = _ultimaConfianzaTranscripcion;
    return Card(
      margin: const EdgeInsets.only(top: 16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.record_voice_over_outlined, color: Theme.of(context).colorScheme.primary),
                const SizedBox(width: 8),
                Text('Transcripción del audio', style: Theme.of(context).textTheme.titleSmall),
              ],
            ),
            if (conf != null) ...[
              const SizedBox(height: 4),
              Text(
                'Confianza: ${(conf * 100).toStringAsFixed(0)}%',
                style: Theme.of(context).textTheme.labelSmall,
              ),
            ],
            const SizedBox(height: 8),
            Text(t),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                ShadButton.outline(
                  onPressed: _busy
                      ? null
                      : () {
                          _descInicial.text = t;
                          _toast('Texto copiado a la descripción inicial.');
                        },
                  child: const Text('Usar como descripción'),
                ),
                if (_step >= 4)
                  ShadButton.outline(
                    onPressed: _busy
                        ? null
                        : () {
                            _textoAdicional.text = t;
                            _toast('Texto copiado al detalle adicional.');
                          },
                    child: const Text('Usar como detalle'),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _iniciarGrabacion(_AudioRecordingTarget target) async {
    if (_recording || _busy) return;
    if (!await _ensureMicrophoneReady()) return;
    final dir = await getTemporaryDirectory();
    final prefix = target == _AudioRecordingTarget.descripcion ? 'em_desc' : 'em_audio';
    final path = '${dir.path}/${prefix}_${DateTime.now().millisecondsSinceEpoch}.m4a';
    await _recorder.start(const RecordConfig(encoder: AudioEncoder.aacLc), path: path);
    if (!mounted) return;
    setState(() => _recordingTarget = target);
    _toast(
      target == _AudioRecordingTarget.descripcion
          ? 'Grabando descripción… tocá de nuevo para transcribir.'
          : 'Grabando… tocá de nuevo para transcribir y subir.',
    );
  }

  Future<void> _finalizarGrabacionDescripcion() async {
    final path = await _recorder.stop();
    if (!mounted) return;
    setState(() => _recordingTarget = _AudioRecordingTarget.none);
    if (path == null || path.isEmpty) return;

    await _guard(() async {
      final result = await _transcribirArchivoLocal(
        path: path,
        filename: 'descripcion.m4a',
        mime: 'audio/mp4',
      );
      if (result == null || !mounted) return;
      final text = result.transcripcion;
      if (text.isEmpty) {
        _toast('No se detectó voz en el audio.');
        return;
      }
      setState(() => _ultimaConfianzaTranscripcion = result.confianza);
      _aplicarTranscripcion(text, soloDescripcionInicial: true);
      _toast('Descripción transcrita. Podés editarla antes de crear la solicitud.');
    }, busyLabel: 'Transcribiendo audio…');
  }

  Future<void> _grabarDescripcionPorVoz() async {
    if (_recordingTarget == _AudioRecordingTarget.descripcion) {
      await _finalizarGrabacionDescripcion();
      return;
    }
    if (_recording) return;
    await _iniciarGrabacion(_AudioRecordingTarget.descripcion);
  }

  Future<void> _crearSolicitud() async {
    final t = _descInicial.text.trim();
    await _guard(() async {
      try {
        final d = await _repo.create(
          vehiculoId: widget.vehiculoId,
          descripcionTexto: t.isEmpty ? null : t,
        );
        if (!mounted) return;
        setState(() {
          _solicitudId = d.id;
          _detail = d;
          _step = 1;
        });
      } on DioException catch (e) {
        if (!isNetworkFailure(e)) rethrow;
        _enterOfflineMode(
          'Sin conexión: continuá el reporte offline. Se enviará al reconectar.',
        );
        await _persistOfflineDraft();
        if (!mounted) return;
        setState(() => _step = 1);
      }
    });
  }

  Future<void> _enviarUbicacion() async {
    final sid = _solicitudId;
    if (sid == null && !_offlineMode) return;
    if (!await _ensureLocationReady()) return;

    await _guard(() async {
      final p = await obtainDevicePosition();
      final payload = {
        'latitud': p.latitude,
        'longitud': p.longitude,
        if (p.accuracy.isFinite) 'precision_metros': p.accuracy,
        'es_actual': true,
      };

      if (_offlineMode) {
        _offlineUbicacion = payload;
        await _persistOfflineDraft();
        if (!mounted) return;
        setState(() {
          _step = 2;
          _mapPreviewLat = null;
          _mapPreviewLng = null;
        });
        _toast('Ubicación guardada localmente.');
        return;
      }

      try {
        final d = await _repo.postUbicacion(
          sid!,
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
      } on DioException catch (e) {
        if (!isNetworkFailure(e)) rethrow;
        _offlineUbicacion = payload;
        _enterOfflineMode('Sin conexión: ubicación guardada localmente.');
        await _persistOfflineDraft();
        if (!mounted) return;
        setState(() {
          _step = 2;
          _mapPreviewLat = null;
          _mapPreviewLng = null;
        });
      }
    }, busyLabel: 'Obteniendo GPS y enviando…');
  }

  Future<void> _verPosicionEnMapaSinEnviar() async {
    if (!await _ensureLocationReady()) return;
    await _guard(() async {
      final p = await obtainDevicePosition();
      if (!mounted) return;
      setState(() {
        _mapPreviewLat = p.latitude;
        _mapPreviewLng = p.longitude;
      });
      _toast(
        'Vista previa en mapa (no enviada). Coordenadas: '
        '${p.latitude.toStringAsFixed(5)}, ${p.longitude.toStringAsFixed(5)}.',
      );
    }, busyLabel: 'Obteniendo GPS…');
  }

  Future<void> _omitirUbicacion() async {
    if (_offlineMode) await _persistOfflineDraft();
    setState(() => _step = 2);
  }

  Future<void> _adjuntarFotoDesdeGaleria() async {
    final sid = _solicitudId;
    if (sid == null && !_offlineMode) return;
    final perm = await Permission.photos.request();
    if (!perm.isGranted) {
      await Permission.storage.request();
    }
    final x = await _picker.pickImage(
      source: ImageSource.gallery,
      imageQuality: 80,
      maxWidth: 1920,
      maxHeight: 1920,
    );
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
    if (sid == null && !_offlineMode) return;
    final cam = await Permission.camera.request();
    if (!cam.isGranted && mounted) {
      _toast('Se necesita permiso de cámara.');
      return;
    }
    final x = await _picker.pickImage(
      source: ImageSource.camera,
      imageQuality: 80,
      maxWidth: 1920,
      maxHeight: 1920,
    );
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
    required int? sid,
    required String tipoApi,
    required String path,
    required String mime,
    required String nombre,
  }) async {
    if (_offlineMode || sid == null) {
      await _guard(() async {
        final persistent = await OfflineEmergenciaStorage.copyEvidenceFile(
          clientUuid: _clientUuid,
          sourcePath: path,
          filename: nombre.isNotEmpty ? nombre : 'evidencia.dat',
        );
        _offlineEvidencias.add(
          OfflineEvidenciaPendiente(
            tipo: tipoApi,
            localPath: persistent,
            filename: nombre.isNotEmpty ? nombre : 'evidencia.dat',
            mimeType: mime == 'application/octet-stream' ? null : mime,
          ),
        );
        await _persistOfflineDraft();
        if (!mounted) return;
        setState(() => _step = tipoApi == 'FOTO' ? 3 : 4);
        _toast('Evidencia guardada localmente.');
      });
      return;
    }

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
        _step = tipoApi == 'FOTO' ? 3 : 4;
      });
      _toast(tipoApi == 'FOTO' ? 'Foto registrada.' : 'Audio registrado.');
    });
  }

  Future<void> _grabarAudio() async {
    final sid = _solicitudId;
    if (sid == null && !_offlineMode) return;

    if (_recordingTarget == _AudioRecordingTarget.evidencia) {
      final path = await _recorder.stop();
      if (!mounted) return;
      setState(() => _recordingTarget = _AudioRecordingTarget.none);
      if (path == null || path.isEmpty) return;

      if (!_offlineMode) {
        setState(() {
          _busy = true;
          _busyLabel = 'Transcribiendo audio…';
          _error = null;
        });
        try {
          final result = await _transcribirArchivoLocal(
            path: path,
            filename: 'grabacion.m4a',
            mime: 'audio/mp4',
          );
          if (result != null && mounted) {
            final text = result.transcripcion;
            if (text.isNotEmpty) {
              setState(() => _ultimaConfianzaTranscripcion = result.confianza);
              _aplicarTranscripcion(text, soloDescripcionInicial: false);
            }
          }
        } finally {
          if (mounted) {
            setState(() {
              _busy = false;
              _busyLabel = null;
            });
          }
        }
      }

      await _procesarArchivoEvidencia(
        sid: sid,
        tipoApi: 'AUDIO',
        path: path,
        mime: 'audio/mp4',
        nombre: 'grabacion.m4a',
      );
      return;
    }

    if (_recording) return;
    await _iniciarGrabacion(_AudioRecordingTarget.evidencia);
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
    if (_offlineMode || sid == null) {
      await _guard(() async {
        await _persistOfflineDraft(completado: true);
        if (!mounted) return;
        setState(() => _step = 5);
        _toast('Reporte offline completo. Se sincronizará al reconectar.');
      });
      return;
    }
    final t = _textoAdicional.text.trim();
    await _guard(() async {
      final d = await _repo.patchTexto(sid, descripcionTexto: t.isEmpty ? null : t);
      setState(() {
        _detail = d;
        _step = 5;
      });
    });
  }

  Future<void> _omitirFoto() async {
    if (_offlineMode) await _persistOfflineDraft();
    setState(() => _step = 3);
  }

  Future<void> _omitirAudio() async {
    if (_offlineMode) await _persistOfflineDraft();
    setState(() => _step = 4);
  }

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
        actions: [
          if (_offlineMode)
            const Padding(
              padding: EdgeInsets.only(right: 12),
              child: Chip(
                avatar: Icon(Icons.cloud_off, size: 18),
                label: Text('Offline'),
              ),
            ),
        ],
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
                ColoredBox(
                  color: const Color(0x66000000),
                  child: Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const CircularProgressIndicator(),
                        if (_busyLabel != null) ...[
                          const SizedBox(height: 16),
                          Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 24),
                            child: Text(
                              _busyLabel!,
                              textAlign: TextAlign.center,
                              style: const TextStyle(color: Colors.white),
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
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
            'Vehículo $placa. Describí lo que ocurre escribiendo o grabando un audio '
            '(se transcribe automáticamente a texto). Luego se creará la solicitud.',
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
          const SizedBox(height: 16),
          const Divider(),
          const SizedBox(height: 8),
          Text(
            _recordingTarget == _AudioRecordingTarget.descripcion
                ? 'Grabando… tocá «Detener y transcribir» para convertir a texto.'
                : 'O grabá tu relato: el audio se convierte en texto editable.',
            style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant),
          ),
          const SizedBox(height: 12),
          ShadButton.outline(
            onPressed: _busy ? null : _grabarDescripcionPorVoz,
            child: Text(
              _recordingTarget == _AudioRecordingTarget.descripcion
                  ? 'Detener y transcribir'
                  : 'Grabar descripción por voz',
            ),
          ),
          _buildTranscripcionCard(context),
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
            _recordingTarget == _AudioRecordingTarget.evidencia
                ? 'Grabando… tocá «Detener, transcribir y subir» para finalizar.'
                : 'Grabá un audio: se transcribe a texto y se sube como evidencia. '
                    'El texto se agrega al relato si aún no completaste el paso 5.',
            style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant),
          ),
          const SizedBox(height: 16),
          ShadButton(
            onPressed: _busy ? null : _grabarAudio,
            child: Text(
              _recordingTarget == _AudioRecordingTarget.evidencia
                  ? 'Detener, transcribir y subir'
                  : 'Grabar audio',
            ),
          ),
          _buildTranscripcionCard(context),
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
            'Completá o ajustá el relato. Si transcribiste audio antes, el texto ya puede estar aquí.',
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
          _buildTranscripcionCard(context),
          const SizedBox(height: 20),
          ShadButton(onPressed: _busy ? null : _guardarTextoAdicional, child: const Text('Guardar y continuar')),
        ];
      case 5:
      default:
        if (_offlineMode) {
          return [
            Icon(Icons.cloud_off_outlined, size: 56, color: Theme.of(context).colorScheme.tertiary),
            const SizedBox(height: 12),
            Text('Reporte guardado offline', style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 8),
            Text(
              'Referencia local: ${_clientUuid.substring(0, 8)}…',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            Text(
              'Ubicación: ${_offlineUbicacion != null ? "incluida" : "omitida"} · '
              'Evidencias: ${_offlineEvidencias.length}',
            ),
            const SizedBox(height: 8),
            Text(
              'Al reconectar, la app enviará este reporte automáticamente.',
              style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant),
            ),
            const SizedBox(height: 24),
            ShadButton(
              onPressed: () => context.go('/cliente/app/home'),
              child: const Text('Volver al inicio'),
            ),
            const SizedBox(height: 12),
            ShadButton.outline(
              onPressed: () async {
                final r = await ref.read(offlineEmergenciaSyncProvider)();
                if (!context.mounted) return;
                if (r.synced > 0) {
                  _toast('${r.synced} reporte(s) sincronizado(s).');
                  context.go('/cliente/app/emergencias/solicitudes');
                } else if (r.failed > 0) {
                  _toast(r.errors.isEmpty ? 'Error al sincronizar' : r.errors.first);
                } else {
                  _toast('Sin conexión con el servidor.');
                }
              },
              child: const Text('Sincronizar ahora'),
            ),
          ];
        }
        final d = _detail;
        final uFin = d?.ubicaciones.isNotEmpty == true ? d!.ubicaciones.last : null;
        return [
          Icon(Icons.check_circle_outline, size: 56, color: Theme.of(context).colorScheme.primary),
          const SizedBox(height: 12),
          Text('Solicitud registrada', style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 8),
          Text(
            'Los talleres cercanos enviarán cotizaciones con precio, servicios y distancia. '
            'Compará opciones y elegí la que prefieras.',
            style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant),
          ),
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
            ShadButton(
              onPressed: () => context.push('/cliente/app/emergencias/solicitudes/${d.id}/cotizaciones'),
              child: const Text('Ver cotizaciones de talleres'),
            ),
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
