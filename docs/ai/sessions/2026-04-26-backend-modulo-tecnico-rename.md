# 2026-04-26 — Paquete backend `tecnico_emergencias` → `tecnico`

- Carpeta: `app/modules/tecnico_emergencias/` renombrada a `app/modules/tecnico/`.
- Imports: `app.modules.tecnico.*` (router, schemas, service).
- `main.py`: `tecnico_router` desde `app.modules.tecnico.router`.
- Bitácora (`registrar_accion` `modulo=`): cadenas `tecnico_emergencias` → `tecnico` en `service/estado.py` y `service/ubicaciones.py`.
- Test: `test_tecnico_emergencias_schemas.py` → `test_tecnico_schemas.py`.
- **URLs sin cambio:** el router sigue con `prefix="/app/tecnico/emergencias"`.
