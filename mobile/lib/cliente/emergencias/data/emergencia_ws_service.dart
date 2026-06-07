// Servicio WebSocket para seguimiento en tiempo real de una solicitud.
//
// El canal backend es /ws/incidents/{solicitudId}?token=TOKEN
// (usa solicitud_id como clave — ver ConnectionManager.broadcast_to_incident).
//
// El servicio:
//  - Conecta al WebSocket y expone un Stream<Map<String,dynamic>>.
//  - Reconecta automáticamente con backoff exponencial (máx 30 s).
//  - Se cancela limpiamente cuando el Provider se descarta (autoDispose).

import 'dart:async';
import 'dart:convert';
import 'dart:developer';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import '../../../core/config/app_env.dart';

/// Evento recibido por WebSocket (formato del backend ConnectionManager).
class WsSolicitudEvent {
  const WsSolicitudEvent({
    required this.type,
    required this.solicitudId,
    this.status,
    this.message,
    this.payload = const {},
    required this.emittedAt,
  });

  final String type;
  final int solicitudId;
  final String? status;
  final String? message;
  final Map<String, dynamic> payload;
  final String emittedAt;

  factory WsSolicitudEvent.fromJson(Map<String, dynamic> json) {
    return WsSolicitudEvent(
      type: json['type'] as String? ?? '',
      solicitudId: (json['incident_id'] as num?)?.toInt() ?? 0,
      status: json['status'] as String?,
      message: json['message'] as String?,
      payload: (json['payload'] as Map<String, dynamic>?) ?? {},
      emittedAt: json['emitted_at'] as String? ?? '',
    );
  }
}

class EmergenciaWsService {
  EmergenciaWsService({required this.solicitudId});

  final int solicitudId;
  final _storage = const FlutterSecureStorage();

  final _controller = StreamController<WsSolicitudEvent>.broadcast();
  Stream<WsSolicitudEvent> get events => _controller.stream;

  WebSocketChannel? _channel;
  StreamSubscription<dynamic>? _sub;
  bool _disposed = false;
  int _attempt = 0;
  Timer? _reconnectTimer;

  // ── Ciclo de vida ──────────────────────────────────────────────────────────

  Future<void> connect() async {
    if (_disposed) return;
    final token = await _storage.read(key: 'access_token') ?? '';
    final rawBase = AppEnv.apiBaseUrl; // e.g. http://192.168.0.10:8000/api
    // WS URL: reemplaza http(s) por ws(s), mantiene el prefijo /api
    final wsBase = rawBase.replaceFirst(RegExp(r'^http'), 'ws');
    final uri = Uri.parse('$wsBase/ws/incidents/$solicitudId?token=$token');

    log('EmergenciaWsService: conectando $uri');
    try {
      _channel = WebSocketChannel.connect(uri);
      _sub = _channel!.stream.listen(
        _onData,
        onError: _onError,
        onDone: _onDone,
        cancelOnError: false,
      );
      _attempt = 0;
    } catch (e) {
      log('EmergenciaWsService: error al conectar: $e');
      _scheduleReconnect();
    }
  }

  void dispose() {
    _disposed = true;
    _reconnectTimer?.cancel();
    _sub?.cancel();
    _channel?.sink.close();
    _controller.close();
  }

  // ── Internos ──────────────────────────────────────────────────────────────

  void _onData(dynamic raw) {
    if (_disposed) return;
    try {
      final json = jsonDecode(raw as String) as Map<String, dynamic>;
      final event = WsSolicitudEvent.fromJson(json);
      _controller.add(event);
    } catch (e) {
      log('EmergenciaWsService: error parseando mensaje: $e');
    }
  }

  void _onError(Object error) {
    log('EmergenciaWsService: error WS: $error');
  }

  void _onDone() {
    if (_disposed) return;
    log('EmergenciaWsService: conexión cerrada, reconectando…');
    _scheduleReconnect();
  }

  void _scheduleReconnect() {
    if (_disposed) return;
    final delay = Duration(seconds: (1 << _attempt).clamp(1, 30));
    _attempt++;
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(delay, connect);
  }
}
