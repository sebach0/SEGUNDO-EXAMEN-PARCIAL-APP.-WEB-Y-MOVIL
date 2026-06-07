from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_permission
from app.modules.cotizaciones import service
from app.modules.cotizaciones.schemas import CotizacionContextoRead, CotizacionCreateIn, CotizacionRead
from app.modules.talleres_y_tecnicos.taller_responsable.router import require_taller_responsable
from app.modules.talleres_y_tecnicos.talleres.models import Taller
from app.modules.acceso_y_administracion.usuarios.models import Usuario

router = APIRouter(prefix="/cotizaciones", tags=["Cotizaciones"])


@router.get(
    "/solicitudes/{solicitud_id}",
    response_model=list[CotizacionRead],
    dependencies=[Depends(require_permission("cotizaciones:leer"))],
)
async def listar_cotizaciones(
    solicitud_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    """Lista todas las cotizaciones enviadas por los talleres para una solicitud."""
    return await service.listar_cotizaciones(solicitud_id=solicitud_id, db=db)


@router.get(
    "/solicitudes/{solicitud_id}/contexto-oferta",
    response_model=CotizacionContextoRead,
    dependencies=[Depends(require_permission("cotizaciones:crear"))],
)
async def contexto_oferta_cotizacion(
    solicitud_id: int,
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    """Distancia al incidente y servicios del taller para armar la oferta."""
    _, taller = ctx
    return await service.contexto_oferta_taller(
        solicitud_id=solicitud_id,
        taller_id=taller.id,
        db=db,
    )


@router.post(
    "/solicitudes/{solicitud_id}",
    response_model=CotizacionRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("cotizaciones:crear"))],
)
async def proponer_cotizacion(
    solicitud_id: int,
    body: CotizacionCreateIn,
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    """El taller responsable envía una cotización para una solicitud de emergencia."""
    _, taller = ctx
    return await service.proponer_cotizacion(
        solicitud_id=solicitud_id,
        taller_id=taller.id,
        body=body,
        db=db,
    )


@router.post(
    "/solicitudes/{solicitud_id}/cotizacion/{cotizacion_id}/seleccionar",
    response_model=CotizacionRead,
    dependencies=[Depends(require_permission("cotizaciones:aceptar"))],
)
async def seleccionar_cotizacion(
    solicitud_id: int,
    cotizacion_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    """El cliente selecciona una cotización; las demás pasan a EXPIRADA y el taller queda asignado."""
    return await service.seleccionar_cotizacion(
        solicitud_id=solicitud_id,
        cotizacion_id=cotizacion_id,
        db=db,
    )
