# Sesión 2026-06-07 — Ciclo 5 Etapa 1D–E (cotizaciones + pagos tenant)

## Objetivo

Completar CU47–49 en backend: aislamiento multi-tenant en cotizaciones/pagos, rechazo de cotización y administración de pagos manuales.

## Cambios backend

### Migración `0014_ciclo5_cotiz_pagos` / SQL `0022`

- `cotizaciones.tenant_id`, `cotizacion_items.tenant_id` (backfill desde solicitud).
- `pagos.tenant_id`, `pagos.cotizacion_id` (backfill cotización ACEPTADA).
- Permisos: `cotizaciones:rechazar`, `pagos:admin`.

### Cotizaciones

- `tenant_guard.py`: `assert_user_tenant_access`, `resolve_tenant_for_cotizacion`, etc.
- Servicio: `rechazar_cotizacion`, `responder_cotizacion`; tenant checks en listar/proponer/seleccionar.
- Router:
  - `PATCH /api/cotizaciones/solicitudes/{id}/cotizacion/{id}/rechazar`
  - `PATCH /api/cotizaciones/solicitudes/{id}/cotizacion/{id}/respond`
  - Endpoints existentes pasan `user`, `permisos`, `cliente_id`.

### Pagos

- Cliente: `tenant_id` + `cotizacion_id` al crear; monto validado vs cotización ACEPTADA.
- Admin:
  - `GET /api/admin/payments`
  - `PATCH /api/admin/payments/{id}/validate-manual`
- Módulos: `pagos/admin_service.py`, `pagos/admin_router.py`.

## Tests

- `backend/tests/test_ciclo5_cotizaciones_pagos.py` — 8 tests unitarios (schemas + tenant guard).

## Validación manual sugerida

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python -m unittest tests.test_ciclo5_cotizaciones_pagos -v
```

## Siguiente

- Etapa 2 Angular: UI admin pagos + rechazo cotización web si aplica.
- Etapa 3 Flutter: botón rechazar cotización en marketplace cliente.
