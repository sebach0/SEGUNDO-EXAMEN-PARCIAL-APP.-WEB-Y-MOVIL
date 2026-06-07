// lib/core/config/app_env.dart
// Valores leídos de mobile/.env (asset). Copiá .env.example → .env y ajustá.
import 'package:flutter_dotenv/flutter_dotenv.dart';

/// Acceso tipado a variables de `mobile/.env`.
///
/// [dotenv.load] debe ejecutarse en `main()` antes de `runApp`.
final class AppEnv {
  AppEnv._();

  static String? _baseUrl;

  /// Base del API, sin barra final (p. ej. `http://192.168.0.10:8000/api`).
  static String get apiBaseUrl {
    if (_baseUrl != null) return _baseUrl!;
    final raw = dotenv.env['API_BASE_URL']?.trim();
    if (raw == null || raw.isEmpty) {
      throw StateError(
        'API_BASE_URL no está definido en mobile/.env. '
        'Copiá mobile/.env.example a mobile/.env y configurá la URL alcanzable desde el dispositivo.',
      );
    }
    final normalized = raw.endsWith('/') ? raw.substring(0, raw.length - 1) : raw;
    _baseUrl = normalized;
    return _baseUrl!;
  }

  static String get appName {
    final n = dotenv.env['APP_NAME']?.trim();
    if (n != null && n.isNotEmpty) return n;
    throw StateError(
      'APP_NAME no está definido en mobile/.env. '
      'Copiá mobile/.env.example a mobile/.env.',
    );
  }

  static Duration get apiConnectTimeout {
    final s = int.tryParse(dotenv.env['API_CONNECT_TIMEOUT_SECONDS']?.trim() ?? '');
    return Duration(seconds: (s ?? 10).clamp(5, 120));
  }

  static Duration get apiReceiveTimeout {
    final s = int.tryParse(dotenv.env['API_RECEIVE_TIMEOUT_SECONDS']?.trim() ?? '');
    return Duration(seconds: (s ?? 30).clamp(5, 300));
  }

  /// Timeouts para subida multipart (foto/audio). Más largos que el resto del API.
  static Duration get apiUploadTimeout {
    final s = int.tryParse(dotenv.env['API_UPLOAD_TIMEOUT_SECONDS']?.trim() ?? '');
    return Duration(seconds: (s ?? 120).clamp(30, 600));
  }

  /// Opcional — subida previa a un CDN propio (JSON `{"url":"https://..."}`). El flujo normal
  /// sube foto/audio al propio API (`POST .../evidencias/archivo`); esto solo sirve si integrás otro bucket.
  static String? get fileUploadUrl {
    final u = dotenv.env['FILE_UPLOAD_URL']?.trim();
    if (u == null || u.isEmpty) return null;
    return u;
  }
}
