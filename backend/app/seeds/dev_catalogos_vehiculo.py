# Seed idempotente: tipos de vehículo, marcas y modelos (catálogos para app móvil / API).
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.clientes_y_vehiculos.vehiculos.models import MarcaVehiculo, ModeloVehiculo, TipoVehiculo

logger = logging.getLogger(__name__)

_TIPOS = ("Sedán", "SUV", "Pickup", "Hatchback", "Motocicleta")

_MARCAS_Y_MODELOS: dict[str, tuple[str, ...]] = {
    "Toyota": ("Corolla", "Hilux", "RAV4"),
    "Chevrolet": ("Spark", "Sail", "D-Max"),
    "Suzuki": ("Swift", "Vitara", "Jimny"),
    "Ford": ("Ranger", "EcoSport", "Fiesta"),
    "Hyundai": ("Tucson", "Accent", "Santa Fe"),
}


async def _get_or_create_tipo(db: AsyncSession, nombre: str) -> TipoVehiculo:
    r = await db.execute(select(TipoVehiculo).where(TipoVehiculo.nombre == nombre))
    row = r.scalar_one_or_none()
    if row is not None:
        return row
    t = TipoVehiculo(nombre=nombre)
    db.add(t)
    await db.flush()
    return t


async def _get_or_create_marca(db: AsyncSession, nombre: str) -> MarcaVehiculo:
    r = await db.execute(select(MarcaVehiculo).where(MarcaVehiculo.nombre == nombre))
    row = r.scalar_one_or_none()
    if row is not None:
        return row
    m = MarcaVehiculo(nombre=nombre)
    db.add(m)
    await db.flush()
    return m


async def _get_or_create_modelo(db: AsyncSession, marca_id: int, nombre: str) -> None:
    r = await db.execute(
        select(ModeloVehiculo).where(
            ModeloVehiculo.marca_id == marca_id,
            ModeloVehiculo.nombre == nombre,
        )
    )
    if r.scalar_one_or_none() is not None:
        return
    db.add(ModeloVehiculo(marca_id=marca_id, nombre=nombre))
    await db.flush()


async def ensure_catalogos_vehiculo_demo(db: AsyncSession) -> None:
    """
    Asegura datos mínimos en ``tipos_vehiculo``, ``marcas_vehiculo`` y ``modelos_vehiculo``.
    Idempotente: no duplica por nombre / (marca_id, nombre).
    """
    for nombre in _TIPOS:
        await _get_or_create_tipo(db, nombre)

    for marca_nombre, modelos in _MARCAS_Y_MODELOS.items():
        m = await _get_or_create_marca(db, marca_nombre)
        for mod in modelos:
            await _get_or_create_modelo(db, m.id, mod)

    logger.info(
        "Seed catálogos vehículo: %s tipos, %s marcas con modelos.",
        len(_TIPOS),
        len(_MARCAS_Y_MODELOS),
    )


# Catálogo extra (stress visual en pickers: marcas/modelos/tipos adicionales). Idempotente.
_TIPOS_STRESS = ("Van", "Minibús", "Rural")

_MARCAS_STRESS: dict[str, tuple[str, ...]] = {
    "Nissan": ("Sentra", "Frontier", "Kicks"),
    "Volkswagen": ("Gol", "Amarok", "Tiguan"),
    "Renault": ("Duster", "Logan", "Sandero"),
    "Mitsubishi": ("L200", "ASX", "Outlander"),
    "Kia": ("Rio", "Sportage", "Seltos"),
    "Mazda": ("Mazda 3", "CX-5", "BT-50"),
    "Peugeot": ("208", "3008", "Partner"),
    "Fiat": ("Uno", "Toro", "Strada"),
}


async def ensure_catalogos_vehiculo_stress_extra(db: AsyncSession) -> None:
    """Marcas/modelos y tipos extra para listas largas en UI (no crítico para flujo demo)."""
    for nombre in _TIPOS_STRESS:
        await _get_or_create_tipo(db, nombre)
    for marca_nombre, modelos in _MARCAS_STRESS.items():
        m = await _get_or_create_marca(db, marca_nombre)
        for mod in modelos:
            await _get_or_create_modelo(db, m.id, mod)
    logger.info(
        "Seed catálogos stress: +%s tipos, +%s marcas.",
        len(_TIPOS_STRESS),
        len(_MARCAS_STRESS),
    )
