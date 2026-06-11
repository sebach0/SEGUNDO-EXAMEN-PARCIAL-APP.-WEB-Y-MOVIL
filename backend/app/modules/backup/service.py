"""Backup service — serializes key DB tables to a JSON zip archive."""
from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_TABLES = [
    "usuarios",
    "roles",
    "permisos",
    "rol_permiso",
    "usuario_rol",
    "tenants",
    "talleres",
    "tecnicos",
    "clientes",
    "vehiculos",
    "solicitudes_emergencia",
    "bandeja_taller",
    "cotizaciones",
    "pagos",
    "notificaciones",
    "bitacora",
]


async def _dump_table(db: AsyncSession, table: str) -> list[dict]:
    try:
        result = await db.execute(text(f"SELECT * FROM {table}"))
        cols = list(result.keys())
        rows = []
        for row in result.fetchall():
            record: dict = {}
            for col, val in zip(cols, row):
                if isinstance(val, datetime):
                    record[col] = val.isoformat()
                else:
                    record[col] = val
            rows.append(record)
        return rows
    except Exception:
        return []


async def generate_backup_zip(db: AsyncSession) -> bytes:
    """Returns a ZIP file in memory containing one JSON file per table."""
    generated_at = datetime.now(timezone.utc).isoformat()
    buf = io.BytesIO()

    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        meta = {"generated_at": generated_at, "tables": _TABLES, "version": "1.0"}
        zf.writestr("backup_meta.json", json.dumps(meta, ensure_ascii=False, indent=2))

        for table in _TABLES:
            rows = await _dump_table(db, table)
            content = json.dumps(rows, ensure_ascii=False, indent=2, default=str)
            zf.writestr(f"{table}.json", content)

    return buf.getvalue()


async def save_backup_to_disk(db: AsyncSession, backup_dir: Path, max_files: int = 7) -> str:
    """Genera el ZIP y lo persiste en *backup_dir*. Elimina los más antiguos si supera *max_files*."""
    backup_dir.mkdir(parents=True, exist_ok=True)
    zip_bytes = await generate_backup_zip(db)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{ts}.zip"
    (backup_dir / filename).write_bytes(zip_bytes)

    existing = sorted(backup_dir.glob("backup_*.zip"), key=lambda f: f.stat().st_mtime)
    while len(existing) > max_files:
        existing.pop(0).unlink(missing_ok=True)

    return filename


def list_backups(backup_dir: Path) -> list[dict]:
    """Lista los backups guardados en disco, del más reciente al más antiguo."""
    if not backup_dir.exists():
        return []
    files = sorted(backup_dir.glob("backup_*.zip"), key=lambda f: f.stat().st_mtime, reverse=True)
    return [
        {
            "filename": f.name,
            "size_bytes": f.stat().st_size,
            "created_at": datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).isoformat(),
        }
        for f in files
    ]
