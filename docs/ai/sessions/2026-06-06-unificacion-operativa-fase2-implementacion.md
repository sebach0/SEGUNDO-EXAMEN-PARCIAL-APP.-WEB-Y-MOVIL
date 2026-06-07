# Sesión 2026-06-06 — Unificación operativa fase 2 (implementación)

## Objetivo

Completar el plan de unificación del flujo real (`solicitudes_emergencia`) con KPIs, ETA/retraso, offline móvil y eventos WebSocket.

## Hecho en esta sesión

### Etapa 1 — BD y modelos ✅
- Migración `0017_unificacion_operativa.sql` / Alembic `0009_unificacion_operativa`.
- **Aplicada en Docker:** `alembic upgrade head` → revisión `0009_unificacion_operativa`.

### Etapa 2 — Backend reglas ✅
- KPIs leen `SolicitudEmergencia` (no tabla paralela `incidentes`).
- Timestamps de ciclo de vida, bandeja filtrada, cancelación notifica al taller.
- Endpoint `POST /api/app/cliente/emergencias/sync` con `client_uuid` anti-duplicado.

### Etapa 3 — ETA + retraso + WS ✅
- `eta_service.py`: `emit_eta_actualizado_ws`, `emit_servicio_retrasado_ws`.
- Emisión WS al registrar ETA (asignación técnico, EN_CAMINO fallback, cotización seleccionada).
- Push + WS al detectar retraso ≥ 5 min.
- Angular: tipos `ETA_ACTUALIZADO` / `SERVICIO_RETRASADO` en `ciclo4.models.ts` y filtros en `realtime.service.ts`.

### Etapa 4 — Offline móvil ✅
- Cola `OfflineEmergenciaQueue` + UUID v4 válido.
- `OfflineEmergenciaSyncListener` en `app.dart` (sync al iniciar y al volver al foreground).
- Wizard: si falla red al crear, encola borrador y muestra SnackBar.

### Etapa 6 — Flutter retraso ✅ (previo + verificado)
- Seguimiento expone `minutos_retraso`, `servicio_retrasado`; `EtaLlegadaCard` muestra demora.

### Etapa 7 — Tests ✅
- `backend/tests/test_eta_service.py` (4 tests, sin BD real).

## Pendiente / siguiente iteración

- Reportes PDF/Excel operacionales (no implementados).
- PWA Angular offline unificada (cola propia Ciclo 4 sigue separada).
- ETA dinámico por distancia GPS (opcional).
- Monitor admin WS: conectar por `solicitud_id` (canal unificado) en lugar de solo tabla `incidentes`.
- Cotizaciones cliente web Angular (si aplica al alcance del examen).

## Comandos útiles

```bash
# Migración (BD existente)
docker compose exec backend alembic upgrade head

# Tests ETA
cd backend && python -m pytest tests/test_eta_service.py -q

# Análisis mobile
cd mobile && flutter analyze lib/core/services/offline_emergencia_sync_listener.dart
```
