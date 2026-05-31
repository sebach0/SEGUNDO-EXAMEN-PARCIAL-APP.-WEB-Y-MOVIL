# 2026-04-26 — Refactor: `portal_taller_emergencias` servicio en paquete

## Qué
- El monolito `app/modules/portal_taller_emergencias/service.py` se reemplazó por un **paquete** `app/modules/portal_taller_emergencias/service/`.
- Submódulos: `helpers.py` (enriquecimiento bandeja, disponibilidad, constantes y mapeos de asignación), `bandeja.py` (listado, detalle, disponibilidad, aceptar/rechazar), `asignaciones.py` (CU28, listado de asignaciones), `reportes.py` (historial, comisiones, dashboard).
- `service/__init__.py` reexporta las mismas funciones que antes: `from app.modules.portal_taller_emergencias import service` y `from . import service` en el router **sin cambio**.

## Por qué
- Archivo ~580 líneas difícil de mantener; separación por **responsabilidad** sin romper módulo de dominio.
