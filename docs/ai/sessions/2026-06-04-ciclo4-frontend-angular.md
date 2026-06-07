# Sesión 2026-06-04 — Ciclo 4: Frontend Angular

## Resumen

Implementación completa del frontend Angular para el Ciclo #4 del Examen 2.
Se respetó la arquitectura existente (Angular 17 standalone components, SCSS custom).

## Estructura encontrada

- **Angular 17** con standalone components (`standalone: true` en todos).
- **Sin NgModules** — todo usa `loadComponent` / `loadChildren` lazy.
- **Interceptor funcional** `api-auth.interceptor.ts` — Bearer auto en `/api/*`.
- **Dos auth services**: `TallerAuthService` (token `ev_taller_access`) y `AdminAuthService`.
- **SCSS custom**: `_admin-theme.scss` + `_admin-ui.scss` con mixins reutilizables, paleta oscura.
- **Sin PWA**, sin WebSocket, sin IndexedDB previo.

## Archivos creados

### Modelos
- `frontend/src/app/core/models/ciclo4.models.ts`

### Servicios (core)
- `frontend/src/app/core/services/network.service.ts`
- `frontend/src/app/core/services/offline-queue.service.ts` (IndexedDB)
- `frontend/src/app/core/services/realtime.service.ts` (WebSocket con reconexión exponencial)
- `frontend/src/app/core/services/incident.service.ts`
- `frontend/src/app/core/services/sync.service.ts`

### Componentes Taller (Ciclo 4)
- `taller/features/ciclo4/realtime-panel/` — RealtimeStatusPanelComponent
- `taller/features/ciclo4/incident-tracking/` — IncidentRealtimeTrackingComponent (CU36/CU37)
- `taller/features/ciclo4/offline-incidents/` — WorkshopIncidentOfflineComponent (CU41)
- `taller/features/ciclo4/sync-status/` — SyncStatusComponent (CU40/CU42)

### Componentes Admin (Ciclo 4)
- `admin/features/ciclo4/realtime-monitor/` — AdminRealtimeMonitorComponent
- `admin/features/ciclo4/kpis/` — OperationalDashboardComponent

## Archivos modificados

- `app.component.ts/html/scss` — Banner global offline/sync
- `core/interceptors/api-auth.interceptor.ts` — Soporte ciclo4 `/incidents`, `/sync`, `/tenants`
- `taller/taller.routes.ts` — 3 rutas ciclo4 añadidas
- `admin/admin.routes.ts` — 2 rutas ciclo4 añadidas
- `taller/shell/taller-shell.component.ts` — Nav items ciclo4
- `admin/shell/admin-shell.component.ts` — Nav items ciclo4

## Rutas nuevas

### Taller
- `/taller/panel/ciclo4/incidentes/:id/tracking` → IncidentRealtimeTrackingComponent
- `/taller/panel/ciclo4/offline-incidents` → WorkshopIncidentOfflineComponent
- `/taller/panel/ciclo4/sync/status` → SyncStatusComponent

### Admin
- `/admin/panel/ciclo4/realtime-monitor` → AdminRealtimeMonitorComponent
- `/admin/panel/ciclo4/kpis` → OperationalDashboardComponent

## PWA

No se configuró el service worker de Angular aún (requiere `npm install @angular/pwa`).
El banner offline funciona vía `window.online/offline` sin necesidad de service worker.

Para activar PWA completa:
```bash
cd frontend
ng add @angular/pwa
```

## Endpoints backend requeridos

| Endpoint | Método | Componente que lo usa |
|----------|--------|-----------------------|
| `/api/incidents` | GET | AdminRealtimeMonitorComponent |
| `/api/incidents/:id` | GET | IncidentRealtimeTrackingComponent |
| `/api/incidents/:id/tracking` | GET/POST | IncidentRealtimeTrackingComponent |
| `/api/incidents/:id/status` | PATCH | IncidentService |
| `/api/sync/web/events` | POST | SyncService / WorkshopIncidentOfflineComponent |
| `/api/sync/status` | GET | SyncStatusComponent |
| `/ws/incidents/:id?token=...` | WS | RealtimeService |
| `/api/kpis/summary` | GET | OperationalDashboardComponent (TODO) |
