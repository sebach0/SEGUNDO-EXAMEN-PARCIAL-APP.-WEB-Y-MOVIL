# Sesión 2026-06-06 — Ciclo 4 Segunda Fase: Servicios, Cotizaciones, Cancelación, KPIs, Seguro

## Objetivo

Implementar todos los puntos restantes del Ciclo 4 en **Backend (FastAPI)** y **Frontend (Angular)**, sin tocar el Ciclo 5. La prioridad fue:

1. **Backend**: migraciones + modelos + servicios + routers
2. **Frontend Angular**: componentes y conexión a endpoints reales

---

## Lo que se implementó

### Base de Datos — Migración 0016

Archivo: `backend/migrations/0016_ciclo4_servicios_cotizaciones.sql`
Alembic: `backend/alembic/versions/0008_ciclo4_servicios_cotizaciones.py` (revision `0008_ciclo4_servicios_cot`)

**Tablas nuevas:**
- `servicios_catalogo` — catálogo de 10 tipos de servicio (chaperío, llantería, grúa, etc.)
- `taller_servicios` — N:M entre talleres y servicios_catalogo
- `cotizaciones` — cotización formal de un taller para una solicitud
- `cotizacion_items` — líneas de detalle de una cotización

**Columnas agregadas:**
- `talleres.tiene_grua BOOLEAN DEFAULT FALSE`
- `solicitudes_emergencia.motivo_cancelacion TEXT`
- `solicitudes_emergencia.cancelado_en TIMESTAMP`
- `pagos.responsable_pago ENUM(CLIENTE/SEGURO/MIXTO)`
- `pagos.monto_seguro, numero_poliza, aseguradora`

**Tipos ENUM nuevos:**
- `estado_cotizacion` (ENVIADA, ACEPTADA, RECHAZADA, EXPIRADA)
- `responsable_pago` (CLIENTE, SEGURO, MIXTO)

**Permisos nuevos:** `cotizaciones:crear`, `cotizaciones:leer`, `cotizaciones:aceptar`, `servicios:gestionar`, `kpis:leer`

---

### Backend — Modelos

- `ServicioCatalogo`, `TallerServicio` → `backend/app/modules/talleres_y_tecnicos/talleres/models.py`
- `Cotizacion`, `CotizacionItem` → `backend/app/modules/cotizaciones/models.py`
- `ResponsablePagoEnum` + campos → `backend/app/modules/pagos_y_comisiones/pagos/models.py`
- `motivo_cancelacion`, `cancelado_en` → `backend/app/modules/incidentes/emergencias/models.py`
- `tiene_grua` → `Taller` model

### Backend — Servicios y Routers

| Módulo | Archivo | Endpoints |
|--------|---------|-----------|
| Servicios taller | `talleres/service.py` + `talleres/router.py` | `GET /talleres/catalogo/servicios`, `GET /PUT /{id}/servicios`, `PATCH /{id}/grua` |
| Cotizaciones | `cotizaciones/service.py` + `router.py` | `GET/POST /cotizaciones/solicitudes/{id}`, `POST .../cotizacion/{id}/seleccionar` |
| Cancelación | `emergencias/service/solicitudes.py` + `router.py` | `POST /app/cliente/emergencias/{id}/cancelar` |
| KPIs | `kpis/service.py` + `router.py` | `GET /api/kpis/summary?desde=&hasta=&taller_id=` |

### Backend — `main.py`

Registrados:
```python
from app.modules.cotizaciones.router import router as cotizaciones_router
from app.modules.kpis.router import router as kpis_router
app.include_router(cotizaciones_router, prefix=PREFIX)
app.include_router(kpis_router, prefix=PREFIX)
```

### Frontend Angular — Nuevos archivos

| Archivo | Descripción |
|---------|-------------|
| `core/models/cotizacion.models.ts` | Interfaces: `Cotizacion`, `ServicioCatalogo`, `KpiSummary` |
| `core/services/cotizacion.service.ts` | HTTP service para cotizaciones, servicios y KPIs |
| `taller/features/servicios/taller-servicios.component.*` | Gestión de servicios del taller (checkboxes + grúa) |
| `taller/features/cotizaciones/taller-cotizaciones.component.*` | Proponer cotizaciones + ver estado |
| `admin/features/ciclo4/kpis/operational-dashboard.component.ts` | KPI dashboard conectado a `GET /api/kpis/summary` |

### Frontend Angular — Rutas nuevas

```typescript
{ path: 'servicios', loadComponent: () => TallerServiciosComponent }
{ path: 'cotizaciones/solicitud/:solicitudId', loadComponent: () => TallerCotizacionesComponent }
```

Nav item agregado en `taller-shell.component.ts`:
- `Mis servicios → /taller/panel/servicios`

---

## Flujo de cotizaciones

```
Cliente crea solicitud_emergencia
    → Solicitud llega a bandeja de talleres (CU25 existente)
    → Taller puede proponer cotización: POST /cotizaciones/solicitudes/{id}
    → Cliente lista cotizaciones: GET /cotizaciones/solicitudes/{id}
    → Cliente selecciona: POST .../cotizacion/{id}/seleccionar
        → Cotización seleccionada → ACEPTADA
        → Demás cotizaciones ENVIADAS → EXPIRADA
        → solicitudes_emergencia.taller_id = taller seleccionado
        → solicitudes_emergencia.estado → TALLER_ASIGNADO
```

## Flujo de cancelación (legacy)

```
POST /api/app/cliente/emergencias/{id}/cancelar
    Body: { "motivo": "..." }
    → estado → CANCELADA
    → motivo_cancelacion guardado
    → cancelado_en = NOW()
    → historial de estado registrado
    → notificación push al taller asignado (si hay)
```

## KPIs endpoint

`GET /api/kpis/summary?desde=YYYY-MM-DD&hasta=YYYY-MM-DD`

Métricas calculadas desde `incidentes` (Ciclo 4):
- Tiempo promedio asignación (reportado_en → asignado_en)
- Tiempo promedio llegada (asignado_en → en_atencion_en)
- Tiempo promedio atención total
- Incidentes activos / finalizados / cancelados
- Cumplimiento SLA (%)
- Incidentes por tipo
- Zonas con más incidentes (top 10)
- Talleres más eficientes (menor tiempo promedio, top 10)

**Filtros:** tenant_id (automático del JWT), desde, hasta, taller_id

---

## Estado final de los puntos del Ciclo 4

| Punto | Estado |
|-------|--------|
| Tiempo real WebSocket + tracking | ✅ Completo (sesión anterior) |
| Offline móvil + web PWA | ✅ Completo (sesión anterior) |
| KPIs reales desde BD | ✅ Completo (esta sesión) |
| Selección inteligente de taller (AI rank) | ✅ Existía |
| Servicios del taller (catálogo) | ✅ Completo (esta sesión) |
| Multi-tenant (Ciclo 4) | ✅ Completo (sesión anterior) |
| Cotizaciones | ✅ Completo (esta sesión) |
| Cancelación legacy | ✅ Completo (esta sesión) |
| Responsable de pago / seguro | ✅ Modelo preparado (esta sesión) |
| Frontend Angular cotizaciones | ✅ Completo (esta sesión) |
| Frontend Angular servicios taller | ✅ Completo (esta sesión) |
| Frontend Angular KPI dashboard | ✅ Conectado a endpoint real |

## Pendiente (Ciclo 5 o Mobile)

- Cancellación via app móvil Flutter (botón en UI)
- Listado de cotizaciones para cliente en app móvil
- Interfaz de selección de cotización en app móvil
- Gestión de responsable de pago / seguro en UI

---

## Notas técnicas

- La migración Alembic usa revision ID `0008_ciclo4_servicios_cot` (≤32 chars por limitación de columna)
- Los KPIs filtran automáticamente por `tenant_id` del JWT del usuario autenticado
- La selección de cotización usa `SELECT ... WITH FOR UPDATE` para evitar race conditions
- El endpoint de cancelación registra historial de estado y envía push notification al taller
