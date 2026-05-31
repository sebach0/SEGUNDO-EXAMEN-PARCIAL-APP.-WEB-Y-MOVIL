# Sesión 2026-04-26 — Paquete `comunicacion_y_notificaciones`

## Hecho

- `app/modules/comunicacion_y_notificaciones/__init__.py`.
- Movidos en bloque: `comunicaciones/`, `dispositivos_push/`, `mensajes_solicitud/`, `notificaciones/`.
- Sustitución global de imports:
  - `app.modules.comunicaciones` → `...comunicacion_y_notificaciones.comunicaciones`
  - `app.modules.dispositivos_push` → `...dispositivos_push`
  - `app.modules.mensajes_solicitud` → `...mensajes_solicitud`
  - `app.modules.notificaciones` → `...notificaciones`

## Contrato HTTP

- Sin cambio de prefijos (`/api/app/cliente/...`, `/api/app/tecnico/...`, mensajes bajo emergencias, etc.).

## Verificación

- `python -m compileall -q app` desde `backend/`.
