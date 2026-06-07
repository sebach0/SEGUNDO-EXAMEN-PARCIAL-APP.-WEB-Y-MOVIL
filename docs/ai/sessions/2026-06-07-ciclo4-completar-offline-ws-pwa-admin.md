# Sesión 2026-06-07 — Ciclo 4: Completar los 4 puntos faltantes

## Resumen

Implementación de los 4 puntos pendientes del Ciclo #4 para cerrar el examen:

1. Unificación offline web (Opción A)
2. WebSocket en mobile Flutter
3. PWA formal en Angular
4. Monitor admin completo

---

## 1. Unificación offline web — Opción A (flujo real)

**Objetivo:** La cola offline del portal web Angular apunta ahora a `solicitudes_emergencia` (flujo real), no a la tabla `incidentes` de Ciclo 4 experimental.

**Backend:**
- `backend/app/modules/atencion/taller_emergencias/router.py`
  - Nuevo endpoint `POST /api/app/taller/emergencias/sync-web`
  - Procesa eventos offline con `solicitud_id`: ESTADO_CAMBIADO, TALLER_ACEPTO, TALLER_RECHAZO, OBSERVACION
  - ESTADO_CAMBIADO aplica el estado directamente en `SolicitudEmergencia` y emite WS
  - Los otros tipos se reconocen (no cambian BD — la aceptación formal es por cotizaciones)

**Frontend:**
- `frontend/src/app/core/models/ciclo4.models.ts`
  - `OfflineEvent` ahora tiene campo opcional `solicitud_id?: number`
  - Nuevos tipos: `SolicitudWebSyncPayload`, `SolicitudWebEventoPayload`, `SolicitudSyncResult`, `SolicitudSyncResultItem`
- `frontend/src/app/core/services/sync.service.ts`
  - Nuevo método `syncSolicitudWebEvents()` → `POST /api/app/taller/emergencias/sync-web`
- `frontend/src/app/taller/features/ciclo4/offline-incidents/workshop-incident-offline.component.ts`
  - Campo `incidenteId` reemplazado por `solicitudId`
  - Llama `syncSolicitudWebEvents()` (flujo real) en lugar del endpoint ciclo4/incidentes
  - `_entidad` = `'solicitud_evento'`

---

## 2. WebSocket en mobile Flutter

**Objetivo:** La pantalla de seguimiento se actualiza automáticamente vía WS sin pull-to-refresh manual.

**Dependencia agregada:**
- `pubspec.yaml`: `web_socket_channel: ^3.0.1`

**Archivos nuevos:**
- `mobile/lib/cliente/emergencias/data/emergencia_ws_service.dart`
  - `EmergenciaWsService`: conecta a `ws://HOST/ws/incidents/{solicitudId}?token=TOKEN`
  - Backoff exponencial de reconexión (1s → 30s máx)
  - Expone `Stream<WsSolicitudEvent>`
- `mobile/lib/cliente/emergencias/application/emergencia_ws_provider.dart`
  - `emergenciaWsProvider`: `StreamProvider.autoDispose.family<WsSolicitudEvent, int>`

**Archivo modificado:**
- `mobile/lib/cliente/emergencias/presentation/screens/emergencia_seguimiento_screen.dart`
  - Convertido de `ConsumerWidget` a `ConsumerStatefulWidget`
  - `ref.listen(emergenciaWsProvider(...))` → invalida `emergenciaSeguimientoProvider` en eventos relevantes
  - Banner de último evento WS (desaparece a los 4 s)
  - Punto indicador `_WsStatusDot` (verde/ámbar/rojo) en AppBar

---

## 3. PWA formal — Angular

**Objetivo:** La web Angular funciona como PWA instalable con Service Worker y caché offline.

**Dependencia instalada:**
- `@angular/service-worker@^17.3.0`

**Archivos nuevos:**
- `frontend/src/manifest.webmanifest`
  - name, short_name, display: standalone, theme_color: #1e293b
  - Shortcuts: solicitudes y portal taller
- `frontend/src/ngsw-config.json`
  - `assetGroups`: caché prefetch del app shell
  - `dataGroups`: caché de APIs con distintas estrategias (auth → freshness, catálogo → performance)

**Archivos modificados:**
- `frontend/angular.json`
  - `"serviceWorker": "src/ngsw-config.json"` en opciones de build
  - `manifest.webmanifest` añadido a `assets`
- `frontend/src/index.html`
  - `<link rel="manifest" href="manifest.webmanifest">`
  - Meta tags PWA: theme-color, apple-mobile-web-app-*, application-name, description
- `frontend/src/app/app.config.ts`
  - `provideServiceWorker('ngsw-worker.js', { enabled: !isDevMode(), registrationStrategy: 'registerWhenStable:30000' })`

**Nota:** El Service Worker solo se activa en build de producción (`ng build --configuration production`). En desarrollo (`ng serve`) está desactivado para no interferir con hot-reload.

---

## 4. Monitor Admin Completo

**Objetivo:** El panel admin muestra solicitudes activas REALES y recibe eventos en tiempo real vía WS sin polling.

**Backend:**
- `backend/app/modules/ciclo4/websocket/manager.py`
  - `ADMIN_CHANNEL_ID = 0` — canal especial
  - `broadcast_to_incident` ahora también retransmite al canal admin
  - Nuevo método `broadcast_to_admin(event_type, message, payload)` para eventos propios del canal admin
  - Propiedad `admin_connected` para contar conexiones activas
- `backend/app/modules/ciclo4/incidentes/router.py`
  - Nuevo `WS /ws/admin/feed` — conecta al canal ADMIN_CHANNEL_ID
  - Valida JWT, acepta cualquier usuario autenticado
  - Envía handshake `ADMIN_CONNECTED` al conectar
  - Nuevo `GET /incidents/admin/solicitudes-activas`
    - Lista `SolicitudEmergencia` en estados: PENDIENTE, BUSCANDO_TALLER, TALLER_ASIGNADO, EN_CAMINO, EN_ATENCION
    - Requiere permiso `solicitudes_emergencia:leer`

**Frontend:**
- `admin-realtime-monitor.component.ts` — reescrito completamente
  - Llama `GET /api/incidents/admin/solicitudes-activas` para lista inicial
  - Conecta a `WS /ws/admin/feed` para feed en tiempo real
  - `ESTADO_CAMBIADO` → actualiza fila en la tabla inmediatamente (sin recargar)
  - Si estado = FINALIZADO/CANCELADO → recarga la lista completa en 2 s
  - Reconexión automática con backoff exponencial
- `admin-realtime-monitor.component.html` — reescrito con sección feed
  - Tabla de solicitudes activas (ID, estado, taller, técnico, ETA, fechas)
  - Feed de eventos en tiempo real (últimos 50, scroll interno)
  - Indicador WS (punto verde/ámbar/rojo animado)
- `admin-realtime-monitor.component.scss`
  - Estilos para `.arm__events`, `.arm__event`, `.ws-dot`, animación pulse

---

## Flujo end-to-end Ciclo 4 — estado final

```
Cliente (mobile Flutter)
  → Crea solicitud → POST /api/app/cliente/emergencias
  → Seguimiento en tiempo real → WS /ws/incidents/{id}
  → RefreshIndicator mantiene como fallback

Taller (Angular web)
  → Bandeja de solicitudes → GET /api/app/taller/emergencias/bandeja/disponibles
  → Cotizaciones → POST /api/app/taller/cotizaciones/solicitudes/{id}
  → Offline: IndexedDB → sync POST /api/app/taller/emergencias/sync-web

Admin (Angular web)
  → Solicitudes activas → GET /api/incidents/admin/solicitudes-activas
  → Feed real-time → WS /ws/admin/feed
  → KPIs → GET /api/kpis/...

Backend emite WS
  → broadcast_to_incident(solicitud_id) → cliente + admin reciben el evento
  → ETA actualizado, retraso, estado cambiado
```

---

## Comandos para aplicar cambios

```bash
# Backend
docker compose exec backend alembic upgrade head   # no hay nueva migración

# Frontend (instalar SW ya ejecutado)
cd frontend
npm install  # asegura @angular/service-worker
ng build --configuration production  # el SW solo activa en prod

# Mobile (web_socket_channel ya instalado)
cd mobile
flutter pub get
flutter run
```
