// Registro y baja de token FCM (CU19) al iniciar o cerrar sesión cliente / técnico.
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart' show defaultTargetPlatform, kIsWeb, TargetPlatform;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:permission_handler/permission_handler.dart';

import '../../cliente/application/cliente_injection.dart';
import '../../tecnico/application/tecnico_injection.dart';
import '../constants/api_constants.dart';

@pragma('vm:entry-point')
Future<void> firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
}

final _lastClienteToken = <String, String?>{'t': null};
final _lastTecnicoToken = <String, String?>{'t': null};

Future<String?> _ensurePermissionAndToken() async {
  if (kIsWeb) {
    return null;
  }
  if (defaultTargetPlatform == TargetPlatform.android) {
    final s = await Permission.notification.status;
    if (!s.isGranted) {
      final r = await Permission.notification.request();
      if (!r.isGranted) return null;
    }
  } else {
    final settings = await FirebaseMessaging.instance.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );
    if (settings.authorizationStatus == AuthorizationStatus.denied) {
      return null;
    }
  }
  return FirebaseMessaging.instance.getToken();
}

String _androidOrIos() {
  if (kIsWeb) return 'web';
  if (defaultTargetPlatform == TargetPlatform.android) return 'android';
  if (defaultTargetPlatform == TargetPlatform.iOS) return 'ios';
  return 'unknown';
}

Future<String?> _fcmTokenOrNull() async {
  try {
    return await FirebaseMessaging.instance
        .getToken()
        .timeout(const Duration(seconds: 3));
  } catch (_) {
    return null;
  }
}

class FcmRegistration {
  FcmRegistration(this._ref);

  final Ref _ref;

  /// Tras login o al restaurar sesión (cliente).
  Future<void> onClienteSessionActive() async {
    if (kIsWeb) {
      return;
    }
    final token = await _ensurePermissionAndToken();
    if (token == null) return;
    _lastClienteToken['t'] = token;
    final repo = _ref.read(comunicacionRepositoryProvider);
    try {
      await repo.registrarTokenFcm(token: token, platform: _androidOrIos());
    } catch (_) {
      // Reintentará al volver a abrir la app.
    }
  }

  /// Antes de [AuthRepository.logout] (Authorization aún válido).
  Future<void> beforeClienteLogout() async {
    if (kIsWeb) {
      return;
    }
    final t = _lastClienteToken['t'] ?? await _fcmTokenOrNull();
    if (t == null) return;
    final repo = _ref.read(comunicacionRepositoryProvider);
    try {
      await repo
          .eliminarTokenFcm(token: t, platform: _androidOrIos())
          .timeout(const Duration(seconds: 3));
    } catch (_) {}
    _lastClienteToken['t'] = null;
  }

  /// Tras login o al restaurar sesión (técnico).
  Future<void> onTecnicoSessionActive() async {
    if (kIsWeb) {
      return;
    }
    final token = await _ensurePermissionAndToken();
    if (token == null) return;
    _lastTecnicoToken['t'] = token;
    final dio = _ref.read(tecnicoDioProvider);
    try {
      await dio.post<void>(
        ApiConstants.appTecnicoFcm,
        data: {'token': token, 'platform': _androidOrIos()},
      );
    } catch (_) {}
  }

  /// Antes de cerrar sesión técnico.
  Future<void> beforeTecnicoLogout() async {
    if (kIsWeb) {
      return;
    }
    final t = _lastTecnicoToken['t'] ?? await _fcmTokenOrNull();
    if (t == null) return;
    final dio = _ref.read(tecnicoDioProvider);
    try {
      await dio
          .delete<void>(ApiConstants.appTecnicoFcm, data: {'token': t, 'platform': _androidOrIos()})
          .timeout(const Duration(seconds: 3));
    } catch (_) {}
    _lastTecnicoToken['t'] = null;
  }
}

final fcmRegistrationProvider = Provider<FcmRegistration>((ref) {
  return FcmRegistration(ref);
});
