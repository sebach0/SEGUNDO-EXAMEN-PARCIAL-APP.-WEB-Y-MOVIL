# Datos — servicios asignados y ubicación (vista lógica script 008)
from __future__ import annotations

from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.modules.incidentes.emergencias.models import SolicitudEmergencia, SolicitudUbicacion
from app.modules.clientes_y_vehiculos.clientes.models import Cliente
from app.modules.acceso_y_administracion.usuarios.models import Usuario
from app.modules.clientes_y_vehiculos.vehiculos.models import MarcaVehiculo, ModeloVehiculo, TipoVehiculo, Vehiculo


def _servicios_select():
    su = aliased(SolicitudUbicacion)
    return (
        select(
            SolicitudEmergencia.id.label("solicitud_id"),
            SolicitudEmergencia.tecnico_id,
            SolicitudEmergencia.taller_id,
            SolicitudEmergencia.estado,
            SolicitudEmergencia.tiempo_estimado_min,
            SolicitudEmergencia.created_at,
            SolicitudEmergencia.updated_at,
            Cliente.id.label("cliente_id"),
            Usuario.nombres,
            Usuario.apellidos,
            Usuario.telefono,
            Vehiculo.placa,
            MarcaVehiculo.nombre.label("marca"),
            ModeloVehiculo.nombre.label("modelo"),
            TipoVehiculo.nombre.label("tipo_vehiculo"),
            su.latitud,
            su.longitud,
            su.direccion_referencia,
            func.jsonb_extract_path_text(
                SolicitudEmergencia.ai_payload, "clasificacion", "categoria_incidente"
            ).label("categoria_incidente"),
            func.jsonb_extract_path_text(
                SolicitudEmergencia.ai_payload, "prioridad", "nivel_prioridad"
            ).label("nivel_prioridad"),
            SolicitudEmergencia.presupuesto_bob,
            SolicitudEmergencia.presupuesto_registrado_at,
        )
        .select_from(SolicitudEmergencia)
        .join(Cliente, Cliente.id == SolicitudEmergencia.cliente_id)
        .join(Usuario, Usuario.id == Cliente.usuario_id)
        .join(Vehiculo, Vehiculo.id == SolicitudEmergencia.vehiculo_id)
        .outerjoin(MarcaVehiculo, MarcaVehiculo.id == Vehiculo.marca_id)
        .outerjoin(ModeloVehiculo, ModeloVehiculo.id == Vehiculo.modelo_id)
        .outerjoin(TipoVehiculo, TipoVehiculo.id == Vehiculo.tipo_vehiculo_id)
        .outerjoin(
            su,
            and_(su.solicitud_id == SolicitudEmergencia.id, su.es_actual.is_(True)),
        )
    )


async def list_servicios_asignados_a_tecnico(
    db: AsyncSession, *, tecnico_id: int
) -> list[dict[str, Any]]:
    stmt = (
        _servicios_select()
        .where(SolicitudEmergencia.tecnico_id == tecnico_id)
        .order_by(SolicitudEmergencia.updated_at.desc())
    )
    r = await db.execute(stmt)
    return [dict(x) for x in r.mappings().all()]


async def list_historial_tecnico(
    db: AsyncSession, *, tecnico_id: int, limit: int = 100
) -> list[dict[str, Any]]:
    from app.modules.incidentes.emergencias.models import EstadoSolicitudSeguimientoEnum
    stmt = (
        _servicios_select()
        .where(
            SolicitudEmergencia.tecnico_id == tecnico_id,
            SolicitudEmergencia.estado.in_([
                EstadoSolicitudSeguimientoEnum.FINALIZADA,
                EstadoSolicitudSeguimientoEnum.CANCELADA,
            ]),
        )
        .order_by(SolicitudEmergencia.updated_at.desc())
        .limit(limit)
    )
    r = await db.execute(stmt)
    return [dict(x) for x in r.mappings().all()]


async def get_servicio_asignado_detalle(
    db: AsyncSession, *, solicitud_id: int, tecnico_id: int
) -> dict[str, Any] | None:
    stmt = _servicios_select().where(
        SolicitudEmergencia.id == solicitud_id,
        SolicitudEmergencia.tecnico_id == tecnico_id,
    )
    r = await db.execute(stmt)
    row = r.mappings().one_or_none()
    return dict(row) if row else None


async def get_ubicacion_actual_para_solicitud_tecnico(
    db: AsyncSession, *, solicitud_id: int, tecnico_id: int
) -> dict[str, Any] | None:
    stmt = (
        select(
            SolicitudUbicacion.solicitud_id,
            SolicitudUbicacion.latitud,
            SolicitudUbicacion.longitud,
            SolicitudUbicacion.precision_metros,
            SolicitudUbicacion.direccion_referencia,
            SolicitudUbicacion.registrado_at,
        )
        .join(SolicitudEmergencia, SolicitudEmergencia.id == SolicitudUbicacion.solicitud_id)
        .where(
            SolicitudUbicacion.solicitud_id == solicitud_id,
            SolicitudEmergencia.tecnico_id == tecnico_id,
            SolicitudUbicacion.es_actual.is_(True),
        )
    )
    r = await db.execute(stmt)
    row = r.mappings().one_or_none()
    return dict(row) if row else None
