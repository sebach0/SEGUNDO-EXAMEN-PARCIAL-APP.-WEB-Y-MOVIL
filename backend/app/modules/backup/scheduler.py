"""Scheduler de backup automático — loop asyncio iniciado en lifespan."""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path

_log = logging.getLogger(__name__)


async def run_backup_scheduler(backup_dir: Path, interval_hours: int, max_files: int) -> None:
    from app.core.database import AsyncSessionLocal
    from .service import save_backup_to_disk

    backup_dir.mkdir(parents=True, exist_ok=True)
    _log.info("Backup automático activo — cada %sh, máx %s archivos en %s", interval_hours, max_files, backup_dir)

    while True:
        await asyncio.sleep(interval_hours * 3600)
        try:
            async with AsyncSessionLocal() as db:
                filename = await save_backup_to_disk(db, backup_dir, max_files)
            _log.info("Backup automático guardado: %s", filename)
        except Exception:
            _log.exception("Error en backup automático")
