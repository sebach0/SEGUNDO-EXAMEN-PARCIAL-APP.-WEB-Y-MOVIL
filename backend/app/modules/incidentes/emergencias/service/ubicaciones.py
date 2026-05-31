# Ubicaciones del cliente sobre la solicitud (CU12).
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timeutil import utc_now_naive
from app.modules.ai.services.post_create import enrich_solicitud_ai_after_create
from app.modules.acceso_y_administracion.bitacora.models import AccionBitacoraEnum
from app.modules.acceso_y_administracion.bitacora.service import registrar_accion
from app.modules.incidentes.emergencias import repository
from app.modules.incidentes.emergencias.schemas import SolicitudEmergenciaDetailRead, UbicacionCreateIn
from app.modules.acceso_y_administracion.usuarios.models import Usuario

from . import helpers


async def agregar_ubicacion(
    user: Usuario,
    cliente_id: int,
    solicitud_id: int,
    body: UbicacionCreateIn,
    db: AsyncSession,
) -> SolicitudEmergenciaDetailRead:
    s = await repository.get_solicitud_for_cliente(db, solicitud_id=solicitud_id, cliente_id=cliente_id)
    if s is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada")
    helpers.require_registrada(s)

    now = utc_now_naive()
    await helpers.add_ubicacion_internal(db, s, body, now)

    await registrar_accion(
        db,
        "emergencias",
        "solicitud_ubicaciones",
        AccionBitacoraEnum.CREAR,
        descripcion="Ubicación enviada",
        usuario_id=user.id,
        entidad_id=solicitud_id,
    )

    await enrich_solicitud_ai_after_create(db, solicitud_id=solicitud_id, cliente_id=cliente_id)

    s2 = await repository.get_solicitud_for_cliente(
        db, solicitud_id=solicitud_id, cliente_id=cliente_id, with_children=True
    )
    assert s2 is not None
    return helpers.to_detail(s2)
