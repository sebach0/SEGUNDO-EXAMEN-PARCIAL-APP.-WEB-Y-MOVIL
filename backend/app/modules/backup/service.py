"""Backup service — serializes key DB tables to a JSON zip archive."""
from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime, timezone

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
