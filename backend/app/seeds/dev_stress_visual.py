# Seed idempotente: catálogo vehículo extra + clientes adicionales (listas / stress visual en admin o futuras vistas).
# No afecta el flujo demo Santa Cruz; credenciales documentadas en .env.example.
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.acceso_y_administracion.roles.models import Rol
from app.modules.acceso_y_administracion.roles.service import asignar_roles_usuario
from app.modules.acceso_y_administracion.usuarios import service as usuarios_service
from app.modules.acceso_y_administracion.usuarios.models import EstadoUsuarioEnum, Usuario
from app.seeds.dev_catalogos_vehiculo import ensure_catalogos_vehiculo_stress_extra
from app.seeds.identidades_demo_sc import (
    CIUDAD_SANTA_CRUZ,
    STRESS_BARRIOS_SC,
    STRESS_PASSWORD,
    stress_cliente_email,
    stress_cliente_nombres_apellidos,
    stress_cliente_telefono,
)

logger = logging.getLogger(__name__)


async def _rol_cliente_id(db: AsyncSession) -> int | None:
    r = await db.execute(select(Rol.id).where(Rol.nombre == "CLIENTE"))
    row = r.scalar_one_or_none()
    if row is None:
        logger.error("Seed stress visual: no existe rol CLIENTE.")
        return None
    return int(row)

_STRESS_CLIENT_COUNT = 8


async def ensure_stress_visual_seed(
    db: AsyncSession,
    *,
    require_enabled_flag: bool = True,
) -> None:
    if require_enabled_flag and not settings.SEED_STRESS_VISUAL_ON_START:
        return

    pwd = (settings.SEED_STRESS_CLIENT_PASSWORD or STRESS_PASSWORD or "").strip()
    if not pwd:
        logger.warning("Seed stress visual omitido: defina SEED_STRESS_CLIENT_PASSWORD.")
        return

    await ensure_catalogos_vehiculo_stress_extra(db)

    rol_id = await _rol_cliente_id(db)
    if rol_id is None:
        return

    created = 0
    for i in range(1, _STRESS_CLIENT_COUNT + 1):
        email = stress_cliente_email(i)
        tel = stress_cliente_telefono(i)
        nom, ape = stress_cliente_nombres_apellidos(i)
        ex = (await db.execute(select(Usuario).where(Usuario.email == email))).scalar_one_or_none()
        if ex is not None:
            continue
        u = await usuarios_service.create_usuario(
            {
                "nombres": nom,
                "apellidos": ape,
                "email": email,
                "telefono": tel,
                "password": pwd,
                "username": None,
                "estado": EstadoUsuarioEnum.ACTIVO,
            },
            db,
            ejecutor_id=None,
        )
        barrio = STRESS_BARRIOS_SC[(i - 1) % len(STRESS_BARRIOS_SC)]
        await usuarios_service.create_cliente(
            {
                "usuario_id": u.id,
                "ciudad": CIUDAD_SANTA_CRUZ,
                "direccion": f"Barrio {barrio}, Santa Cruz — referencia vía pública",
            },
            db,
        )
        await asignar_roles_usuario(u.id, [rol_id], db)
        created += 1

    if created:
        logger.info("Seed stress visual: %s usuarios cliente extra creados.", created)
    else:
        logger.info("Seed stress visual: clientes extra ya existían; catálogos extra verificados.")
