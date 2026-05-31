# Acceso a datos — bandeja, disponibilidad, asignaciones, historial y comisiones (sin reglas de negocio)
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.modules.talleres_y_tecnicos.talleres.models import Taller
from app.modules.incidentes.emergencias.models import (
    EstadoSolicitudSeguimientoEnum,
    SolicitudEmergencia,
    SolicitudEvidencia,
    SolicitudUbicacion,
)
from app.modules.pagos_y_comisiones.pagos.models import Pago
from app.modules.atencion.taller_emergencias.models import (
    ComisionTaller,
    EstadoAsignacionTecnicoEnum,
    EstadoBandejaTallerEnum,
    SolicitudAsignacionTecnico,
    SolicitudTallerBandeja,
    TallerDisponibilidad,
)
from app.modules.talleres_y_tecnicos.talleres.models import EstadoTecnicoEnum, Tecnico
from app.modules.clientes_y_vehiculos.clientes.models import Cliente
from app.modules.acceso_y_administracion.usuarios.models import Usuario
from app.modules.clientes_y_vehiculos.vehiculos.models import MarcaVehiculo, ModeloVehiculo, TipoVehiculo, Vehiculo


def _incidente_select():
    """Columnas equivalentes a vw_solicitudes_disponibles_taller + estado de bandeja."""
    su = aliased(SolicitudUbicacion)
    return (
        select(
            SolicitudTallerBandeja.id.label("bandeja_id"),
            SolicitudTallerBandeja.taller_id,
            SolicitudEmergencia.id.label("solicitud_id"),
            SolicitudEmergencia.estado.label("estado_solicitud"),
            SolicitudEmergencia.descripcion_texto,
            SolicitudEmergencia.created_at,
            SolicitudEmergencia.vehiculo_id,
            Vehiculo.placa,
            MarcaVehiculo.nombre.label("marca"),
            ModeloVehiculo.nombre.label("modelo"),
            TipoVehiculo.nombre.label("tipo_vehiculo"),
            Cliente.id.label("cliente_id"),
            Usuario.nombres,
            Usuario.apellidos,
            su.latitud,
            su.longitud,
            su.direccion_referencia,
            SolicitudEmergencia.ai_payload,
            SolicitudTallerBandeja.estado.label("estado_bandeja"),
            SolicitudTallerBandeja.motivo_rechazo,
            SolicitudTallerBandeja.creado_at.label("bandeja_creado_at"),
            SolicitudTallerBandeja.respondido_at,
        )
        .select_from(SolicitudTallerBandeja)
        .join(SolicitudEmergencia, SolicitudEmergencia.id == SolicitudTallerBandeja.solicitud_id)
        .join(Vehiculo, Vehiculo.id == SolicitudEmergencia.vehiculo_id)
        .join(Cliente, Cliente.id == SolicitudEmergencia.cliente_id)
        .join(Usuario, Usuario.id == Cliente.usuario_id)
        .outerjoin(MarcaVehiculo, MarcaVehiculo.id == Vehiculo.marca_id)
        .outerjoin(ModeloVehiculo, ModeloVehiculo.id == Vehiculo.modelo_id)
        .outerjoin(TipoVehiculo, TipoVehiculo.id == Vehiculo.tipo_vehiculo_id)
        .outerjoin(
            su,
            and_(su.solicitud_id == SolicitudEmergencia.id, su.es_actual.is_(True)),
        )
    )


async def insert_bandeja_pendiente_por_cada_taller(
    db: AsyncSession, *, solicitud_id: int, creado_at: datetime
) -> None:
    """Al crear una solicitud, una fila PENDIENTE por taller (CU25)."""
    res = await db.execute(select(Taller.id))
    for (tid,) in res.fetchall():
        db.add(
            SolicitudTallerBandeja(
                solicitud_id=solicitud_id,
                taller_id=tid,
                estado=EstadoBandejaTallerEnum.PENDIENTE,
                creado_at=creado_at,
            )
        )
    await db.flush()


async def list_bandeja_pendiente_por_taller(
    db: AsyncSession, *, taller_id: int
) -> list[dict[str, Any]]:
    stmt = (
        _incidente_select()
        .where(
            SolicitudTallerBandeja.taller_id == taller_id,
            SolicitudTallerBandeja.estado == EstadoBandejaTallerEnum.PENDIENTE,
        )
        .order_by(SolicitudEmergencia.created_at.desc())
    )
    r = await db.execute(stmt)
    rows = r.mappings().all()
    return [dict(x) for x in rows]


async def get_bandeja_detalle_por_taller(
    db: AsyncSession, *, bandeja_id: int, taller_id: int
) -> dict[str, Any] | None:
    stmt = _incidente_select().where(
        SolicitudTallerBandeja.id == bandeja_id,
        SolicitudTallerBandeja.taller_id == taller_id,
    )
    r = await db.execute(stmt)
    row = r.mappings().one_or_none()
    return dict(row) if row else None


async def get_bandeja_row(
    db: AsyncSession, *, bandeja_id: int, taller_id: int
) -> SolicitudTallerBandeja | None:
    res = await db.execute(
        select(SolicitudTallerBandeja).where(
            SolicitudTallerBandeja.id == bandeja_id,
            SolicitudTallerBandeja.taller_id == taller_id,
        )
    )
    return res.scalar_one_or_none()


async def list_evidencias_por_solicitud(
    db: AsyncSession, *, solicitud_id: int
) -> list[SolicitudEvidencia]:
    """Fotos y audios asociados a la solicitud (orden cronológico)."""
    r = await db.execute(
        select(SolicitudEvidencia)
        .where(SolicitudEvidencia.solicitud_id == solicitud_id)
        .order_by(SolicitudEvidencia.created_at.asc())
    )
    return list(r.scalars().all())


async def get_disponibilidad(
    db: AsyncSession, *, taller_id: int
) -> TallerDisponibilidad | None:
    res = await db.execute(
        select(TallerDisponibilidad).where(TallerDisponibilidad.taller_id == taller_id)
    )
    return res.scalar_one_or_none()


async def insert_disponibilidad_default(
    db: AsyncSession, *, taller_id: int, updated_at: datetime
) -> TallerDisponibilidad:
    row = TallerDisponibilidad(
        taller_id=taller_id,
        acepta_nuevas_solicitudes=True,
        capacidad_maxima_diaria=10,
        servicios_activos=0,
        observacion=None,
        updated_by_usuario_id=None,
        updated_at=updated_at,
    )
    db.add(row)
    await db.flush()
    return row


async def update_disponibilidad(
    db: AsyncSession,
    *,
    row: TallerDisponibilidad,
    acepta_nuevas_solicitudes: bool | None,
    capacidad_maxima_diaria: int | None,
    observacion: str | None,
    updated_by_usuario_id: int | None,
    updated_at: datetime,
) -> None:
    if acepta_nuevas_solicitudes is not None:
        row.acepta_nuevas_solicitudes = acepta_nuevas_solicitudes
    if capacidad_maxima_diaria is not None:
        row.capacidad_maxima_diaria = capacidad_maxima_diaria
    if observacion is not None:
        st = observacion.strip()
        row.observacion = st if st else None
    row.updated_by_usuario_id = updated_by_usuario_id
    row.updated_at = updated_at


async def marcar_bandeja(
    db: AsyncSession,
    *,
    bandeja_id: int,
    taller_id: int,
    estado: EstadoBandejaTallerEnum,
    respondido_at: datetime,
    motivo_rechazo: str | None = None,
) -> int:
    """Devuelve filas afectadas (0 si no hubo match o ya no estaba PENDIENTE)."""
    values: dict[str, Any] = {
        "estado": estado,
        "respondido_at": respondido_at,
    }
    if motivo_rechazo is not None:
        values["motivo_rechazo"] = motivo_rechazo
    res = await db.execute(
        update(SolicitudTallerBandeja)
        .where(
            SolicitudTallerBandeja.id == bandeja_id,
            SolicitudTallerBandeja.taller_id == taller_id,
            SolicitudTallerBandeja.estado == EstadoBandejaTallerEnum.PENDIENTE,
        )
        .values(**values)
    )
    return int(res.rowcount or 0)


async def expirar_otras_bandeja_pendientes(
    db: AsyncSession,
    *,
    solicitud_id: int,
    bandeja_ganadora_id: int,
    respondido_at: datetime,
) -> None:
    await db.execute(
        update(SolicitudTallerBandeja)
        .where(
            SolicitudTallerBandeja.solicitud_id == solicitud_id,
            SolicitudTallerBandeja.id != bandeja_ganadora_id,
            SolicitudTallerBandeja.estado == EstadoBandejaTallerEnum.PENDIENTE,
        )
        .values(estado=EstadoBandejaTallerEnum.EXPIRADA, respondido_at=respondido_at)
    )


async def get_tecnico_del_taller_activo(
    db: AsyncSession, *, tecnico_id: int, taller_id: int
) -> Tecnico | None:
    res = await db.execute(
        select(Tecnico).where(
            Tecnico.id == tecnico_id,
            Tecnico.taller_id == taller_id,
            Tecnico.estado == EstadoTecnicoEnum.ACTIVO,
        )
    )
    return res.scalar_one_or_none()


async def list_asignaciones_tecnico_por_solicitud_taller(
    db: AsyncSession, *, solicitud_id: int, taller_id: int
) -> list[SolicitudAsignacionTecnico]:
    res = await db.execute(
        select(SolicitudAsignacionTecnico)
        .where(
            SolicitudAsignacionTecnico.solicitud_id == solicitud_id,
            SolicitudAsignacionTecnico.taller_id == taller_id,
        )
        .order_by(SolicitudAsignacionTecnico.created_at.asc())
    )
    return list(res.scalars().all())


async def find_asignacion_activa_mismo_tecnico(
    db: AsyncSession, *, solicitud_id: int, taller_id: int, tecnico_id: int
) -> SolicitudAsignacionTecnico | None:
    res = await db.execute(
        select(SolicitudAsignacionTecnico)
        .where(
            SolicitudAsignacionTecnico.solicitud_id == solicitud_id,
            SolicitudAsignacionTecnico.taller_id == taller_id,
            SolicitudAsignacionTecnico.tecnico_id == tecnico_id,
            SolicitudAsignacionTecnico.estado == EstadoAsignacionTecnicoEnum.ASIGNADO,
        )
        .order_by(SolicitudAsignacionTecnico.created_at.desc())
        .limit(1)
    )
    return res.scalar_one_or_none()


async def marcar_asignaciones_activas_como_reasignado(
    db: AsyncSession, *, solicitud_id: int, taller_id: int
) -> None:
    await db.execute(
        update(SolicitudAsignacionTecnico)
        .where(
            SolicitudAsignacionTecnico.solicitud_id == solicitud_id,
            SolicitudAsignacionTecnico.taller_id == taller_id,
            SolicitudAsignacionTecnico.estado == EstadoAsignacionTecnicoEnum.ASIGNADO,
        )
        .values(estado=EstadoAsignacionTecnicoEnum.REASIGNADO)
    )


async def insert_asignacion_tecnico(
    db: AsyncSession,
    *,
    solicitud_id: int,
    taller_id: int,
    tecnico_id: int,
    estado: EstadoAsignacionTecnicoEnum,
    asignado_por_usuario_id: int | None,
    observacion: str | None,
    created_at: datetime,
) -> SolicitudAsignacionTecnico:
    row = SolicitudAsignacionTecnico(
        solicitud_id=solicitud_id,
        taller_id=taller_id,
        tecnico_id=tecnico_id,
        estado=estado,
        asignado_por_usuario_id=asignado_por_usuario_id,
        observacion=observacion,
        created_at=created_at,
    )
    db.add(row)
    await db.flush()
    return row


def _historial_atenciones_select():
    """Equivalente a vw_historial_atenciones_taller con filtro taller en llamada."""
    stb_hist = aliased(SolicitudTallerBandeja)
    return (
        select(
            SolicitudEmergencia.id.label("solicitud_id"),
            SolicitudEmergencia.taller_id,
            SolicitudEmergencia.tecnico_id,
            SolicitudEmergencia.estado,
            SolicitudEmergencia.created_at,
            SolicitudEmergencia.finalizada_at,
            Usuario.nombres,
            Usuario.apellidos,
            Vehiculo.placa,
            MarcaVehiculo.nombre.label("marca"),
            ModeloVehiculo.nombre.label("modelo"),
            TipoVehiculo.nombre.label("tipo_vehiculo"),
            stb_hist.id.label("bandeja_id"),
        )
        .select_from(SolicitudEmergencia)
        .outerjoin(
            stb_hist,
            and_(
                stb_hist.solicitud_id == SolicitudEmergencia.id,
                stb_hist.taller_id == SolicitudEmergencia.taller_id,
            ),
        )
        .join(Cliente, Cliente.id == SolicitudEmergencia.cliente_id)
        .join(Usuario, Usuario.id == Cliente.usuario_id)
        .join(Vehiculo, Vehiculo.id == SolicitudEmergencia.vehiculo_id)
        .outerjoin(MarcaVehiculo, MarcaVehiculo.id == Vehiculo.marca_id)
        .outerjoin(ModeloVehiculo, ModeloVehiculo.id == Vehiculo.modelo_id)
        .outerjoin(TipoVehiculo, TipoVehiculo.id == Vehiculo.tipo_vehiculo_id)
        .where(SolicitudEmergencia.taller_id.is_not(None))
    )


async def list_historial_atenciones_taller(
    db: AsyncSession,
    *,
    taller_id: int,
    estado: EstadoSolicitudSeguimientoEnum | None,
    desde: datetime | None,
    hasta: datetime | None,
    limit: int,
) -> list[dict[str, Any]]:
    stmt = _historial_atenciones_select().where(SolicitudEmergencia.taller_id == taller_id)
    if estado is not None:
        stmt = stmt.where(SolicitudEmergencia.estado == estado)
    if desde is not None:
        stmt = stmt.where(SolicitudEmergencia.created_at >= desde)
    if hasta is not None:
        stmt = stmt.where(SolicitudEmergencia.created_at <= hasta)
    stmt = stmt.order_by(SolicitudEmergencia.created_at.desc()).limit(limit)
    r = await db.execute(stmt)
    return [dict(x) for x in r.mappings().all()]


async def list_comisiones_taller_con_pago(
    db: AsyncSession, *, taller_id: int
) -> list[dict[str, Any]]:
    stb_com = aliased(SolicitudTallerBandeja)
    stmt = (
        select(
            ComisionTaller.id,
            ComisionTaller.solicitud_id,
            ComisionTaller.taller_id,
            ComisionTaller.pago_id,
            ComisionTaller.porcentaje_plataforma,
            ComisionTaller.monto_servicio,
            ComisionTaller.monto_comision,
            ComisionTaller.monto_taller_neto,
            ComisionTaller.estado,
            ComisionTaller.calculado_at,
            ComisionTaller.liquidado_at,
            Pago.monto.label("pago_monto"),
            Pago.estado.label("pago_estado"),
            Pago.pagado_at.label("pago_pagado_at"),
            Pago.moneda.label("pago_moneda"),
            stb_com.id.label("bandeja_id"),
        )
        .select_from(ComisionTaller)
        .outerjoin(
            stb_com,
            and_(
                stb_com.solicitud_id == ComisionTaller.solicitud_id,
                stb_com.taller_id == ComisionTaller.taller_id,
            ),
        )
        .outerjoin(Pago, Pago.id == ComisionTaller.pago_id)
        .where(ComisionTaller.taller_id == taller_id)
        .order_by(ComisionTaller.calculado_at.desc())
    )
    r = await db.execute(stmt)
    return [dict(x) for x in r.mappings().all()]


async def resumen_comisiones_taller(db: AsyncSession, *, taller_id: int) -> dict[str, Any]:
    stmt = select(
        func.count(ComisionTaller.id).label("total_registros"),
        func.coalesce(func.sum(ComisionTaller.monto_servicio), 0).label("total_servicios"),
        func.coalesce(func.sum(ComisionTaller.monto_comision), 0).label("total_comision"),
        func.coalesce(func.sum(ComisionTaller.monto_taller_neto), 0).label("total_neto"),
    ).where(ComisionTaller.taller_id == taller_id)
    r = await db.execute(stmt)
    row = r.mappings().one()
    return {
        "taller_id": taller_id,
        "total_registros": int(row["total_registros"] or 0),
        "total_servicios": row["total_servicios"],
        "total_comision": row["total_comision"],
        "total_neto": row["total_neto"],
    }


async def resumen_comisiones_taller_rango(
    db: AsyncSession,
    *,
    taller_id: int,
    desde: datetime | None = None,
    hasta: datetime | None = None,
) -> dict[str, Any]:
    """Totales de comisiones en un rango (por `calculado_at`)."""
    stmt = select(
        func.count(ComisionTaller.id).label("total_registros"),
        func.coalesce(func.sum(ComisionTaller.monto_servicio), 0).label("total_servicios"),
        func.coalesce(func.sum(ComisionTaller.monto_comision), 0).label("total_comision"),
        func.coalesce(func.sum(ComisionTaller.monto_taller_neto), 0).label("total_neto"),
    ).where(ComisionTaller.taller_id == taller_id)
    if desde is not None:
        stmt = stmt.where(ComisionTaller.calculado_at >= desde)
    if hasta is not None:
        stmt = stmt.where(ComisionTaller.calculado_at <= hasta)
    r = await db.execute(stmt)
    row = r.mappings().one()
    return {
        "taller_id": taller_id,
        "total_registros": int(row["total_registros"] or 0),
        "total_servicios": row["total_servicios"],
        "total_comision": row["total_comision"],
        "total_neto": row["total_neto"],
    }


async def agregado_montos_por_tecnico(
    db: AsyncSession,
    *,
    taller_id: int,
    desde: datetime | None = None,
    hasta: datetime | None = None,
) -> list[dict[str, Any]]:
    """
    Suma monto de servicio / comisión / neto del taller por técnico asignado a la solicitud
    (según comisiones emitidas; una fila de comisión por solicitud paga).
    """
    stmt = (
        select(
            Tecnico.id.label("tecnico_id"),
            Usuario.nombres,
            Usuario.apellidos,
            func.count(ComisionTaller.id).label("comisiones_registradas"),
            func.coalesce(func.sum(ComisionTaller.monto_servicio), 0).label("total_monto_servicio"),
            func.coalesce(func.sum(ComisionTaller.monto_comision), 0).label("total_monto_comision"),
            func.coalesce(func.sum(ComisionTaller.monto_taller_neto), 0).label("total_monto_taller_neto"),
        )
        .select_from(ComisionTaller)
        .join(SolicitudEmergencia, SolicitudEmergencia.id == ComisionTaller.solicitud_id)
        .join(Tecnico, Tecnico.id == SolicitudEmergencia.tecnico_id)
        .join(Usuario, Usuario.id == Tecnico.usuario_id)
        .where(ComisionTaller.taller_id == taller_id)
        .where(SolicitudEmergencia.tecnico_id.isnot(None))
    )
    if desde is not None:
        stmt = stmt.where(ComisionTaller.calculado_at >= desde)
    if hasta is not None:
        stmt = stmt.where(ComisionTaller.calculado_at <= hasta)
    stmt = (
        stmt.group_by(Tecnico.id, Usuario.nombres, Usuario.apellidos)
        .order_by(func.sum(ComisionTaller.monto_taller_neto).desc().nulls_last())
    )
    r = await db.execute(stmt)
    return [dict(x) for x in r.mappings().all()]


async def contar_solicitudes_por_estado_taller(
    db: AsyncSession,
    *,
    taller_id: int,
    desde: datetime | None = None,
    hasta: datetime | None = None,
) -> list[tuple[EstadoSolicitudSeguimientoEnum, int]]:
    """Conteo de solicitudes del taller en el periodo (por `created_at` de la solicitud)."""
    stmt = select(SolicitudEmergencia.estado, func.count().label("n")).where(
        SolicitudEmergencia.taller_id == taller_id
    )
    if desde is not None:
        stmt = stmt.where(SolicitudEmergencia.created_at >= desde)
    if hasta is not None:
        stmt = stmt.where(SolicitudEmergencia.created_at <= hasta)
    stmt = stmt.group_by(SolicitudEmergencia.estado)
    r = await db.execute(stmt)
    return [(row[0], int(row[1] or 0)) for row in r.all()]


async def contar_bandeja_pendientes_taller(db: AsyncSession, *, taller_id: int) -> int:
    stmt = select(func.count()).select_from(SolicitudTallerBandeja).where(
        SolicitudTallerBandeja.taller_id == taller_id,
        SolicitudTallerBandeja.estado == EstadoBandejaTallerEnum.PENDIENTE,
    )
    n = (await db.execute(stmt)).scalar_one()
    return int(n or 0)
