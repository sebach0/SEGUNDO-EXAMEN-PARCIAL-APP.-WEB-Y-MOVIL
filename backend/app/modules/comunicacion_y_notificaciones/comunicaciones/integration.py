"""Extensión futura con `emergencias` y tiempo real (CU19).

- **Push al cambiar estado:** desde `emergencias/service` (tras guardar historial),
  llamar a `notificaciones.service.crear_notificacion_y_push(...)` con el
  `usuario_id` del cliente y `TipoNotificacionEnum.ESTADO_ACTUALIZADO` (o el que corresponda).

- **WebSocket / SSE:** exponer un `asyncio.Queue` o bus de eventos por `solicitud_id`
  al que escriba el mismo servicio que hoy inserta en `solicitud_mensajes`; un proceso
  worker puede fan-out a conexiones WS sin cambiar el contrato REST del chat.
"""
