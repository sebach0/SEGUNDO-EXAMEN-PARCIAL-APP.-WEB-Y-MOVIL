# API app técnico — emergencias (ciclo 3 fase 3: CU32–CU35, script 008).
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.modules.comunicacion_y_notificaciones.mensajes_solicitud.schemas import MensajeSolicitudCreateIn, MensajeSolicitudRead
from app.modules.comunicacion_y_notificaciones.comunicaciones.router import _ensure_tecnico
from app.modules.incidentes.emergencias.schemas import UbicacionCreateIn, UbicacionTecnicoCompartidaRead
from app.modules.acceso_y_administracion.usuarios.models import Usuario

from . import service
from .schemas import ActualizarEstadoServicioIn, ServicioAsignadoRead, UbicacionClienteActualRead

router = APIRouter(prefix="/app/tecnico/emergencias", tags=["Emergencias (técnico)"])


@router.get(
    "/servicios-asignados",
    response_model=list[ServicioAsignadoRead],
    dependencies=[Depends(require_permission("servicios_tecnico:leer"))],
)
async def listar_servicios_asignados(
    current_user: Usuario = Depends(_ensure_tecnico),
    db: AsyncSession = Depends(get_db),
):
    """CU32 — solicitudes donde este técnico está asignado."""
    return await service.listar_servicios_asignados(current_user, db)


@router.get(
    "/solicitudes/{solicitud_id}/ubicacion",
    response_model=UbicacionClienteActualRead,
    dependencies=[Depends(require_permission("cliente_ubicacion:leer"))],
)
async def ubicacion_cliente_actual(
    solicitud_id: int,
    current_user: Usuario = Depends(_ensure_tecnico),
    db: AsyncSession = Depends(get_db),
):
    """CU33 — ubicación actual (solicitud asignada al técnico)."""
    return await service.obtener_ubicacion_cliente(current_user, solicitud_id, db)


@router.post(
    "/solicitudes/{solicitud_id}/ubicacion-tecnico",
    response_model=UbicacionTecnicoCompartidaRead,
    dependencies=[Depends(require_permission("tecnico_ubicacion:compartir"))],
)
async def compartir_ubicacion_tecnico(
    solicitud_id: int,
    body: UbicacionCreateIn,
    current_user: Usuario = Depends(_ensure_tecnico),
    db: AsyncSession = Depends(get_db),
):
    """Envía la posición actual del técnico asociada a la solicitud (el cliente puede consultarla)."""
    return await service.compartir_ubicacion_tecnico(current_user, solicitud_id, body, db)


@router.patch(
    "/solicitudes/{solicitud_id}/estado",
    response_model=ServicioAsignadoRead,
    dependencies=[Depends(require_permission("servicios_tecnico:actualizar_estado"))],
)
async def actualizar_estado_servicio(
    solicitud_id: int,
    body: ActualizarEstadoServicioIn,
    current_user: Usuario = Depends(_ensure_tecnico),
    db: AsyncSession = Depends(get_db),
):
    """CU34 — transiciones TECNICO_ASIGNADO→EN_CAMINO→EN_ATENCION→FINALIZADA."""
    return await service.actualizar_estado_servicio(current_user, solicitud_id, body, db)


@router.get(
    "/{solicitud_id}/mensajes",
    response_model=list[MensajeSolicitudRead],
    dependencies=[Depends(require_permission("mensajes_tecnico:leer"))],
)
async def listar_mensajes(
    solicitud_id: int,
    current_user: Usuario = Depends(_ensure_tecnico),
    db: AsyncSession = Depends(get_db),
):
    """CU35 — leer hilo (reutiliza solicitud_mensajes)."""
    return await service.listar_mensajes_solicitud(current_user, solicitud_id, db)


@router.post(
    "/{solicitud_id}/mensajes",
    response_model=MensajeSolicitudRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("mensajes_tecnico:crear"))],
)
async def enviar_mensaje(
    solicitud_id: int,
    body: MensajeSolicitudCreateIn,
    current_user: Usuario = Depends(_ensure_tecnico),
    db: AsyncSession = Depends(get_db),
):
    """CU35 — enviar mensaje al cliente."""
    return await service.enviar_mensaje_solicitud(current_user, solicitud_id, body, db)
