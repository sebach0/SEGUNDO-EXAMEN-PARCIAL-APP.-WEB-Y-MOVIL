from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.acceso_y_administracion.usuarios.models import Usuario
from app.modules.clientes_y_vehiculos.vehiculos import service as vehiculos_service
from app.modules.clientes_y_vehiculos.vehiculos.schemas import VehiculoRead, VehiculoUpdate

from ..schemas_movil import VehiculoClienteCreateIn
from .acceso import get_cliente_row_for_usuario, require_cliente_rol


async def list_mis_vehiculos(user: Usuario, db: AsyncSession) -> list[VehiculoRead]:
    await require_cliente_rol(user.id, db)
    cliente = await get_cliente_row_for_usuario(user.id, db)
    rows = await vehiculos_service.get_vehiculos(db, cliente_id=cliente.id)
    return [VehiculoRead.model_validate(v) for v in rows]


async def get_mi_vehiculo(user: Usuario, vehiculo_id: int, db: AsyncSession) -> VehiculoRead:
    await require_cliente_rol(user.id, db)
    cliente = await get_cliente_row_for_usuario(user.id, db)
    v = await vehiculos_service.get_vehiculo_by_id(vehiculo_id, db)
    if v.cliente_id != cliente.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehículo no encontrado")
    return VehiculoRead.model_validate(v)


async def crear_mi_vehiculo(user: Usuario, body: VehiculoClienteCreateIn, db: AsyncSession) -> VehiculoRead:
    await require_cliente_rol(user.id, db)
    cliente = await get_cliente_row_for_usuario(user.id, db)
    data = {
        "cliente_id": cliente.id,
        "placa": body.placa.strip().upper(),
        "marca_id": body.marca_id,
        "modelo_id": body.modelo_id,
        "tipo_vehiculo_id": body.tipo_vehiculo_id,
        "anio": body.anio,
        "color": body.color,
    }
    v = await vehiculos_service.create_vehiculo(data, db, ejecutor_id=user.id)
    return VehiculoRead.model_validate(v)


async def actualizar_mi_vehiculo(
    user: Usuario,
    vehiculo_id: int,
    body: VehiculoUpdate,
    db: AsyncSession,
) -> VehiculoRead:
    await require_cliente_rol(user.id, db)
    cliente = await get_cliente_row_for_usuario(user.id, db)
    v = await vehiculos_service.get_vehiculo_by_id(vehiculo_id, db)
    if v.cliente_id != cliente.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehículo no encontrado")
    updated = await vehiculos_service.update_vehiculo(
        vehiculo_id,
        body.model_dump(exclude_none=True),
        db,
        user.id,
    )
    return VehiculoRead.model_validate(updated)
