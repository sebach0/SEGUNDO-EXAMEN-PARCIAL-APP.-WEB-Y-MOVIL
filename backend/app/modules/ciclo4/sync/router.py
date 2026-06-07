# Router — Ciclo 4: Sincronización Offline
# =========================================================
# POST /sync/incidents      — CU39: sincronizar emergencia offline móvil
# GET  /sync/status         — CU40: estado de sincronizaciones
# POST /sync/web/events     — CU41/CU42: sincronizar eventos web offline
# =========================================================
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_permission
from app.modules.acceso_y_administracion.usuarios.models import Usuario
from app.modules.ciclo4.deps import get_tenant_id
from app.modules.ciclo4.sync import service
from app.modules.ciclo4.sync.schemas import (
    SyncIncidenteIn,
    SyncIncidenteResultado,
    SyncStatusItemRead,
    WebSyncIn,
    WebSyncResultado,
)

sync_router = APIRouter(
    prefix="/sync",
    tags=["Sincronización Offline (Ciclo 4)"],
)


@sync_router.post(
    "/incidents",
    response_model=SyncIncidenteResultado,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("sync:usar"))],
    summary="CU39 — Sincronizar emergencia offline (móvil)",
)
async def sincronizar_incidente(
    body: SyncIncidenteIn,
    current_user: Usuario = Depends(get_current_user),
    tenant_id: int = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    CU39: Recibe un incidente capturado offline en la app móvil.
    Anti-duplicado por (tenant_id, client_uuid): si ya existe, devuelve el incidente
    existente sin crear otro. Si es nuevo, lo crea con origen=OFFLINE.

    La app puede llamar este endpoint N veces con el mismo client_uuid de forma segura.
    """
    return await service.sincronizar_incidente_movil(body, current_user.id, tenant_id, db)


@sync_router.get(
    "/status",
    response_model=list[SyncStatusItemRead],
    dependencies=[Depends(require_permission("sync:usar"))],
    summary="CU40 — Consultar estado de sincronizaciones",
)
async def estado_sincronizacion(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    CU40: Devuelve la lista de registros de sincronización del usuario autenticado.
    Incluye: client_uuid, entidad, estado_local, intentos, ultimo_error,
             incidente_id, registrado_local_en, sincronizado_en.
    """
    return await service.get_estado_sincronizacion(current_user.id, db)


@sync_router.post(
    "/web/events",
    response_model=WebSyncResultado,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("sync:usar"))],
    summary="CU41/CU42 — Sincronizar eventos offline web (Angular PWA)",
)
async def sincronizar_eventos_web(
    body: WebSyncIn,
    current_user: Usuario = Depends(get_current_user),
    tenant_id: int = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    CU41/CU42: Procesa una lista de eventos capturados offline por Angular PWA.
    Válida anti-duplicado por client_uuid. Aplica cambios reales en incidentes.
    Responde con resumen: sincronizados vs. con error.
    """
    return await service.sincronizar_eventos_web(body.eventos, current_user.id, tenant_id, db)
