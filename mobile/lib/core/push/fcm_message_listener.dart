// Escucha notificaciones FCM y muestra notificación del sistema (Android/iOS).
import 'dart:async';
import 'dart:convert';

import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../cliente/presentation/router/cliente_go_router.dart';

/// [GoRouter] vive bajo [ShadApp.router]; este widget lo envuelve, así que
/// [GoRouter.of] del [context] aquí falla. Usamos [goRouterProvider] (misma instancia
/// que [routerConfig]) para [go] y para leer la ruta actual.
class FcmMessageListener extends ConsumerStatefulWidget {
  const FcmMessageListener({super.key, required this.child});

  final Widget child;

  @override
  ConsumerState<FcmMessageListener> createState() => _FcmMessageListenerState();
}

class _FcmMessageListenerState extends ConsumerState<FcmMessageListener> {
  StreamSubscription<RemoteMessage>? _onMessageSub;
  StreamSubscription<RemoteMessage>? _onOpenSub;

  @override
  void initState() {
    super.initState();
    if (kIsWeb) return;
    unawaited(
      _SystemLocalNotifier.instance.initialize(
        onTapPayload: _onLocalNotificationTap,
      ),
    );
    _onMessageSub = FirebaseMessaging.onMessage.listen(_onMessage);
    _onOpenSub = FirebaseMessaging.onMessageOpenedApp.listen(_onMessageOpened);
    unawaited(_handleInitialMessage());
  }

  Future<void> _onMessage(RemoteMessage message) async {
    if (!mounted || kIsWeb) return;
    final target = _targetFromMessage(message);
    await _SystemLocalNotifier.instance.showFromRemoteMessage(
      message,
      payload: jsonEncode({'target': target}),
    );
  }

  Future<void> _handleInitialMessage() async {
    final initial = await FirebaseMessaging.instance.getInitialMessage();
    if (!mounted || initial == null) return;
    _onMessageOpened(initial);
  }

  void _onMessageOpened(RemoteMessage message) {
    if (!mounted) return;
    final target = _targetFromMessage(message);
    ref.read(goRouterProvider).go(target);
  }

  void _onLocalNotificationTap(String? payload) {
    if (!mounted || payload == null || payload.isEmpty) return;
    try {
      final m = jsonDecode(payload) as Map<String, dynamic>;
      final target = (m['target'] ?? '').toString();
      if (target.isEmpty) return;
      ref.read(goRouterProvider).go(target);
    } catch (_) {
      // Ignorar payload mal formado.
    }
  }

  String _targetFromMessage(RemoteMessage message) {
    final solicitudId = int.tryParse((message.data['solicitud_id'] ?? '').toString());
    if (solicitudId == null) return '/';
    final tipo = (message.data['tipo'] ?? '').toString().toUpperCase();
    final accion = (message.data['accion'] ?? '').toString().toUpperCase();
    final location =
        ref.read(goRouterProvider).routerDelegate.currentConfiguration.uri.toString();
    final esTecnico = location.startsWith('/tecnico');
    return switch ((esTecnico, tipo, accion)) {
      (true, 'MENSAJE_NUEVO', _) => '/tecnico/app/servicios/$solicitudId/chat',
      (true, _, _) => '/tecnico/app/servicios/$solicitudId',
      (false, 'MENSAJE_NUEVO', _) =>
        '/cliente/app/emergencias/solicitudes/$solicitudId/chat',
      (false, _, 'COTIZACION_NUEVA') =>
        '/cliente/app/emergencias/solicitudes/$solicitudId/cotizaciones',
      (false, _, _) =>
        '/cliente/app/emergencias/solicitudes/$solicitudId/seguimiento',
    };
  }

  @override
  void dispose() {
    _onMessageSub?.cancel();
    _onOpenSub?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => widget.child;
}

class _SystemLocalNotifier {
  _SystemLocalNotifier._();

  static final instance = _SystemLocalNotifier._();

  final FlutterLocalNotificationsPlugin _plugin = FlutterLocalNotificationsPlugin();
  bool _initialized = false;

  Future<void> initialize({required void Function(String? payload) onTapPayload}) async {
    if (_initialized || kIsWeb) return;

    const androidInit = AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosInit = DarwinInitializationSettings();
    const settings = InitializationSettings(android: androidInit, iOS: iosInit);

    await _plugin.initialize(
      settings: settings,
      onDidReceiveNotificationResponse: (response) => onTapPayload(response.payload),
      onDidReceiveBackgroundNotificationResponse: _onBackgroundNotificationTap,
    );

    const androidChannel = AndroidNotificationChannel(
      'emergencias_high_importance',
      'Notificaciones de emergencias',
      description: 'Alertas de estado y mensajes de emergencia',
      importance: Importance.max,
    );
    await _plugin
        .resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(androidChannel);
    _initialized = true;
  }

  Future<void> showFromRemoteMessage(RemoteMessage message, {String? payload}) async {
    if (!_initialized) return;

    final title = (message.notification?.title ?? message.data['title'] ?? 'Emergencias Viales')
        .toString()
        .trim();
    final body = (message.notification?.body ?? message.data['body'] ?? '')
        .toString()
        .trim();

    if (title.isEmpty && body.isEmpty) return;

    const androidDetails = AndroidNotificationDetails(
      'emergencias_high_importance',
      'Notificaciones de emergencias',
      channelDescription: 'Alertas de estado y mensajes de emergencia',
      importance: Importance.max,
      priority: Priority.high,
      icon: '@mipmap/ic_launcher',
    );
    const iosDetails = DarwinNotificationDetails(
      presentAlert: true,
      presentBadge: true,
      presentSound: true,
    );
    const details = NotificationDetails(android: androidDetails, iOS: iosDetails);

    final notificationId = DateTime.now().millisecondsSinceEpoch.remainder(1 << 30);
    await _plugin.show(
      id: notificationId,
      title: title,
      body: body,
      notificationDetails: details,
      payload: payload,
    );
  }
}

@pragma('vm:entry-point')
void _onBackgroundNotificationTap(NotificationResponse response) {
  // El deep-link de la app se resuelve al reanudar con FCM getInitialMessage/onMessageOpenedApp.
}
