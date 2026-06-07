---
name: project-ciclo5-estado
description: Estado de implementación del Ciclo 5 del proyecto de emergencias vehiculares (CU43-CU50)
metadata:
  type: project
---

El Ciclo 5 (CU43-CU50) fue implementado completamente en sesión de 2026-06-07.

**Why:** Examen parcial 2 - plataforma SaaS multi-tenant de emergencias vehiculares.

**How to apply:** No reimplementar lo que ya existe. Analizar primero antes de tocar backend.

## Estado por capa

### Backend — 100% COMPLETO (no tocar)
- CU43 Tenants: `ciclo4/tenants/router.py` + `service.py`
- CU44 Asignaciones: `ciclo4/tenants/service_assignments.py`
- CU45 KPIs: `kpis/service.py` + `kpis/router.py` + `kpis/admin_router.py`
- CU46 Reportes: `reports/service.py` + `reports/router.py` (CSV incluido)
- CU47 Cotizaciones: `cotizaciones/service.py::proponer_cotizacion`
- CU48 Aprobar/rechazar: `cotizaciones/service.py::seleccionar_cotizacion / rechazar_cotizacion`
- CU49 Pagos: `pagos_y_comisiones/pagos/service.py`
- CU50 SLA: `sla/service.py` + `sla/router.py`
- Migraciones: 0012-0014 aplicadas
- Todos los routers registrados en `main.py`

### Angular Frontend — IMPLEMENTADO en ciclo 5
Nuevos componentes en `frontend/src/app/admin/features/ciclo5/`:
- `tenants/admin-tenants.component.*` (CU43)
- `asignaciones/admin-tenant-asignaciones.component.*` (CU44)
- `kpis/admin-kpis-dashboard.component.*` (CU45)
- `reports/admin-reports.component.*` (CU46 + exportar CSV)
- `sla/admin-sla.component.*` (CU50 + detalle casos fuera SLA)

Rutas agregadas a `admin.routes.ts`:
- `/admin/panel/ciclo5/tenants`
- `/admin/panel/ciclo5/tenants/:id/asignaciones`
- `/admin/panel/ciclo5/dashboard`
- `/admin/panel/ciclo5/reports`
- `/admin/panel/ciclo5/sla`

Tipos en `core/models/admin-api.models.ts`: TenantDto, AdminDashboardKpisDto, ReportDtos, SlaDto
Métodos en `core/services/admin-api.service.ts`: CRUD tenants, asignaciones, KPIs, reportes, SLA

### Flutter Mobile — 100% COMPLETO (ya existía)
- `cliente/cotizaciones/` — lista con selección/aceptación
- `cliente/pagos/` — múltiples pantallas de pago completas

## Convenciones CSS Angular admin
- Importar: `@use '../../../admin-theme' as t` y `@use '../../../admin-ui' as ui`
- Mixins: `ui.ev-page-title`, `ui.ev-card`, `ui.ev-toolbar`, `ui.ev-input`, `ui.ev-btn-primary`, `ui.ev-btn-ghost`, `ui.ev-table`, `ui.ev-alert-error`, `ui.ev-alert-info`, `ui.ev-modal-backdrop`, `ui.ev-modal`
- Variables: `t.$ev-muted`, `t.$ev-text`, `t.$ev-border`, `t.$ev-surface`, `t.$ev-focus`, `t.$ev-space`, `t.$ev-radius-lg`, `t.$ev-gradient-cta`
