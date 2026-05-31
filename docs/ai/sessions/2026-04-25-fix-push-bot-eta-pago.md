# Sesión — 2026-04-25 — fix push técnico + hora BOT + ETA + pago

## Contexto
Pruebas reales reportaron:
- Push al técnico no recibido en dispositivo.
- Hora BOT mostrada incorrectamente (ej. `01:38 BOT` cuando debía ser hora local de Bolivia nocturna previa).
- ETA ausente en seguimiento.
- Pago cliente sin aprovechar presupuesto registrado por técnico.

## Cambios aplicados

### 1) Push técnico pendiente al registrar token
- Archivo: `backend/app/modules/comunicaciones/service.py`
- Cambio: en `registrar_fcm_token`, cuando el usuario no tenía tokens previos, se reenvían hasta 10 notificaciones no leídas recientes vía `_notificar_push`.
- Objetivo: cubrir casos donde evento de negocio ocurrió antes del registro FCM.

### 2) Hora BOT correcta en mobile (parse UTC de timestamps naive)
- Archivo nuevo: `mobile/lib/core/utils/api_datetime.dart`
- Regla: si timestamp llega sin zona, parsearlo como UTC agregando `Z`.
- Archivos actualizados para usar parser común:
  - `cliente/emergencias/domain/solicitud_emergencia_models.dart`
  - `cliente/emergencias/domain/solicitud_seguimiento_models.dart`
  - `cliente/comunicacion/domain/mensaje_solicitud_models.dart`
  - `cliente/comunicacion/domain/notificacion_models.dart`
  - `cliente/emergencias/domain/ubicacion_tecnico_compartida.dart`
  - `tecnico/emergencias/domain/tecnico_servicio_models.dart`
  - `cliente/pagos/domain/pago_models.dart`

### 3) ETA fallback operativo
- Archivo: `backend/app/modules/portal_tecnico_emergencias/service.py`
- Cambio: transición a `EN_CAMINO` ahora setea `tiempo_estimado_min = 20` si estaba `NULL`.

### 4) Pago cliente prellenado desde presupuesto técnico
- Archivo: `mobile/lib/cliente/pagos/presentation/screens/pago_resumen_screen.dart`
- Cambio: si `presupuesto_bob` existe en detalle/seguimiento, el monto se prellena y se muestra una tarjeta informativa.

## Verificación rápida ejecutada
- `python -m py_compile` sobre servicios backend modificados ✅
- `dart format` sobre archivos Dart modificados ✅

## Riesgos / siguientes verificaciones
- Revisar en entorno real que Firebase entregue el replay según expectativas UX (no saturar con notificaciones históricas).
- Definir política final para ETA predictiva real (distancia/tráfico) frente al fallback fijo.
