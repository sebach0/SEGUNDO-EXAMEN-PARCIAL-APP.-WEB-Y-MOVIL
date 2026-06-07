# Servicio — cotizaciones (marketplace tipo Uber/InDrive)
from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.geo import haversine_km
from app.core.timeutil import utc_now_naive
from app.modules.acceso_y_administracion.bitacora.models import AccionBitacoraEnum
from app.modules.acceso_y_administracion.bitacora.service import registrar_accion
from app.modules.atencion.taller_emergencias import repository as bandeja_repository
from app.modules.atencion.taller_emergencias.models import EstadoBandejaTallerEnum, SolicitudTallerBandeja
from app.modules.atencion.taller_emergencias.service import helpers as bandeja_helpers
from app.modules.comunicacion_y_notificaciones.notificaciones import service as notificaciones_service
from app.modules.comunicacion_y_notificaciones.notificaciones.models import TipoNotificacionEnum
from app.modules.cotizaciones.models import Cotizacion, CotizacionItem, EstadoCotizacionEnum
from app.modules.cotizaciones.schemas import (
    CotizacionContextoRead,
    CotizacionCreateIn,
    CotizacionItemIn,
    CotizacionRead,
    ServicioOfrecidoRead,
)
from app.modules.incidentes.emergencias import repository as emergencias_repository
from app.modules.incidentes.emergencias.models import (
    EstadoSolicitudSeguimientoEnum,
    SolicitudEmergencia,
    SolicitudUbicacion,
)
from app.modules.incidentes.emergencias.solicitud_lifecycle import (
    aplicar_timestamps_por_estado,
    registrar_eta,
)
from app.modules.incidentes.emergencias.eta_service import emit_eta_actualizado_ws
from app.modules.incidentes.emergencias.models import EtaOrigenEnum
from app.modules.talleres_y_tecnicos.talleres.models import Taller
from app.modules.talleres_y_tecnicos.talleres.service import get_servicios_taller


TRASLADO_ITEM_DESCRIPCION = "Traslado del técnico al lugar de la emergencia"


def _tarifa_traslado_bs_km() -> Decimal:
    return Decimal(str(settings.COTIZACION_TARIFA_TRASLADO_BS_KM))


def _calcular_costo_traslado(distancia_km: Decimal | None) -> Decimal:
    if distancia_km is None or distancia_km <= 0:
        return Decimal("0")
    return (distancia_km * _tarifa_traslado_bs_km()).quantize(Decimal("0.01"))


def _es_item_traslado(descripcion: str) -> bool:
    d = descripcion.lower().strip()
    return "traslado" in d and ("técnico" in d or "tecnico" in d)


def _item_traslado_in(distancia_km: Decimal) -> CotizacionItemIn:
    tarifa = _tarifa_traslado_bs_km()
    return CotizacionItemIn(
        descripcion=TRASLADO_ITEM_DESCRIPCION,
        cantidad=distancia_km,
        precio_unitario=tarifa,
    )


def _servicios_from_json(raw: list | None) -> list[ServicioOfrecidoRead]:
    if not raw:
        return []
    out: list[ServicioOfrecidoRead] = []
    for item in raw:
        if isinstance(item, dict) and item.get("id") is not None:
            out.append(
                ServicioOfrecidoRead(
                    id=int(item["id"]),
                    nombre=str(item.get("nombre") or ""),
                    codigo=str(item.get("codigo") or ""),
                )
            )
    return out


def _to_read(cot: Cotizacion, taller_nombre: str | None = None) -> CotizacionRead:
    d = CotizacionRead.model_validate(cot)
    d.taller_nombre = taller_nombre
    d.servicios_ofrecidos = _servicios_from_json(cot.servicios_ofrecidos)
    return d


async def _get_cot_with_items(db: AsyncSession, cotizacion_id: int) -> Cotizacion | None:
    result = await db.execute(
        select(Cotizacion)
        .options(selectinload(Cotizacion.items))
        .where(Cotizacion.id == cotizacion_id)
    )
    return result.scalar_one_or_none()


async def _coords_solicitud(db: AsyncSession, solicitud_id: int) -> tuple[float, float] | None:
    res = await db.execute(
        select(SolicitudUbicacion).where(
            SolicitudUbicacion.solicitud_id == solicitud_id,
            SolicitudUbicacion.es_actual.is_(True),
        )
    )
    u = res.scalar_one_or_none()
    if u is None:
        res2 = await db.execute(
            select(SolicitudUbicacion)
            .where(SolicitudUbicacion.solicitud_id == solicitud_id)
            .order_by(SolicitudUbicacion.registrado_at.desc())
            .limit(1)
        )
        u = res2.scalar_one_or_none()
    if u is None:
        return None
    return float(u.latitud), float(u.longitud)


async def calcular_distancia_km(
    db: AsyncSession,
    *,
    solicitud_id: int,
    taller_id: int,
) -> Decimal | None:
    coords = await _coords_solicitud(db, solicitud_id)
    if coords is None:
        return None
    res = await db.execute(
        select(Taller.latitud, Taller.longitud).where(Taller.id == taller_id)
    )
    row = res.one_or_none()
    if row is None or row[0] is None or row[1] is None:
        return None
    km = haversine_km(coords[0], coords[1], float(row[0]), float(row[1]))
    return Decimal(str(round(km, 2)))


async def contexto_oferta_taller(
    *,
    solicitud_id: int,
    taller_id: int,
    db: AsyncSession,
) -> CotizacionContextoRead:
    res_sol = await db.execute(
        select(SolicitudEmergencia).where(SolicitudEmergencia.id == solicitud_id)
    )
    if res_sol.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada.")

    res_t = await db.execute(select(Taller).where(Taller.id == taller_id))
    taller = res_t.scalar_one_or_none()
    if taller is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Taller no encontrado.")

    servicios = await get_servicios_taller(taller_id, db)
    distancia = await calcular_distancia_km(db, solicitud_id=solicitud_id, taller_id=taller_id)
    coords_inc = await _coords_solicitud(db, solicitud_id)

    eta_sugerida: int | None = None
    if distancia is not None:
        km = float(distancia)
        # Distancias > 150 km suelen ser GPS erróneo; no sugerir ETA absurdo.
        if km <= 150:
            # ~35 km/h promedio urbano → minutos de llegada aproximados (máx. 8 h sugeridas)
            raw = max(5, int((km / 35.0) * 60 + 0.5))
            eta_sugerida = min(raw, 480)

    res_exist = await db.execute(
        select(Cotizacion.id).where(
            Cotizacion.solicitud_id == solicitud_id,
            Cotizacion.taller_id == taller_id,
            Cotizacion.estado.notin_([EstadoCotizacionEnum.RECHAZADA, EstadoCotizacionEnum.EXPIRADA]),
        )
    )
    cotizacion_activa = res_exist.scalar_one_or_none() is not None

    tarifa = _tarifa_traslado_bs_km()
    costo_traslado = _calcular_costo_traslado(distancia)

    return CotizacionContextoRead(
        distancia_km=distancia,
        tarifa_traslado_bs_km=tarifa,
        costo_traslado_estimado=costo_traslado if costo_traslado > 0 else None,
        servicios_disponibles=[
            ServicioOfrecidoRead(id=s.id, nombre=s.nombre, codigo=s.codigo) for s in servicios
        ],
        tiene_grua=bool(taller.tiene_grua),
        cotizacion_activa=cotizacion_activa,
        taller_tiene_ubicacion=(taller.latitud is not None and taller.longitud is not None),
        taller_lat=taller.latitud,
        taller_lng=taller.longitud,
        incidente_lat=Decimal(str(coords_inc[0])) if coords_inc else None,
        incidente_lng=Decimal(str(coords_inc[1])) if coords_inc else None,
        eta_sugerida_min=eta_sugerida,
    )


async def _snapshot_servicios_taller(db: AsyncSession, taller_id: int) -> list[dict]:
    servicios = await get_servicios_taller(taller_id, db)
    return [{"id": s.id, "nombre": s.nombre, "codigo": s.codigo} for s in servicios]


async def _finalizar_asignacion_por_cotizacion(
    db: AsyncSession,
    *,
    sol: SolicitudEmergencia,
    taller_id: int,
    now,
) -> None:
    """Marca bandeja ganadora, expira competidores e incrementa carga del taller."""
    res_b = await db.execute(
        select(SolicitudTallerBandeja).where(
            SolicitudTallerBandeja.solicitud_id == sol.id,
            SolicitudTallerBandeja.taller_id == taller_id,
        )
    )
    bandeja = res_b.scalar_one_or_none()
    if bandeja is not None and bandeja.estado == EstadoBandejaTallerEnum.PENDIENTE:
        await bandeja_repository.marcar_bandeja(
            db,
            bandeja_id=bandeja.id,
            taller_id=taller_id,
            estado=EstadoBandejaTallerEnum.ACEPTADA,
            respondido_at=now,
        )
        await bandeja_repository.expirar_otras_bandeja_pendientes(
            db,
            solicitud_id=sol.id,
            bandeja_ganadora_id=bandeja.id,
            respondido_at=now,
        )

    disp = await bandeja_helpers.ensure_disponibilidad(db, taller_id)
    if disp.servicios_activos < disp.capacidad_maxima_diaria:
        disp.servicios_activos = int(disp.servicios_activos) + 1
        disp.updated_at = now

    await notificaciones_service.notificar_cliente_solicitud_emergencia(
        db,
        solicitud=sol,
        tipo=TipoNotificacionEnum.TALLER_ASIGNADO,
        titulo="Taller seleccionado",
        mensaje="Elegiste un taller para tu emergencia. Podés ver el seguimiento en la app.",
    )


# ── Proponer cotización (taller) ──────────────────────────────────────────────

async def proponer_cotizacion(
    *,
    solicitud_id: int,
    taller_id: int,
    body: CotizacionCreateIn,
    db: AsyncSession,
) -> CotizacionRead:
    res_sol = await db.execute(
        select(SolicitudEmergencia).where(SolicitudEmergencia.id == solicitud_id)
    )
    sol = res_sol.scalar_one_or_none()
    if sol is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada.")

    if sol.taller_id is not None and sol.taller_id != taller_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La solicitud ya fue asignada a otro taller.",
        )

    estados_validos = {
        EstadoSolicitudSeguimientoEnum.REGISTRADA,
        EstadoSolicitudSeguimientoEnum.EN_REVISION,
    }
    if sol.estado not in estados_validos:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No se puede cotizar en estado '{sol.estado.value}'.",
        )

    res_exist = await db.execute(
        select(Cotizacion).where(
            Cotizacion.solicitud_id == solicitud_id,
            Cotizacion.taller_id == taller_id,
            Cotizacion.estado.notin_([EstadoCotizacionEnum.RECHAZADA, EstadoCotizacionEnum.EXPIRADA]),
        )
    )
    if res_exist.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una cotización activa de este taller para esta solicitud.",
        )

    distancia = await calcular_distancia_km(db, solicitud_id=solicitud_id, taller_id=taller_id)
    servicios_snapshot = await _snapshot_servicios_taller(db, taller_id)
    costo_traslado = _calcular_costo_traslado(distancia)

    user_items = [i for i in body.items if not _es_item_traslado(i.descripcion)]
    items_finales: list[CotizacionItemIn] = list(user_items)
    if costo_traslado > 0 and distancia is not None:
        items_finales.append(_item_traslado_in(distancia))

    monto_final = body.monto_total + costo_traslado

    now = utc_now_naive()
    cot = Cotizacion(
        solicitud_id=solicitud_id,
        taller_id=taller_id,
        estado=EstadoCotizacionEnum.ENVIADA,
        descripcion_danio=body.descripcion_danio,
        detalle_servicio=body.detalle_servicio,
        monto_total=monto_final,
        tiempo_estimado_llegada_min=body.tiempo_estimado_llegada_min,
        tiempo_estimado_reparacion_min=body.tiempo_estimado_reparacion_min,
        incluye_grua=body.incluye_grua,
        garantia_descripcion=body.garantia_descripcion,
        comentarios=body.comentarios,
        distancia_km=distancia,
        servicios_ofrecidos=servicios_snapshot,
        creado_at=now,
        actualizado_at=now,
    )
    db.add(cot)
    await db.flush()

    for item_in in items_finales:
        db.add(
            CotizacionItem(
                cotizacion_id=cot.id,
                descripcion=item_in.descripcion,
                cantidad=item_in.cantidad,
                precio_unitario=item_in.precio_unitario,
            )
        )
    await db.flush()

    if sol.estado == EstadoSolicitudSeguimientoEnum.REGISTRADA:
        sol.estado = EstadoSolicitudSeguimientoEnum.EN_REVISION
        aplicar_timestamps_por_estado(sol, EstadoSolicitudSeguimientoEnum.EN_REVISION, now)
        sol.updated_at = now

    res_t = await db.execute(select(Taller.nombre_comercial).where(Taller.id == taller_id))
    nombre_taller = res_t.scalar_one_or_none() or "Un taller"

    await notificaciones_service.notificar_cliente_solicitud_emergencia(
        db,
        solicitud=sol,
        tipo=TipoNotificacionEnum.ESTADO_ACTUALIZADO,
        titulo="Nueva cotización disponible",
        mensaje=(
            f"{nombre_taller} envió una propuesta de Bs. {monto_final:.2f}. "
            "Compará precio, distancia y servicios en la app."
        ),
    )

    cot_full = await _get_cot_with_items(db, cot.id)
    assert cot_full is not None
    return _to_read(cot_full, nombre_taller)


# ── Listar cotizaciones de una solicitud ──────────────────────────────────────

async def listar_cotizaciones(
    *,
    solicitud_id: int,
    db: AsyncSession,
) -> list[CotizacionRead]:
    result = await db.execute(
        select(Cotizacion)
        .options(selectinload(Cotizacion.items))
        .where(Cotizacion.solicitud_id == solicitud_id)
        .order_by(Cotizacion.distancia_km.asc().nullslast(), Cotizacion.monto_total.asc())
    )
    cots = result.scalars().all()

    taller_ids = list({c.taller_id for c in cots})
    nombres_map: dict[int, str] = {}
    if taller_ids:
        res_n = await db.execute(
            select(Taller.id, Taller.nombre_comercial).where(Taller.id.in_(taller_ids))
        )
        for tid, nombre in res_n.all():
            nombres_map[tid] = nombre

    return [_to_read(c, nombres_map.get(c.taller_id)) for c in cots]


# ── Seleccionar cotización (cliente) ──────────────────────────────────────────

async def seleccionar_cotizacion(
    *,
    solicitud_id: int,
    cotizacion_id: int,
    db: AsyncSession,
) -> CotizacionRead:
    res_sol = await db.execute(
        select(SolicitudEmergencia)
        .where(SolicitudEmergencia.id == solicitud_id)
        .with_for_update()
    )
    sol = res_sol.scalar_one_or_none()
    if sol is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada.")

    res_ya = await db.execute(
        select(Cotizacion).where(
            Cotizacion.solicitud_id == solicitud_id,
            Cotizacion.estado == EstadoCotizacionEnum.ACEPTADA,
        )
    )
    if res_ya.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una cotización aceptada para esta solicitud.",
        )

    res_cot = await db.execute(
        select(Cotizacion)
        .options(selectinload(Cotizacion.items))
        .where(Cotizacion.id == cotizacion_id, Cotizacion.solicitud_id == solicitud_id)
        .with_for_update()
    )
    cot = res_cot.scalar_one_or_none()
    if cot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cotización no encontrada.")
    if cot.estado != EstadoCotizacionEnum.ENVIADA:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"La cotización no está disponible (estado: {cot.estado.value}).",
        )

    now = utc_now_naive()

    cot.estado = EstadoCotizacionEnum.ACEPTADA
    cot.seleccionada_at = now
    cot.actualizado_at = now

    res_otras = await db.execute(
        select(Cotizacion).where(
            Cotizacion.solicitud_id == solicitud_id,
            Cotizacion.id != cotizacion_id,
            Cotizacion.estado == EstadoCotizacionEnum.ENVIADA,
        )
    )
    for otra in res_otras.scalars().all():
        otra.estado = EstadoCotizacionEnum.EXPIRADA
        otra.actualizado_at = now

    estado_anterior = sol.estado
    sol.taller_id = cot.taller_id
    if sol.estado in (
        EstadoSolicitudSeguimientoEnum.REGISTRADA,
        EstadoSolicitudSeguimientoEnum.EN_REVISION,
    ):
        sol.estado = EstadoSolicitudSeguimientoEnum.TALLER_ASIGNADO
        aplicar_timestamps_por_estado(sol, EstadoSolicitudSeguimientoEnum.TALLER_ASIGNADO, now)
        await emergencias_repository.insert_historial_estado(
            db,
            solicitud_id=sol.id,
            estado_anterior=estado_anterior,
            estado_nuevo=EstadoSolicitudSeguimientoEnum.TALLER_ASIGNADO,
            usuario_id=None,
            observacion="Cliente seleccionó cotización de taller",
            created_at=now,
        )
    sol.updated_at = now

    if cot.tiempo_estimado_llegada_min is not None:
        registrar_eta(sol, cot.tiempo_estimado_llegada_min, EtaOrigenEnum.COTIZACION, now)
        await emit_eta_actualizado_ws(sol)

    await _finalizar_asignacion_por_cotizacion(db, sol=sol, taller_id=cot.taller_id, now=now)

    if sol.estado == EstadoSolicitudSeguimientoEnum.TALLER_ASIGNADO:
        from app.modules.acceso_y_administracion.usuarios.models import Usuario
        from app.modules.atencion.taller_emergencias.service.asignaciones import (
            asignar_tecnico_automatico,
        )

        res_taller = await db.execute(
            select(Taller.usuario_responsable_id).where(Taller.id == cot.taller_id)
        )
        responsable_id = res_taller.scalar_one_or_none()
        if responsable_id is not None:
            res_user = await db.execute(select(Usuario).where(Usuario.id == responsable_id))
            responsable = res_user.scalar_one_or_none()
            if responsable is not None:
                await asignar_tecnico_automatico(
                    responsable,
                    cot.taller_id,
                    solicitud_id,
                    db,
                    observacion="Asignación automática al aceptar cotización del cliente",
                    tiempo_estimado_min=cot.tiempo_estimado_llegada_min,
                )

    await registrar_accion(
        db,
        "cotizaciones",
        "cotizaciones",
        AccionBitacoraEnum.ACTUALIZAR,
        descripcion=f"Cliente seleccionó cotización_id={cotizacion_id} solicitud_id={solicitud_id}",
        entidad_id=cotizacion_id,
    )

    await db.flush()

    res_t = await db.execute(select(Taller.nombre_comercial).where(Taller.id == cot.taller_id))
    nombre = res_t.scalar_one_or_none()
    return _to_read(cot, nombre)
