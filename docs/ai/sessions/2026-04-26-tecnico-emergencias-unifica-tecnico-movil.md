# 2026-04-26 — `tecnico_emergencias`: paquete `service/` y fin de `tecnico_movil`

- Eliminado `tecnico_movil/`; `require_tecnico_rol` y `get_tecnico_row_for_usuario` viven en `tecnico_emergencias/service/acceso.py`.
- El antiguo `tecnico_emergencias/service.py` monolítico se reemplazó por `service/`: `servicios.py`, `ubicaciones.py`, `estado.py`, `mensajes_tecnico.py`, `__init__.py` reexporta la API pública.
- Consumidores: `comunicaciones/router.py`, `mensajes_solicitud/service.py` importan desde `app.modules.tecnico_emergencias.service`.
