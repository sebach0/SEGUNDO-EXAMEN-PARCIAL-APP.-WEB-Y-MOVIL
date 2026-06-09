"""Backup router — GET /admin/backup/descargar"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.modules.backup import service

backup_router = APIRouter(
    prefix="/admin/backup",
    tags=["Admin - Backup"],
)


@backup_router.get(
    "/descargar",
    dependencies=[Depends(require_permission("admin:backup"))],
    summary="Descarga un backup completo en formato ZIP",
)
async def descargar_backup(db: AsyncSession = Depends(get_db)):
    zip_bytes = await service.generate_backup_zip(db)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{timestamp}.zip"
    return StreamingResponse(
        iter([zip_bytes]),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
