# 2026-04-26 — Refactor: módulos `auth` / `roles` / `permisos` y notificaciones/push/mensajes

## Objetivo
Separar el monolito `acceso` y el paquete `comunicaciones` (modelo+repo+FCM+servicio en un solo sitio) en módulos propios, manteniendo las mismas tablas, rutas HTTP y contratos de API.

## Cambios backend
- **Nuevos:** `app/modules/permisos/`, `app/modules/roles/`, `app/modules/auth/` (incl. `email_tokens.py`).
- **Eliminado:** `app/modules/acceso/`.
- **Nuevos:** `app/modules/notificaciones/`, `app/modules/dispositivos_push/`, `app/modules/mensajes_solicitud/`.
- **`comunicaciones`:** permanece con `router.py` + `integration.md`; el resto pasa a los módulos anteriores.
- **`db_metadata.py`:** importa modelos de `permisos` → `roles` → `auth` y, para comunicación, `notificaciones` / `mensajes_solicitud` / `dispositivos_push` (después de `emergencias`).

## Criterios
- Misma URL: `/api/auth/*`, `/api/roles/*`, `/api/permisos/*`, `portal/.../dispositivos|notificaciones|emergencias/.../mensajes`.
- Bitácora de asignación de roles: `modulo="roles"` (antes `acceso`).
- Puerta de FCM: `dispositivos_push.service.registrar_fcm_token` importa con lazy `notificaciones.service.crear_notificacion_y_push` para evitar ciclos.

## Verificación
- `python -m compileall` en los módulos nuevos (sin errores de sintaxis).
- Tests unitarios: requieren entorno con dependencias (`pydantic`, etc.); en host sin venv, ejecutar con el mismo intérprete que el proyecto o Docker.
