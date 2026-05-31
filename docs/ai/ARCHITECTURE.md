# ARCHITECTURE.md
# =========================================================
# Arquitectura del Sistema — Ciclo 1
# =========================================================

## Patrón Arquitectónico

**Arquitectura Modular por Dominio** (Domain-driven Modular Architecture).

Cada módulo encapsula sus propios:
- `models.py` — entidades SQLAlchemy
- `schemas.py` — contratos Pydantic (request/response)
- `service.py` — lógica de negocio (pura, testeable)
- `router.py` — endpoints FastAPI (solo recibe y delega)

## Árbol de módulos Backend

```
app/
├── core/              ← Transversal a todos los módulos
│   ├── config.py      ← Settings desde variables de entorno
│   ├── database.py    ← Engine + sesión asíncrona
│   ├── security.py    ← bcrypt + JWT
│   └── dependencies.py ← get_current_user, require_permission
├── modules/
│   ├── acceso_y_administracion/  ← auth, roles, permisos, usuarios, bitácora (imports `app.modules.acceso_y_administracion.*`)
│   ├── comunicacion_y_notificaciones/  ← CU19, CU21 (y routers cliente/técnico)
│   │   ├── comunicaciones/ ← Routers HTTP que agrupan FCM + notif + mensajes
│   │   ├── notificaciones/ ← In-app + orquestación push
│   │   ├── dispositivos_push/ ← Tokens FCM, firebase-admin
│   │   └── mensajes_solicitud/ ← Chat por solicitud (cliente ↔ técnico)
│   ├── clientes_y_vehiculos/  ← CU1 + CU10 (dominio cliente + vehículo)
│   │   ├── clientes/  ← ORM `Cliente`, schemas admin + `schemas_movil`, `router` `/app/cliente`, `service/`
│   │   └── vehiculos/ ← Catálogos + vehículos (`/vehiculos`)
│   ├── talleres_y_tecnicos/  ← CU22/CU23 + app técnico
│   │   ├── talleres/      ← CRUD `/talleres`, `/especialidades`, `/tecnicos`
│   │   ├── taller_responsable/ ← Portal `/app/taller`
│   │   └── tecnico/       ← `/app/tecnico/emergencias` + `service/`
│   ├── atencion/        ← Atención taller (CU24–CU31 en routers)
│   │   └── taller_emergencias/ ← `/app/taller/emergencias` (bandeja, asignación, comisiones…)
│   ├── incidentes/    ← Paquete análisis «Incidentes» (CU11–CU18)
│   │   └── emergencias/ ← Cliente: `/app/cliente/emergencias` (solicitudes, seguimiento, ubicaciones, evidencias)
│   ├── pagos/         ← Pagos emergencias (cliente)
│   └── ai/            ← Inferencia asistida: proxy a worker, reglas, prioridad
└── main.py            ← Registro de routers + CORS
```

## App móvil Flutter (`mobile/lib/`)

Módulos por actor (misma idea de capas: application / data / domain / presentation):

```
lib/cliente/     ← Cliente: auth portal, vehículos, perfil; Dio + tokens en ApiClient
lib/tecnico/     ← Técnico/responsable: auth, home, perfil, placeholders; tokens en TecnicoApiClient
lib/core/        ← app_env (.env), api_constants, theme, api_error compartido
```

El **go_router** vive en `cliente/presentation/router/cliente_go_router.dart` y concentra rutas `/splash`, `/cliente/*`, `/tecnico/*`.

## Capas del sistema

```
Angular/Flutter
     ↓ JWT Bearer
FastAPI Router         ← solo valida request y delega
     ↓
FastAPI Service        ← lógica de negocio aquí
     ↓
SQLAlchemy Models      ← mapeo a PostgreSQL
     ↓
PostgreSQL             ← tablas + índices + ENUMs
```

## Esquema y migraciones (Docker)

En desarrollo con `docker-compose`, el contenedor Postgres ejecuta los SQL de `backend/migrations/` en orden (`init`, `0002`–`0004`, `0006` como `05_`, ver `docker-compose.yml`). Scripts adicionales en `scripts/` pueden aplicarse a mano en otros entornos; el modelo **debe** coincidir con la BD (ej. `solicitudes_emergencia.tecnico_asignado_at` alineado con `emergencias/models.py`). Volúmenes ya creados no re-ejecutan init: parches idempotentes (`0006`) o `ALTER` manual. Ver `DECISIONS_LOG` **DEC-009**.

## Servicio de inferencia (`ai-inference`)

Contenedor **opcional** (perfil Compose `ai`) definido en `docker-compose.yml`, build con **contexto** `./services/ai-inference` y `Dockerfile` en esa carpeta (contexto acotado; ver `docs/ai/DOCKER_BUILD_OPTIMIZATION.md`). Expone API HTTP interna (p. ej. visión en `/internal/vision/analyze`). El backend usa `AI_INFERENCE_BASE_URL` (p. ej. `http://ai-inference:8080`) y `httpx` para delegar audio/imagen. Override `docker-compose.ai-custom-model.yml` ajusta YOLO a **clasificación** con peso montado desde el host. Ver `DECISIONS_LOG` **DEC-010** y `HANDOFF_LATEST.md`.

## Patrón de auditoría

La función `registrar_accion()` en `acceso_y_administracion/bitacora/service.py`
es el único punto de escritura a la bitácora.
Todos los servicios la llaman después de cada operación exitosa.

## Autenticación

JWT con dos tokens:
- `access_token`: corta duración (60 min), para llamadas a la API
- `refresh_token`: larga duración (7 días), con JTI rastreable en BD
- `sesiones`: tabla en BD que permite revocar tokens individualmente

## Principios aplicados

- **No hardcodear**: todo vía variables de entorno
- **Soft delete**: usuarios se desactivan, no se eliminan
- **Async by default**: SQLAlchemy asyncio + asyncpg
- **Separación de responsabilidades**: router ≠ service ≠ model
