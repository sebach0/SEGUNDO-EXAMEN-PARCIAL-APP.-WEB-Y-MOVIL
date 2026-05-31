# API REST — actor Cliente (JWT + perfil cliente + permisos incidentes/ubicación/evidencias)
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_permission
from app.modules.clientes_y_vehiculos.clientes.service import get_cliente_row_for_usuario, require_cliente_rol
from app.modules.acceso_y_administracion.usuarios.models import Usuario

from . import service
from .models import TipoEvidenciaSolicitudEnum
from .schemas import (
    EvidenciaCreateIn,
    SolicitudEmergenciaCreateIn,
    SolicitudEmergenciaDetailRead,
    SolicitudEmergenciaRead,
    SolicitudEmergenciaUpdateTextoIn,
    SolicitudSeguimientoRead,
    UbicacionCreateIn,
    UbicacionTecnicoCompartidaRead,
)

router = APIRouter(
    prefix="/app/cliente/emergencias",
    tags=["Emergencias (cliente móvil)"],
)


async def _cliente_id(user: Usuario, db: AsyncSession) -> int:
    await require_cliente_rol(user.id, db)
    c = await get_cliente_row_for_usuario(user.id, db)
    return c.id


@router.post(
    "",
    response_model=SolicitudEmergenciaDetailRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("incidentes:crear"))],
)
async def crear_solicitud_emergencia(
    body: SolicitudEmergenciaCreateIn,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """CU11 (+ opcional CU12 inicial, CU15)."""
    cid = await _cliente_id(current_user, db)
    return await service.crear_solicitud(current_user, cid, body, db)


@router.get(
    "",
    response_model=list[SolicitudEmergenciaRead],
    dependencies=[Depends(require_permission("incidentes:leer"))],
)
async def listar_mis_solicitudes(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 100,
):
    cid = await _cliente_id(current_user, db)
    return await service.listar_solicitudes(cid, db, limit=limit)


@router.get(
    "/{solicitud_id}/ubicacion-tecnico",
    response_model=UbicacionTecnicoCompartidaRead,
    dependencies=[Depends(require_permission("incidentes:leer"))],
)
async def ubicacion_tecnico_compartida(
    solicitud_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Última posición compartida por el técnico asignado (polling desde el móvil del cliente)."""
    cid = await _cliente_id(current_user, db)
    return await service.obtener_ubicacion_tecnico_compartida_cliente(cid, solicitud_id, db)


@router.get(
    "/{solicitud_id}/seguimiento",
    response_model=SolicitudSeguimientoRead,
    dependencies=[Depends(require_permission("incidentes:leer"))],
)
async def seguimiento_solicitud(
    solicitud_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """CU16 (estado + historial), CU17 (taller/técnico), CU18 (tiempo_estimado_min)."""
    cid = await _cliente_id(current_user, db)
    return await service.obtener_seguimiento(cid, solicitud_id, db)


@router.get(
    "/{solicitud_id}",
    response_model=SolicitudEmergenciaDetailRead,
    dependencies=[Depends(require_permission("incidentes:leer"))],
)
async def detalle_solicitud(
    solicitud_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cid = await _cliente_id(current_user, db)
    return await service.obtener_detalle(cid, solicitud_id, db)


@router.patch(
    "/{solicitud_id}",
    response_model=SolicitudEmergenciaDetailRead,
    dependencies=[Depends(require_permission("incidentes:actualizar"))],
)
async def actualizar_texto_solicitud(
    solicitud_id: int,
    body: SolicitudEmergenciaUpdateTextoIn,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """CU15 — solo en estado REGISTRADA."""
    cid = await _cliente_id(current_user, db)
    return await service.actualizar_texto(current_user, cid, solicitud_id, body, db)


@router.post(
    "/{solicitud_id}/ubicaciones",
    response_model=SolicitudEmergenciaDetailRead,
    dependencies=[Depends(require_permission("ubicacion:crear"))],
)
async def enviar_ubicacion(
    solicitud_id: int,
    body: UbicacionCreateIn,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """CU12 — tiempo real vía polling o envíos repetidos desde el móvil."""
    cid = await _cliente_id(current_user, db)
    return await service.agregar_ubicacion(current_user, cid, solicitud_id, body, db)


@router.post(
    "/{solicitud_id}/evidencias/archivo",
    response_model=SolicitudEmergenciaDetailRead,
    dependencies=[Depends(require_permission("evidencias:crear"))],
)
async def adjuntar_evidencia_archivo(
    solicitud_id: int,
    request: Request,
    tipo: str = Form(..., description="FOTO o AUDIO"),
    file: UploadFile = File(...),
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """CU13/CU14 — sube foto o audio al propio API (sin URL externa obligatoria)."""
    try:
        tipo_e = TipoEvidenciaSolicitudEnum(tipo.strip().upper())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="tipo debe ser FOTO o AUDIO",
        ) from None
    cid = await _cliente_id(current_user, db)
    return await service.agregar_evidencia_archivo(
        current_user, cid, solicitud_id, request, tipo_e, file, db
    )


@router.post(
    "/{solicitud_id}/evidencias",
    response_model=SolicitudEmergenciaDetailRead,
    dependencies=[Depends(require_permission("evidencias:crear"))],
)
async def adjuntar_evidencia(
    solicitud_id: int,
    body: EvidenciaCreateIn,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """CU13 (FOTO) / CU14 (AUDIO) — URL HTTPS al archivo ya subido a almacenamiento externo."""
    cid = await _cliente_id(current_user, db)
    return await service.agregar_evidencia(current_user, cid, solicitud_id, body, db)
