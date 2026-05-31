# Sesión — 2026-04-25 — Push foreground como notificación del sistema

## Contexto
- Usuario confirmó que el backend ya tenía `FCM_ENABLED=true`, tokens registrados y eventos de notificación en DB.
- Problema principal: en app móvil, con la app abierta, la “notificación” se veía como `SnackBar` (UX no profesional).

## Cambios aplicados
- **Mobile**
  - Archivo: `mobile/lib/core/push/fcm_message_listener.dart`
  - Reemplazo de `SnackBar` en `onMessage` por notificación local del sistema usando `flutter_local_notifications`.
  - Inicialización de plugin + canal Android de alta prioridad `emergencias_high_importance`.
  - Tap en notificación local con payload JSON y navegación por `GoRouter` al destino correcto.
  - Se conserva manejo de `onMessageOpenedApp` y `getInitialMessage`.

- **Dependencias**
  - `mobile/pubspec.yaml`: se añadió `flutter_local_notifications` (con sus paquetes plataforma).

- **Backend observabilidad**
  - Archivo: `backend/app/modules/comunicaciones/fcm_client.py`
  - Logs de resultado de envío multicast: `success_count`, `failure_count`, total tokens y detalle de fallos por token.

## Verificación realizada
- `flutter analyze lib/core/push/fcm_message_listener.dart` ✅ sin errores.
- `docker compose up -d --build backend` ✅ backend reconstruido con logging de FCM.

## Resultado esperado para QA
1. Con app en foreground, llega banner/notificación del sistema (no `SnackBar`).
2. Tap sobre notificación abre pantalla de chat/detalle correspondiente.
3. Logs backend muestran línea `FCM multicast enviado: success=... failure=...`.

