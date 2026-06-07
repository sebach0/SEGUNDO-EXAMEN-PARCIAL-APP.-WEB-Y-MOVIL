# Filtrado de talleres elegibles según tenant, servicios del catálogo e IA.
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ciclo4.deps import _DEFAULT_TENANT_ID
from app.modules.talleres_y_tecnicos.talleres.models import (
    EstadoTallerEnum,
    ServicioCatalogo,
    Taller,
    TallerServicio,
)


_CATEGORIA_A_CODIGOS: dict[str, list[str]] = {
    "MOTOR": ["MECANICA_GENERAL", "MOTOR"],
    "BATERIA": ["BATERIA", "ELECTRICIDAD"],
    "LLANTA": ["LLANTERIA", "AUXILIO_CARRETERA"],
    "CHOQUE": ["CHAPERIA"],
    "OTROS": [],
}


def _categoria_desde_ai_payload(payload: dict | None) -> str | None:
    if not payload:
        return None
    cls = payload.get("clasificacion")
    if isinstance(cls, dict):
        cat = cls.get("categoria")
        if isinstance(cat, str) and cat.strip():
            return cat.strip().upper()
    return None


def _requiere_grua(payload: dict | None) -> bool:
    if not payload:
        return False
    text = str(payload).upper()
    return "GRUA" in text or "GRÚA" in text or "REMOLQUE" in text


async def listar_taller_ids_elegibles(
    db: AsyncSession,
    *,
    tenant_id: int | None,
    ai_payload: dict | None = None,
) -> list[int]:
    """
    Talleres activos del tenant que ofrecen servicios compatibles con la categoría IA.
    Si la categoría es OTROS o desconocida, incluye todos los talleres activos del tenant.
    """
    tid = tenant_id or _DEFAULT_TENANT_ID
    q = select(Taller.id).where(
        Taller.estado == EstadoTallerEnum.ACTIVO,
        (Taller.tenant_id == tid) | (Taller.tenant_id.is_(None)),
    )
    res = await db.execute(q)
    taller_ids = [row[0] for row in res.all()]
    if not taller_ids:
        return []

    categoria = _categoria_desde_ai_payload(ai_payload)
    codigos = _CATEGORIA_A_CODIGOS.get(categoria or "OTROS", [])
    if codigos:
        res_srv = await db.execute(
            select(TallerServicio.taller_id)
            .join(ServicioCatalogo, ServicioCatalogo.id == TallerServicio.servicio_id)
            .where(
                TallerServicio.taller_id.in_(taller_ids),
                ServicioCatalogo.codigo.in_(codigos),
            )
            .distinct()
        )
        filtrados = [row[0] for row in res_srv.all()]
        if filtrados:
            taller_ids = filtrados

    if _requiere_grua(ai_payload):
        res_g = await db.execute(
            select(Taller.id).where(
                Taller.id.in_(taller_ids),
                Taller.tiene_grua.is_(True),
            )
        )
        con_grua = [row[0] for row in res_g.all()]
        if con_grua:
            taller_ids = con_grua

    return taller_ids
