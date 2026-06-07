# Sincronización offline de solicitudes_emergencia (client_uuid anti-duplicado).
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timeutil import to_naive_utc, utc_now_naive
from app.modules.ciclo4.deps import _DEFAULT_TENANT_ID
from app.modules.incidentes.emergencias import repository
from app.modules.incidentes.emergencias.models import EstadoSolicitudSeguimientoEnum, SolicitudEmergencia
from app.modules.incidentes.emergencias.schemas import UbicacionCreateIn
from app.modules.incidentes.emergencias.service.helpers import add_ubicacion_internal
from app.modules.incidentes.emergencias.service.solicitudes import _post_create_pipeline
from app.modules.incidentes.emergencias.solicitud_lifecycle import init_reportado_en
from app.modules.acceso_y_administracion.usuarios.models import Usuario


class SyncSolicitudOfflineIn(BaseModel):
    client_uuid: uuid.UUID
    vehiculo_id: int = Field(ge=1)
    descripcion_texto: str | None = None
    ubicacion_inicial: dict | None = None
    registrado_local_en: datetime | None = None


class SyncSolicitudOfflineOut(BaseModel):
    sincronizado: bool
    solicitud_id: int | None = None
    client_uuid: uuid.UUID
    error: str | None = None


async def sincronizar_solicitud_offline(
    user: Usuario,
    cliente_id: int,
    body: SyncSolicitudOfflineIn,
    db: AsyncSession,
) -> SyncSolicitudOfflineOut:
    tenant_id = user.tenant_id or _DEFAULT_TENANT_ID

    exist = await db.execute(
        select(SolicitudEmergencia).where(
            SolicitudEmergencia.tenant_id == tenant_id,
            SolicitudEmergencia.client_uuid == body.client_uuid,
        )
    )
    prev = exist.scalar_one_or_none()
    if prev is not None:
        return SyncSolicitudOfflineOut(
            sincronizado=True,
            solicitud_id=prev.id,
            client_uuid=body.client_uuid,
        )

    v = await repository.get_vehiculo_if_cliente(
        db, vehiculo_id=body.vehiculo_id, cliente_id=cliente_id
    )
    if v is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehículo no encontrado o no pertenece a tu cuenta.",
        )

    now = utc_now_naive()
    desc = (body.descripcion_texto or "").strip() or None
    reportado_en = to_naive_utc(body.registrado_local_en) or now

    sol = SolicitudEmergencia(
        cliente_id=cliente_id,
        vehiculo_id=body.vehiculo_id,
        descripcion_texto=desc,
        estado=EstadoSolicitudSeguimientoEnum.REGISTRADA,
        created_at=now,
        updated_at=now,
        reportado_en=reportado_en,
        tenant_id=tenant_id,
        client_uuid=body.client_uuid,
        sync_estado="SINCRONIZADO",
    )
    init_reportado_en(sol, reportado_en)
    db.add(sol)
    await db.flush()

    await repository.insert_historial_estado(
        db,
        solicitud_id=sol.id,
        estado_anterior=None,
        estado_nuevo=sol.estado,
        usuario_id=user.id,
        observacion="Alta offline sincronizada",
        created_at=now,
    )

    if body.ubicacion_inicial is not None:
        try:
            ubi = UbicacionCreateIn.model_validate(body.ubicacion_inicial)
            await add_ubicacion_internal(db, sol, ubi, now)
        except Exception:
            pass

    await _post_create_pipeline(
        db,
        user=user,
        cliente_id=cliente_id,
        sol=sol,
        vehiculo_id=body.vehiculo_id,
        now=now,
        bitacora_desc=f"Solicitud offline sync vehículo_id={body.vehiculo_id}",
    )

    return SyncSolicitudOfflineOut(
        sincronizado=True,
        solicitud_id=sol.id,
        client_uuid=body.client_uuid,
    )
