"""Backup router — GET /admin/backup/descargar|historial|archivo/{filename}"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import require_permission
from app.modules.backup import service

backup_router = APIRouter(
    prefix="/admin/backup",
    tags=["Admin - Backup"],
)

_SAFE_FILENAME = re.compile(r'^backup_\d{8}_\d{6}\.zip$')


@backup_router.get(
    "/descargar",
    dependencies=[Depends(require_permission("admin:backup"))],
    summary="Descarga un backup completo en formato ZIP (generado al vuelo)",
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


@backup_router.get(
    "/historial",
    dependencies=[Depends(require_permission("admin:backup"))],
    summary="Lista los backups automáticos guardados en disco",
)
async def historial_backups():
    return service.list_backups(settings.backup_dir_path)


@backup_router.get(
    "/archivo/{filename}",
    dependencies=[Depends(require_permission("admin:backup"))],
    summary="Descarga un backup guardado por su nombre de archivo",
)
async def descargar_archivo_backup(filename: str):
    if not _SAFE_FILENAME.match(filename):
        raise HTTPException(status_code=400, detail="Nombre de archivo inválido")
    path = settings.backup_dir_path / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Backup no encontrado")
    return FileResponse(str(path), media_type="application/zip", filename=filename)
