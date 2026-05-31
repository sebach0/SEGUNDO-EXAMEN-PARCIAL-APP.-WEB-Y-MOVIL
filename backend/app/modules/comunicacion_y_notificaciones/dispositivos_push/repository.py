from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.comunicacion_y_notificaciones.dispositivos_push.models import UsuarioFcmToken


async def upsert_fcm_token(
    db: AsyncSession, *, usuario_id: int, token: str, platform: str | None, now
) -> UsuarioFcmToken:
    tbl = UsuarioFcmToken.__table__
    stmt = (
        pg_insert(tbl)
        .values(usuario_id=usuario_id, token=token, platform=platform, created_at=now, updated_at=now)
        .on_conflict_do_update(
            index_elements=[tbl.c.token],
            set_={"usuario_id": usuario_id, "platform": platform, "updated_at": now},
        )
    )
    await db.execute(stmt)
    await db.flush()
    r = await db.execute(select(UsuarioFcmToken).where(UsuarioFcmToken.token == token))
    return r.scalar_one()


async def delete_fcm_token(db: AsyncSession, *, usuario_id: int, token: str) -> int:
    r = await db.execute(
        delete(UsuarioFcmToken).where(
            UsuarioFcmToken.token == token,
            UsuarioFcmToken.usuario_id == usuario_id,
        )
    )
    return r.rowcount or 0


async def list_fcm_tokens_usuario(db: AsyncSession, *, usuario_id: int) -> list[str]:
    r = await db.execute(select(UsuarioFcmToken.token).where(UsuarioFcmToken.usuario_id == usuario_id))
    return [str(x[0]) for x in r.fetchall()]
