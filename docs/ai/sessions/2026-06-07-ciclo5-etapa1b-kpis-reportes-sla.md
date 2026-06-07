# Ciclo 5 Etapa 1B — KPIs, reportes y SLA

**Fecha:** 2026-06-07

## CU45 — Dashboard operacional KPIs

Endpoints bajo `/api/admin/dashboard/` (permiso `kpis:leer`):

| Ruta | Descripción |
|------|-------------|
| `GET /kpis` | Resumen completo (totales, promedios, SLA, desgloses) |
| `GET /incidents-by-type` | Incidentes por tipo (desde `ai_payload`) |
| `GET /incidents-by-zone` | Zonas con más incidentes |
| `GET /workshop-efficiency` | Ranking talleres más eficientes |
| `GET /cancelled-cases` | Casos cancelados |
| `GET /sla-summary` | Resumen cumplimiento SLA |

Filtros query (todos opcionales): `tenant_id`, `desde`, `hasta`, `taller_id`, `zona_id`, `tipo_incidente_id`.

## CU46 — Reportes

Endpoints bajo `/api/admin/reports/`:

| Ruta | Permiso |
|------|---------|
| `GET /incidents` | `reports:leer` |
| `GET /performance` | `reports:leer` |
| `GET /workshops` | `reports:leer` |
| `GET /cancellations` | `reports:leer` |
| `GET /export/csv` | `reports:exportar` |

Datos desde `solicitudes_emergencia` + joins cliente/vehículo/taller/zona/pagos.

## CU50 — SLA por taller

| Ruta | Descripción |
|------|-------------|
| `GET /api/admin/sla/workshops` | Lista cumplimiento por taller |
| `GET /api/admin/sla/workshops/{id}` | Detalle + casos fuera de SLA |

Permiso: `sla:leer`.

## Archivos nuevos/modificados

- `backend/app/modules/kpis/{filters,deps,admin_router,service,schemas,router}.py`
- `backend/app/modules/reports/{schemas,service,router}.py`
- `backend/app/modules/sla/{schemas,service,router}.py`
- `backend/alembic/versions/0013_ciclo5_reports_sla.py`
- `backend/migrations/0021_ciclo5_reports_sla_permisos.sql`
- `backend/tests/test_ciclo5_kpis.py`

## Comandos

```bash
docker compose exec backend alembic upgrade head
```

## Ejemplo curl

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/admin/dashboard/kpis?desde=2026-01-01&hasta=2026-06-07"

curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/admin/reports/export/csv?desde=2026-01-01" \
  -o reporte.csv
```

## Pendiente

- Etapa 1D–E: `tenant_id` en cotizaciones/pagos + rechazo cotización
- Etapa 2 Angular: dashboard, reportes, SLA screens
- Etapa 3 Flutter: alinear nuevos endpoints si aplica
