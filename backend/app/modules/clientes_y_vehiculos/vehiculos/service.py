# app/modules/vehiculos/service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.core.timeutil import utc_now_naive
from app.modules.clientes_y_vehiculos.vehiculos.models import MarcaVehiculo, ModeloVehiculo, TipoVehiculo, Vehiculo
from app.modules.acceso_y_administracion.bitacora.service import registrar_accion
from app.modules.acceso_y_administracion.bitacora.models import AccionBitacoraEnum


# ── Catálogos ────────────────────────────────────────────────
async def get_marcas(db: AsyncSession):
    result = await db.execute(select(MarcaVehiculo).order_by(MarcaVehiculo.nombre))
    return list(result.scalars().all())

async def create_marca(nombre: str, db: AsyncSession):
    marca = MarcaVehiculo(nombre=nombre)
    db.add(marca)
    await db.flush()
    return marca

async def get_modelos(db: AsyncSession, marca_id: int | None = None):
    query = select(ModeloVehiculo).order_by(ModeloVehiculo.nombre)
    if marca_id:
        query = query.where(ModeloVehiculo.marca_id == marca_id)
    result = await db.execute(query)
    return list(result.scalars().all())

async def create_modelo(marca_id: int, nombre: str, db: AsyncSession):
    modelo = ModeloVehiculo(marca_id=marca_id, nombre=nombre)
    db.add(modelo)
    await db.flush()
    return modelo

async def get_tipos(db: AsyncSession):
    result = await db.execute(select(TipoVehiculo).order_by(TipoVehiculo.nombre))
    return list(result.scalars().all())

async def create_tipo(nombre: str, db: AsyncSession):
    tipo = TipoVehiculo(nombre=nombre)
    db.add(tipo)
    await db.flush()
    return tipo


# ── Vehículos ────────────────────────────────────────────────
async def get_vehiculos(db: AsyncSession, cliente_id: int | None = None):
    query = select(Vehiculo).order_by(Vehiculo.placa)
    if cliente_id:
        query = query.where(Vehiculo.cliente_id == cliente_id)
    result = await db.execute(query)
    return list(result.scalars().all())

async def get_vehiculo_by_id(vehiculo_id: int, db: AsyncSession) -> Vehiculo:
    result = await db.execute(select(Vehiculo).where(Vehiculo.id == vehiculo_id))
    v = result.scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    return v

async def create_vehiculo(data: dict, db: AsyncSession, ejecutor_id: int | None = None):
    v = Vehiculo(
        **{k: data[k] for k in ["cliente_id", "placa", "marca_id", "modelo_id", "tipo_vehiculo_id"]},
        anio=data.get("anio"),
        color=data.get("color"),
        created_at=utc_now_naive(),
        updated_at=utc_now_naive(),
    )
    db.add(v)
    await db.flush()
    await registrar_accion(
        db=db, usuario_id=ejecutor_id, modulo="vehiculos", entidad="vehiculos",
        entidad_id=v.id, accion=AccionBitacoraEnum.CREAR,
        descripcion=f"Vehículo creado: {v.placa}",
    )
    return v

async def update_vehiculo(vehiculo_id: int, data: dict, db: AsyncSession, ejecutor_id: int | None = None):
    v = await get_vehiculo_by_id(vehiculo_id, db)
    for field, value in data.items():
        if value is not None:
            setattr(v, field, value)
    v.updated_at = utc_now_naive()
    await registrar_accion(
        db=db, usuario_id=ejecutor_id, modulo="vehiculos", entidad="vehiculos",
        entidad_id=vehiculo_id, accion=AccionBitacoraEnum.ACTUALIZAR,
        descripcion=f"Vehículo actualizado: {vehiculo_id}",
    )
    return v
