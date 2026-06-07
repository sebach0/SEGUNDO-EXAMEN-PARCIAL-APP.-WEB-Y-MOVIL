# Ciclo 5 Etapa 1A — Tenants CU43–CU44

**Fecha:** 2026-06-07

## Qué se implementó

### CU43 — Gestionar tenant / organización

- Columna `tenants.actualizado_en` (migración `0012` + SQL `0020`).
- CRUD admin completo bajo `/api/admin/tenants/`:
  - `GET /` — listar
  - `GET /{tenant_id}` — detalle
  - `POST /` — crear (slug único, estado ACTIVO|INACTIVO|SUSPENDIDO)
  - `PATCH /{tenant_id}` — editar nombre/slug/estado
  - `PATCH /{tenant_id}/activate` — activar
  - `PATCH /{tenant_id}/deactivate` — desactivar (sin borrado físico)
- Compatibilidad: `/api/tenants/` (GET/POST legacy Ciclo 4).
- Bitácora en crear/actualizar/activar/desactivar.

### CU44 — Asignar usuarios y talleres a tenant

- Permiso nuevo: `tenants:asignar` (rol ADMIN).
- Endpoints:
  - `GET /api/admin/tenants/{tenant_id}/members`
  - `POST /api/admin/tenants/{tenant_id}/assign-users` body `{ "ids": [1,2] }`
  - `POST /api/admin/tenants/{tenant_id}/assign-workshops`
  - `POST /api/admin/tenants/{tenant_id}/assign-technicians`
  - `PATCH /api/admin/users/{user_id}/tenant` body `{ "tenant_id": N }`
  - `PATCH /api/admin/workshops/{workshop_id}/tenant`
  - `PATCH /api/admin/technicians/{technician_id}/tenant`
- Técnicos: actualiza `usuarios.tenant_id` y alinea `talleres.tenant_id` del taller del técnico.
- Respuesta: `{ message, tenant_id, assigned[], skipped[] }`.
- Movimiento entre tenants permitido (admin con permiso).

### Multi-tenant helper

- `resolve_tenant_scope()` en `ciclo4/deps.py` — base para CU45+ (filtros cross-tenant).

## Archivos tocados

- `backend/migrations/0020_ciclo5_tenants_actualizado_permisos.sql`
- `backend/alembic/versions/0012_ciclo5_tenants_actualizado_permisos.py`
- `backend/app/modules/ciclo4/tenants/{models,schemas,service,service_assignments,router}.py`
- `backend/app/modules/ciclo4/deps.py`
- `backend/app/main.py`
- `backend/tests/test_ciclo5_tenants.py`

## Comandos

```bash
docker compose exec backend alembic upgrade head
```

## Prueba curl (tras login admin)

```bash
# Listar tenants
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/admin/tenants/

# Crear tenant
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"nombre":"Red Sur","slug":"red-sur","estado":"ACTIVO"}' \
  http://localhost:8000/api/admin/tenants/

# Asignar usuario 5 al tenant 2
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"ids":[5]}' http://localhost:8000/api/admin/tenants/2/assign-users
```

## Pendiente (Etapa 1B+)

- CU45 KPIs admin desglosados
- CU46 reportes CSV
- CU47–49 endurecer tenant_id en cotizaciones/pagos
- CU50 SLA por taller
- Frontend Angular tenants/assignments
