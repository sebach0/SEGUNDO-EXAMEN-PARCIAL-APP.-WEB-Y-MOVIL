# Lecturas para ranking de talleres (IA6).
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.atencion.taller_emergencias.models import (
    EstadoBandejaTallerEnum,
    SolicitudTallerBandeja,
)
from app.modules.talleres_y_tecnicos.talleres.models import EstadoTecnicoEnum, EstadoTallerEnum, Taller, Tecnico


async def list_talleres_for_assignment(db: AsyncSession) -> list[dict]:
    r = await db.execute(
        select(Taller).where(Taller.estado == EstadoTallerEnum.ACTIVO).order_by(Taller.id)
    )
    talleres = list(r.scalars().unique().all())
    if not talleres:
        return []

    pend_r = await db.execute(
        select(SolicitudTallerBandeja.taller_id, func.count().label("n"))
        .where(SolicitudTallerBandeja.estado == EstadoBandejaTallerEnum.PENDIENTE)
        .group_by(SolicitudTallerBandeja.taller_id)
    )
    pend_map = {row.taller_id: int(row.n) for row in pend_r.all()}

    tech_r = await db.execute(
        select(Tecnico)
        .where(Tecnico.estado == EstadoTecnicoEnum.ACTIVO)
        .options(joinedload(Tecnico.especialidad))
    )
    specs_by_taller: dict[int, list[str]] = {}
    for t in tech_r.scalars().unique().all():
        specs_by_taller.setdefault(t.taller_id, [])
        if t.especialidad and t.especialidad.nombre:
            specs_by_taller[t.taller_id].append(t.especialidad.nombre)

    out: list[dict] = []
    for t in talleres:
        out.append(
            {
                "taller_id": t.id,
                "nombre_comercial": t.nombre_comercial,
                "ciudad": t.ciudad,
                "latitud": float(t.latitud) if t.latitud is not None else None,
                "longitud": float(t.longitud) if t.longitud is not None else None,
                "pendientes_bandeja": pend_map.get(t.id, 0),
                "especialidad_nombres": specs_by_taller.get(t.id, []),
            }
        )
    return out
