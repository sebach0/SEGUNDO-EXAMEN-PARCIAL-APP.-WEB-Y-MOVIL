# app/main.py
# =========================================================
# Punto de entrada principal de la aplicación FastAPI
# Aquí se registran todos los routers y se configura CORS
# =========================================================
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings

_log = logging.getLogger(__name__)

# Evita dos seeds concurrentes en el mismo proceso (p. ej. uvicorn --reload disparando lifespan dos veces).
_startup_seed_lock = asyncio.Lock()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if (
        settings.SEED_ADMIN_ON_START
        or settings.SEED_CLIENTE_ON_START
        or settings.SEED_TALLER_ON_START
        or settings.SEED_TECNICO_ON_START
        or settings.SEED_DEMO_SANTA_CRUZ_ON_START
        or settings.SEED_DEMO_MEDIA_PRIORIDAD_ON_START
        or settings.SEED_STRESS_VISUAL_ON_START
    ):
        from app.core.database import AsyncSessionLocal
        from app.seeds.dev_admin import ensure_baseline_rol_permisos, ensure_dev_admin
        from app.seeds.dev_catalogos_vehiculo import ensure_catalogos_vehiculo_demo
        from app.seeds.dev_cliente import ensure_dev_cliente
        from app.seeds.dev_tecnico import ensure_dev_tecnico
        from app.seeds.dev_taller import ensure_dev_taller
        from app.seeds.dev_demo_media_prioridad import ensure_demo_media_prioridad
        from app.seeds.dev_demo_santa_cruz import ensure_demo_santa_cruz_datos
        from app.seeds.dev_stress_visual import ensure_stress_visual_seed

        async with _startup_seed_lock:
            # Tras `docker compose up`, Postgres puede reiniciarse al terminar init.sql;
            # un intento único suele dar Connection refused aunque el healthcheck ya sea "healthy".
            last_err: BaseException | None = None
            for attempt in range(1, 9):
                try:
                    async with AsyncSessionLocal() as session:
                        await ensure_baseline_rol_permisos(session)
                        await ensure_catalogos_vehiculo_demo(session)
                        if settings.SEED_ADMIN_ON_START:
                            await ensure_dev_admin(session, require_enabled_flag=False)
                        if settings.SEED_CLIENTE_ON_START:
                            await ensure_dev_cliente(session, require_enabled_flag=False)
                        if settings.SEED_TALLER_ON_START:
                            await ensure_dev_taller(session, require_enabled_flag=False)
                        if settings.SEED_TECNICO_ON_START:
                            await ensure_dev_tecnico(session, require_enabled_flag=False)
                        if settings.SEED_DEMO_SANTA_CRUZ_ON_START:
                            await ensure_demo_santa_cruz_datos(session, require_enabled_flag=False)
                        if settings.SEED_DEMO_MEDIA_PRIORIDAD_ON_START:
                            await ensure_demo_media_prioridad(session, require_enabled_flag=False)
                        if settings.SEED_STRESS_VISUAL_ON_START:
                            await ensure_stress_visual_seed(session, require_enabled_flag=False)
                        await session.commit()
                    break
                except Exception as e:
                    last_err = e
                    _log.warning(
                        "Seeds intento %s/8: %s — reintento en 2s",
                        attempt,
                        e,
                    )
                    await asyncio.sleep(2)
            else:
                _log.error(
                    "Seeds (admin/cliente/taller/técnico) no pudieron tras 8 intentos. "
                    "Manual: docker compose exec backend python -m app.seeds",
                    exc_info=last_err,
                )
    yield

# ── Importar todos los routers si ────────────────────────────────
from app.modules.acceso_y_administracion.auth.router import auth_router
from app.modules.acceso_y_administracion.permisos.router import permisos_router
from app.modules.acceso_y_administracion.roles.router import roles_router
from app.modules.acceso_y_administracion.usuarios.router import router as usuarios_router, clientes_router
from app.modules.clientes_y_vehiculos.vehiculos.router import router as vehiculos_router
from app.modules.talleres_y_tecnicos.talleres.router import router, especialidades_router, tecnicos_router
from app.modules.acceso_y_administracion.bitacora.router import router as bitacora_router
from app.modules.acceso_y_administracion.admin_finanzas.router import (
    router as admin_finanzas_router,
)
from app.modules.talleres_y_tecnicos.taller_responsable.router import router as taller_responsable_router
from app.modules.atencion.taller_emergencias.router import router as taller_emergencias_router
from app.modules.clientes_y_vehiculos.clientes.router import router as clientes_app_router
from app.modules.incidentes.emergencias.router import router as emergencias_router
from app.modules.comunicacion_y_notificaciones.comunicaciones.router import (
    cliente_router as comunicaciones_cliente_router,
    emergencias_mensajes_cliente_router,
    tecnico_router as comunicaciones_tecnico_router,
)
from app.modules.talleres_y_tecnicos.tecnico.router import router as tecnico_router
from app.modules.pagos_y_comisiones.pagos.router import emergencias_pagos_cliente_router
from app.modules.ai.router import router as ai_router

# ── Crear aplicación ─────────────────────────────────────────
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    docs_url="/docs",          # Swagger UI
    redoc_url="/redoc",        # ReDoc
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────
# En producción, CORS_ORIGINS debe ser solo el dominio del frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Registrar routers bajo el prefijo /api ─────────────────
# Modificado para remover el v1
PREFIX = settings.API_PREFIX

app.include_router(auth_router, prefix=PREFIX)
app.include_router(roles_router, prefix=PREFIX)
app.include_router(permisos_router, prefix=PREFIX)
app.include_router(usuarios_router, prefix=PREFIX)
app.include_router(clientes_router, prefix=PREFIX)
app.include_router(vehiculos_router, prefix=PREFIX)
app.include_router(router, prefix=PREFIX)           # talleres
app.include_router(especialidades_router, prefix=PREFIX)
app.include_router(tecnicos_router, prefix=PREFIX)
app.include_router(bitacora_router, prefix=PREFIX)
app.include_router(admin_finanzas_router, prefix=PREFIX)
app.include_router(taller_responsable_router, prefix=PREFIX)
app.include_router(taller_emergencias_router, prefix=PREFIX)
app.include_router(clientes_app_router, prefix=PREFIX)
app.include_router(emergencias_router, prefix=PREFIX)
app.include_router(comunicaciones_cliente_router, prefix=PREFIX)
app.include_router(emergencias_mensajes_cliente_router, prefix=PREFIX)
app.include_router(comunicaciones_tecnico_router, prefix=PREFIX)
app.include_router(tecnico_router, prefix=PREFIX)
app.include_router(emergencias_pagos_cliente_router, prefix=PREFIX)
app.include_router(ai_router, prefix=PREFIX)

# Archivos de evidencia (foto/audio) servidos en HTTPS/HTTP según el entorno. si
_evid_dir = settings.evidencias_upload_dir
_evid_dir.mkdir(parents=True, exist_ok=True)
app.mount(
    f"{PREFIX}/media/evidencias",
    StaticFiles(directory=str(_evid_dir)),
    name="evidencias_media",
)


# ── Health check ─────────────────────────────────────────────
@app.get("/health", tags=["Sistema"])
async def health_check():
    """Endpoint de verificación de salud — útil para load balancers y Docker healthcheck."""
    return {"status": "ok", "version": settings.VERSION, "environment": settings.ENVIRONMENT}


# ── Root ─────────────────────────────────────────────────────
@app.get("/", tags=["Sistema"])
async def root():
    return {
        "proyecto": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
    }
