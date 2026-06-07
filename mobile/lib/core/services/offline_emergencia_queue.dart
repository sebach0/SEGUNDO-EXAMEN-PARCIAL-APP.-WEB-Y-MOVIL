// Cola offline de solicitudes de emergencia (SharedPreferences + sync al reconectar).
import 'dart:convert';
import 'dart:io';
import 'dart:math';

import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../cliente/emergencias/data/emergencias_repository.dart';
import '../constants/api_constants.dart';
import '../network/api_error.dart';
import 'offline_emergencia_storage.dart';

const _storageKey = 'emergencias_offline_queue_v2';

enum OfflineSyncEstado { pendiente, enviado, sincronizado, error }

class OfflineEvidenciaPendiente {
  OfflineEvidenciaPendiente({
    required this.tipo,
    required this.localPath,
    required this.filename,
    this.mimeType,
  });

  final String tipo;
  final String localPath;
  final String filename;
  final String? mimeType;

  Map<String, dynamic> toJson() => {
        'tipo': tipo,
        'local_path': localPath,
        'filename': filename,
        if (mimeType != null) 'mime_type': mimeType,
      };

  factory OfflineEvidenciaPendiente.fromJson(Map<String, dynamic> j) {
    return OfflineEvidenciaPendiente(
      tipo: j['tipo'] as String,
      localPath: j['local_path'] as String,
      filename: j['filename'] as String,
      mimeType: j['mime_type'] as String?,
    );
  }
}

class OfflineEmergenciaDraft {
  OfflineEmergenciaDraft({
    required this.clientUuid,
    required this.vehiculoId,
    this.descripcionTexto,
    this.ubicacionInicial,
    this.textoAdicional,
    this.evidenciasPendientes = const [],
    this.solicitudIdRemota,
    this.wizardCompletado = false,
    required this.registradoLocalEn,
    this.estadoLocal = OfflineSyncEstado.pendiente,
    this.ultimoError,
  });

  final String clientUuid;
  final int vehiculoId;
  final String? descripcionTexto;
  final Map<String, dynamic>? ubicacionInicial;
  final String? textoAdicional;
  final List<OfflineEvidenciaPendiente> evidenciasPendientes;
  int? solicitudIdRemota;
  final bool wizardCompletado;
  final String registradoLocalEn;
  OfflineSyncEstado estadoLocal;
  String? ultimoError;

  Map<String, dynamic> toJson() => {
        'client_uuid': clientUuid,
        'vehiculo_id': vehiculoId,
        if (descripcionTexto != null) 'descripcion_texto': descripcionTexto,
        if (ubicacionInicial != null) 'ubicacion_inicial': ubicacionInicial,
        if (textoAdicional != null) 'texto_adicional': textoAdicional,
        'evidencias_pendientes':
            evidenciasPendientes.map((e) => e.toJson()).toList(),
        if (solicitudIdRemota != null) 'solicitud_id_remota': solicitudIdRemota,
        'wizard_completado': wizardCompletado,
        'registrado_local_en': registradoLocalEn,
        'estado_local': estadoLocal.name,
        if (ultimoError != null) 'ultimo_error': ultimoError,
      };

  factory OfflineEmergenciaDraft.fromJson(Map<String, dynamic> j) {
    final evRaw = j['evidencias_pendientes'];
    return OfflineEmergenciaDraft(
      clientUuid: j['client_uuid'] as String,
      vehiculoId: j['vehiculo_id'] as int,
      descripcionTexto: j['descripcion_texto'] as String?,
      ubicacionInicial: j['ubicacion_inicial'] is Map<String, dynamic>
          ? j['ubicacion_inicial'] as Map<String, dynamic>
          : null,
      textoAdicional: j['texto_adicional'] as String?,
      evidenciasPendientes: evRaw is List
          ? [
              for (final e in evRaw)
                if (e is Map<String, dynamic>)
                  OfflineEvidenciaPendiente.fromJson(e),
            ]
          : const [],
      solicitudIdRemota: j['solicitud_id_remota'] as int?,
      wizardCompletado: j['wizard_completado'] as bool? ?? false,
      registradoLocalEn: j['registrado_local_en'] as String,
      estadoLocal: OfflineSyncEstado.values.byName(
        j['estado_local'] as String? ?? OfflineSyncEstado.pendiente.name,
      ),
      ultimoError: j['ultimo_error'] as String?,
    );
  }
}

class OfflineSyncResult {
  const OfflineSyncResult({
    required this.synced,
    required this.failed,
    required this.errors,
  });

  final int synced;
  final int failed;
  final List<String> errors;

  bool get hasWork => synced > 0 || failed > 0;
}

class OfflineEmergenciaQueue {
  OfflineEmergenciaQueue(this._dio, this._repo);

  final Dio _dio;
  final EmergenciasRepository _repo;

  Future<List<OfflineEmergenciaDraft>> listAll() => _loadAll();

  Future<List<OfflineEmergenciaDraft>> listPending() async {
    final all = await _loadAll();
    return all
        .where(
          (e) =>
              e.estadoLocal != OfflineSyncEstado.sincronizado &&
              (e.wizardCompletado || e.solicitudIdRemota != null),
        )
        .toList();
  }

  Future<void> upsert(OfflineEmergenciaDraft draft) async {
    final all = await _loadAll();
    final idx = all.indexWhere((e) => e.clientUuid == draft.clientUuid);
    if (idx >= 0) {
      all[idx] = draft;
    } else {
      all.add(draft);
    }
    await _saveAll(all);
  }

  Future<void> enqueue(OfflineEmergenciaDraft draft) => upsert(draft);

  Future<OfflineSyncResult> syncPending() async {
    final all = await _loadAll();
    var synced = 0;
    var failed = 0;
    final errors = <String>[];

    for (final draft in all) {
      if (draft.estadoLocal == OfflineSyncEstado.sincronizado) continue;
      if (!draft.wizardCompletado && draft.solicitudIdRemota == null) continue;

      draft.estadoLocal = OfflineSyncEstado.enviado;
      draft.ultimoError = null;
      await _saveAll(all);

      try {
        final hadRemoteId = draft.solicitudIdRemota != null;
        final solicitudId = await _ensureSolicitudId(draft);
        await _uploadPendingParts(
          solicitudId,
          draft,
          ubicacionYaEnSync: !hadRemoteId,
          patchTextoAdicional: hadRemoteId,
        );
        draft.estadoLocal = OfflineSyncEstado.sincronizado;
        draft.ultimoError = null;
        synced++;
        await OfflineEmergenciaStorage.deleteDraft(draft.clientUuid);
      } on DioException catch (e) {
        if (isNetworkFailure(e)) {
          draft.estadoLocal = OfflineSyncEstado.pendiente;
        } else {
          draft.estadoLocal = OfflineSyncEstado.error;
          draft.ultimoError = messageFromDio(e);
          failed++;
          errors.add(draft.ultimoError!);
        }
      } catch (e) {
        draft.estadoLocal = OfflineSyncEstado.error;
        draft.ultimoError = e.toString();
        failed++;
        errors.add(draft.ultimoError!);
      }
      await _saveAll(all);
    }

    return OfflineSyncResult(synced: synced, failed: failed, errors: errors);
  }

  Future<int> _ensureSolicitudId(OfflineEmergenciaDraft draft) async {
    if (draft.solicitudIdRemota != null) {
      return draft.solicitudIdRemota!;
    }

    final res = await _dio.post<Map<String, dynamic>>(
      ApiConstants.appClienteEmergenciasSync,
      data: {
        'client_uuid': draft.clientUuid,
        'vehiculo_id': draft.vehiculoId,
        if (_mergedDescripcion(draft) != null)
          'descripcion_texto': _mergedDescripcion(draft),
        if (draft.ubicacionInicial != null) 'ubicacion_inicial': draft.ubicacionInicial,
        'registrado_local_en': draft.registradoLocalEn,
      },
    );
    final id = res.data?['solicitud_id'];
    if (id is! int) {
      throw Exception('El servidor no devolvió solicitud_id tras sincronizar.');
    }
    draft.solicitudIdRemota = id;
    return id;
  }

  Future<void> _uploadPendingParts(
    int solicitudId,
    OfflineEmergenciaDraft draft, {
    required bool ubicacionYaEnSync,
    required bool patchTextoAdicional,
  }) async {
    if (draft.ubicacionInicial != null && !ubicacionYaEnSync) {
      final u = draft.ubicacionInicial!;
      await _repo.postUbicacion(
        solicitudId,
        latitud: (u['latitud'] as num).toDouble(),
        longitud: (u['longitud'] as num).toDouble(),
        precisionMetros: u['precision_metros'] is num
            ? (u['precision_metros'] as num).toDouble()
            : null,
        direccionReferencia: u['direccion_referencia'] as String?,
        esActual: u['es_actual'] as bool? ?? true,
      );
    }

    for (final ev in draft.evidenciasPendientes) {
      if (!await File(ev.localPath).exists()) continue;
      await _repo.postEvidenciaArchivo(
        solicitudId,
        tipoApi: ev.tipo,
        filePath: ev.localPath,
        filename: ev.filename,
        mimeType: ev.mimeType,
      );
    }

    final extra = draft.textoAdicional?.trim();
    if (patchTextoAdicional && extra != null && extra.isNotEmpty) {
      await _repo.patchTexto(solicitudId, descripcionTexto: extra);
    }
  }

  String? _mergedDescripcion(OfflineEmergenciaDraft draft) {
    final base = draft.descripcionTexto?.trim();
    final extra = draft.textoAdicional?.trim();
    if (base != null && base.isNotEmpty && extra != null && extra.isNotEmpty) {
      return '$base\n\n$extra';
    }
    if (base != null && base.isNotEmpty) return base;
    if (extra != null && extra.isNotEmpty) return extra;
    return null;
  }

  Future<List<OfflineEmergenciaDraft>> _loadAll() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_storageKey);
    if (raw == null || raw.isEmpty) {
      // Migrar v1 si existe
      final legacy = prefs.getString('emergencias_offline_queue_v1');
      if (legacy != null && legacy.isNotEmpty) {
        await prefs.setString(_storageKey, legacy);
        await prefs.remove('emergencias_offline_queue_v1');
        return _loadAll();
      }
      return [];
    }
    final decoded = jsonDecode(raw);
    if (decoded is! List) return [];
    return [
      for (final e in decoded)
        if (e is Map<String, dynamic>) OfflineEmergenciaDraft.fromJson(e),
    ];
  }

  Future<void> _saveAll(List<OfflineEmergenciaDraft> items) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
      _storageKey,
      jsonEncode(items.map((e) => e.toJson()).toList()),
    );
  }
}

/// UUID v4 válido para el backend (`uuid.UUID`).
String newClientUuid() {
  final r = Random.secure();
  final b = List<int>.generate(16, (_) => r.nextInt(256));
  b[6] = (b[6] & 0x0f) | 0x40;
  b[8] = (b[8] & 0x3f) | 0x80;
  String hh(int i) => b[i].toRadixString(16).padLeft(2, '0');
  return '${hh(0)}${hh(1)}${hh(2)}${hh(3)}-'
      '${hh(4)}${hh(5)}-'
      '${hh(6)}${hh(7)}-'
      '${hh(8)}${hh(9)}-'
      '${hh(10)}${hh(11)}${hh(12)}${hh(13)}${hh(14)}${hh(15)}';
}
