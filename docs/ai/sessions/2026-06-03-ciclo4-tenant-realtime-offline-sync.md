# Sesión 2026-06-03 — Ciclo 4: Multi-tenant + Tiempo Real + Offline Sync

## Resumen

Implementación completa de la infraestructura backend para el **Ciclo #4** del Examen 2 Parcial.

## Archivos creados

### Migración SQL y Alembic
- `backend/migrations/0015_ciclo4_tenants_incidentes.sql` — DDL completo
- `backend/alembic/versions/0007_ciclo4_tenants_incidentes.py` — Alembic revision

### Módulo `app/modules/ciclo4/`
```
ciclo4/
  deps.py                  — dependencia get_tenant_id
  tenants/
    models.py, schemas.py, service.py, router.py
  incidentes/
    models.py, schemas.py, service.py, router.py (REST + WebSocket)
  websocket/
    manager.py             — ConnectionManager singleton
  sync/
    models.py, schemas.py, service.py, router.py
```

### Tests
- `backend/tests/test_ciclo4.py` — 23 tests (23/23 pasan)

## Archivos modificados
- `app/modules/acceso_y_administracion/usuarios/models.py` — `tenant_id` nullable
- `app/db_metadata.py` — importa modelos Ciclo 4
- `app/main.py` — registra routers Ciclo 4

## Tablas nuevas
| Tabla | Propósito |
|-------|-----------|
| tenants | Raíz aislamiento SaaS |
| tipos_incidente | Catálogo BATERIA/LLANTA/MOTOR/CHOQUE/OTROS |
| zonas | Zonas geográficas por tenant |
| incidentes | Incidente v2 (ciclo de vida + timestamps + offline) |
| incidente_taller | Asignación taller ↔ incidente |
| incidente_estado_historial | Auditoría de cada cambio de estado |
| incidente_tracking | Puntos GPS del técnico |
| eventos_tiempo_real | Log persistente de eventos WebSocket |
| sincronizacion_offline | Cola anti-duplicado (client_uuid) |
| errores_sincronizacion | Log de intentos fallidos |

## Endpoints nuevos

| Método | Ruta | CU |
|--------|------|----|
| POST | /api/incidents | CU11 v2 |
| GET | /api/incidents | listar míos |
| GET | /api/incidents/{id} | CU36 (polling) |
| PATCH | /api/incidents/{id}/status | CU37 |
| GET | /api/incidents/{id}/tracking | CU36 (GPS) |
| POST | /api/incidents/{id}/tracking | CU37 (GPS) |
| WS | /api/ws/incidents/{id} | CU36/CU37 |
| POST | /api/sync/incidents | CU39 |
| GET | /api/sync/status | CU40 |
| POST | /api/sync/web/events | CU41/CU42 |
| GET | /api/tenants | admin |
| POST | /api/tenants | admin |

## Estrategia anti-rotura
- `solicitudes_emergencia` (Ciclo 1-3) NO fue modificada
- Todos los cambios son adiciones (tablas nuevas, columna nullable en usuarios)
- `get_tenant_id` retorna `user.tenant_id or 1` (retrocompatible)

## Pendiente para Ciclo 5
- Dashboard KPIs (kpi_snapshots)
- Cotizaciones y selección de taller
- Pagos integrados con Stripe/simulado
- Módulo analytics
