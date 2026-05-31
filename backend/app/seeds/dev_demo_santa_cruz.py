# Seed idempotente: vehículos + solicitudes + bandeja + asignaciones + pagos/comisiones (demo Santa Cruz, BO).
# Ejecutar después de cliente, taller, técnico y catálogos. Marcador en descripción: [DEMO-SC]
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.timeutil import utc_now_naive
from app.modules.incidentes.emergencias import repository as em_repo
from app.modules.incidentes.emergencias.models import (
    EstadoSolicitudSeguimientoEnum,
    SolicitudEmergencia,
    TipoEvidenciaSolicitudEnum,
)
from app.modules.pagos_y_comisiones.pagos.models import EstadoPagoEnum, MetodoPagoEnum, Pago
from app.modules.atencion.taller_emergencias import repository as pt_repo
from app.modules.atencion.taller_emergencias.models import (
    ComisionTaller,
    EstadoAsignacionTecnicoEnum,
    EstadoBandejaTallerEnum,
    EstadoComisionTallerEnum,
    SolicitudTallerBandeja,
)
from app.modules.talleres_y_tecnicos.talleres.models import Taller, Tecnico
from app.modules.clientes_y_vehiculos.clientes.models import Cliente
from app.modules.acceso_y_administracion.usuarios.models import Usuario
from app.modules.clientes_y_vehiculos.vehiculos import service as vehiculos_service
from app.modules.clientes_y_vehiculos.vehiculos.models import MarcaVehiculo, ModeloVehiculo, TipoVehiculo, Vehiculo

from app.seeds.identidades_demo_sc import GEO_SC_CENTRO_LAT as SC_LAT, GEO_SC_CENTRO_LNG as SC_LON

logger = logging.getLogger(__name__)

DEMO_MARKER = "[DEMO-SC]"


async def _ids_catalogo(db: AsyncSession) -> tuple[int, int, int] | None:
    """(tipo_sedan_id, marca_toyota_id, modelo_corolla_id) o None."""
    tr = await db.execute(select(TipoVehiculo).where(TipoVehiculo.nombre == "Sedán"))
    tipo = tr.scalar_one_or_none()
    mr = await db.execute(select(MarcaVehiculo).where(MarcaVehiculo.nombre == "Toyota"))
    marca = mr.scalar_one_or_none()
    if tipo is None or marca is None:
        return None
    modr = await db.execute(
        select(ModeloVehiculo).where(
            ModeloVehiculo.marca_id == marca.id,
            ModeloVehiculo.nombre == "Corolla",
        )
    )
    modelo = modr.scalar_one_or_none()
    if modelo is None:
        return None
    return tipo.id, marca.id, modelo.id


async def _ids_catalogo_alt(
    db: AsyncSession, *, tipo_nombre: str, marca_nombre: str, modelo_nombre: str
) -> tuple[int, int, int] | None:
    tr = await db.execute(select(TipoVehiculo).where(TipoVehiculo.nombre == tipo_nombre))
    tipo = tr.scalar_one_or_none()
    mr = await db.execute(select(MarcaVehiculo).where(MarcaVehiculo.nombre == marca_nombre))
    marca = mr.scalar_one_or_none()
    if tipo is None or marca is None:
        return None
    modr = await db.execute(
        select(ModeloVehiculo).where(
            ModeloVehiculo.marca_id == marca.id,
            ModeloVehiculo.nombre == modelo_nombre,
        )
    )
    modelo = modr.scalar_one_or_none()
    if modelo is None:
        return None
    return tipo.id, marca.id, modelo.id


async def _ctx_demo(
    db: AsyncSession,
) -> tuple[int, int, int, int, int, list[int]] | None:
    """
    cliente_id, taller_id, tecnico_id, usuario_cliente_id, usuario_responsable_id, vehiculo_ids[]
    """
    email_c = (settings.SEED_CLIENTE_EMAIL or "").strip().lower()
    email_t = (settings.SEED_TALLER_EMAIL or "").strip().lower()
    email_tec = (settings.SEED_TECNICO_EMAIL or "").strip().lower()
    if not email_c or not email_t:
        return None
    ur = await db.execute(select(Usuario).where(Usuario.email == email_c))
    uc = ur.scalar_one_or_none()
    if uc is None:
        logger.warning("Demo SC: no existe usuario cliente %s", email_c)
        return None
    cr = await db.execute(select(Cliente).where(Cliente.usuario_id == uc.id))
    cliente = cr.scalar_one_or_none()
    if cliente is None:
        logger.warning("Demo SC: no existe fila clientes para %s", email_c)
        return None
    utr = await db.execute(select(Usuario).where(Usuario.email == email_t))
    ut = utr.scalar_one_or_none()
    if ut is None:
        logger.warning("Demo SC: no existe usuario taller %s", email_t)
        return None
    tlr = await db.execute(select(Taller).where(Taller.usuario_responsable_id == ut.id))
    taller = tlr.scalar_one_or_none()
    if taller is None:
        tlr2 = await db.execute(select(Taller).order_by(Taller.id).limit(1))
        taller = tlr2.scalar_one_or_none()
    if taller is None:
        logger.warning("Demo SC: no hay taller en BD.")
        return None
    tecnico_id: int | None = None
    if email_tec:
        uec = (await db.execute(select(Usuario).where(Usuario.email == email_tec))).scalar_one_or_none()
        if uec is not None:
            tec = (
                await db.execute(select(Tecnico).where(Tecnico.usuario_id == uec.id))
            ).scalar_one_or_none()
            if tec is not None:
                tecnico_id = tec.id
    if tecnico_id is None:
        logger.warning("Demo SC: sin técnico seed; se omiten filas que requieren técnico asignado.")
    veh_rows = await db.execute(
        select(Vehiculo.id)
        .where(Vehiculo.cliente_id == cliente.id)
        .order_by(Vehiculo.id)
    )
    vids = [int(x[0]) for x in veh_rows.fetchall()]
    if not vids:
        logger.warning("Demo SC: el cliente no tiene vehículos (corré ensure_demo_vehiculos antes).")
        return None
    return cliente.id, taller.id, tecnico_id or 0, uc.id, ut.id, vids


async def _count_demo_solicitudes(db: AsyncSession, *, cliente_id: int) -> int:
    r = await db.execute(
        select(func.count())
        .select_from(SolicitudEmergencia)
        .where(
            SolicitudEmergencia.cliente_id == cliente_id,
            SolicitudEmergencia.descripcion_texto.like(f"{DEMO_MARKER}%"),
        )
    )
    return int(r.scalar_one() or 0)


async def _ensure_vehiculo_placa(
    db: AsyncSession,
    *,
    cliente_id: int,
    ejecutor_id: int,
    placa: str,
    tipo_nombre: str,
    marca_nombre: str,
    modelo_nombre: str,
    anio: int,
    color: str,
) -> int | None:
    ex = (await db.execute(select(Vehiculo).where(Vehiculo.placa == placa))).scalar_one_or_none()
    if ex is not None:
        return ex.id
    ids = await _ids_catalogo_alt(db, tipo_nombre=tipo_nombre, marca_nombre=marca_nombre, modelo_nombre=modelo_nombre)
    if ids is None:
        ids = await _ids_catalogo(db)
    if ids is None:
        logger.error("Demo SC: catálogo vehículo incompleto.")
        return None
    tipo_id, marca_id, modelo_id = ids
    v = await vehiculos_service.create_vehiculo(
        {
            "cliente_id": cliente_id,
            "placa": placa,
            "marca_id": marca_id,
            "modelo_id": modelo_id,
            "tipo_vehiculo_id": tipo_id,
            "anio": anio,
            "color": color,
        },
        db,
        ejecutor_id=ejecutor_id,
    )
    return v.id


async def ensure_demo_vehiculos_santa_cruz(db: AsyncSession) -> None:
    """4 placas demo (único nacional); contexto Santa Cruz."""
    email_c = (settings.SEED_CLIENTE_EMAIL or "").strip().lower()
    if not email_c:
        return
    uc = (await db.execute(select(Usuario).where(Usuario.email == email_c))).scalar_one_or_none()
    if uc is None:
        return
    cliente = (await db.execute(select(Cliente).where(Cliente.usuario_id == uc.id))).scalar_one_or_none()
    if cliente is None:
        return
    flota = [
        ("3482RSC", "Sedán", "Toyota", "Corolla", 2019, "Plata — garaje Equipetrol"),
        ("9012LSC", "Sedán", "Chevrolet", "Sail", 2017, "Blanco — Urbarí"),
        ("4410MSC", "Hatchback", "Suzuki", "Swift", 2021, "Rojo — 2do anillo"),
        ("7721KSC", "Pickup", "Toyota", "Hilux", 2020, "Gris — doble vía La Guardia"),
    ]
    for placa, tipo, marca, modelo, anio, color in flota:
        vid = await _ensure_vehiculo_placa(
            db,
            cliente_id=cliente.id,
            ejecutor_id=uc.id,
            placa=placa,
            tipo_nombre=tipo,
            marca_nombre=marca,
            modelo_nombre=modelo,
            anio=anio,
            color=color,
        )
        if vid:
            logger.info("Demo SC: vehículo %s id=%s", placa, vid)


def _desc(linea: str) -> str:
    return f"{DEMO_MARKER} {linea}"


async def _add_bandeja_manual(
    db: AsyncSession,
    *,
    solicitud_id: int,
    taller_id: int,
    estado: EstadoBandejaTallerEnum,
    creado_at: datetime,
    respondido_at: datetime | None,
    motivo: str | None,
) -> None:
    db.add(
        SolicitudTallerBandeja(
            solicitud_id=solicitud_id,
            taller_id=taller_id,
            estado=estado,
            motivo_rechazo=motivo,
            creado_at=creado_at,
            respondido_at=respondido_at,
        )
    )
    await db.flush()


async def _hist(
    db: AsyncSession,
    *,
    solicitud_id: int,
    ant: EstadoSolicitudSeguimientoEnum | None,
    nuevo: EstadoSolicitudSeguimientoEnum,
    when: datetime,
    usuario_id: int | None,
    obs: str | None,
) -> None:
    await em_repo.insert_historial_estado(
        db,
        solicitud_id=solicitud_id,
        estado_anterior=ant,
        estado_nuevo=nuevo,
        usuario_id=usuario_id,
        observacion=obs,
        created_at=when,
    )


async def _pago_y_comision(
    db: AsyncSession,
    *,
    solicitud_id: int,
    cliente_id: int,
    taller_id: int,
    monto: Decimal,
    when: datetime,
) -> None:
    pct = Decimal("10.00")
    com = (monto * Decimal("0.10")).quantize(Decimal("0.01"))
    neto = (monto - com).quantize(Decimal("0.01"))
    p = Pago(
        solicitud_id=solicitud_id,
        cliente_id=cliente_id,
        monto=monto,
        moneda="BOB",
        metodo=MetodoPagoEnum.QR,
        estado=EstadoPagoEnum.PAGADO,
        referencia_externa=f"DEMO-SC-{solicitud_id}",
        proveedor="SIMULADO",
        metadata_json={"seed": "demo_santa_cruz"},
        created_at=when,
        pagado_at=when,
    )
    db.add(p)
    await db.flush()
    db.add(
        ComisionTaller(
            solicitud_id=solicitud_id,
            taller_id=taller_id,
            pago_id=p.id,
            porcentaje_plataforma=pct,
            monto_servicio=monto,
            monto_comision=com,
            monto_taller_neto=neto,
            estado=EstadoComisionTallerEnum.CALCULADA,
            calculado_at=when,
            liquidado_at=None,
        )
    )
    await db.flush()


async def ensure_demo_santa_cruz_datos(
    db: AsyncSession,
    *,
    require_enabled_flag: bool = True,
) -> None:
    """
    Solicitudes variadas (bandeja, estados, pagos) + vehículos demo Santa Cruz.
    Idempotente: si ya hay >= 10 solicitudes [DEMO-SC] para el cliente seed, no duplica.
    """
    if require_enabled_flag and not settings.SEED_DEMO_SANTA_CRUZ_ON_START:
        return

    await ensure_demo_vehiculos_santa_cruz(db)

    ctx = await _ctx_demo(db)
    if ctx is None:
        return
    cliente_id, taller_id, tecnico_id, uid_cliente, uid_resp, vids = ctx
    if tecnico_id == 0:
        logger.warning("Demo SC: omitido bloque solicitudes (falta técnico seed).")
        return

    if await _count_demo_solicitudes(db, cliente_id=cliente_id) >= 10:
        logger.info("Demo SC: solicitudes demo ya existen (>=10), se omite inserción.")
        return

    now = utc_now_naive()
    v0, v1, v2, v3 = vids[0], vids[min(1, len(vids) - 1)], vids[min(2, len(vids) - 1)], vids[min(3, len(vids) - 1)]

    # --- 1) Bandeja pendiente, solicitud recién creada ---
    t1 = now - timedelta(days=2)
    s1 = await em_repo.insert_solicitud(
        db,
        cliente_id=cliente_id,
        vehiculo_id=v0,
        descripcion_texto=_desc(
            "Llanta baja cerca del Cristo Redentor (urbe). Necesito auxilio vial en Santa Cruz."
        ),
        estado=EstadoSolicitudSeguimientoEnum.REGISTRADA,
        created_at=t1,
        updated_at=t1,
    )
    await _hist(db, solicitud_id=s1.id, ant=None, nuevo=EstadoSolicitudSeguimientoEnum.REGISTRADA, when=t1, usuario_id=uid_cliente, obs="Alta desde app (demo).")
    await pt_repo.insert_bandeja_pendiente_por_cada_taller(db, solicitud_id=s1.id, creado_at=t1)
    await em_repo.insert_ubicacion(
        db,
        solicitud_id=s1.id,
        latitud=SC_LAT,
        longitud=SC_LON,
        precision_metros=Decimal("12"),
        direccion_referencia="Zona Sur, cerca del Cristo, Santa Cruz",
        es_actual=True,
        registrado_at=t1,
    )

    # --- 2) Taller rechazó en bandeja (sigue sin asignación) ---
    t2 = now - timedelta(days=5)
    s2 = await em_repo.insert_solicitud(
        db,
        cliente_id=cliente_id,
        vehiculo_id=v1,
        descripcion_texto=_desc("Batería descargada en Av. Monseñor Rivero, equipetrol. Sin arranque."),
        estado=EstadoSolicitudSeguimientoEnum.REGISTRADA,
        created_at=t2,
        updated_at=t2,
    )
    await _hist(db, solicitud_id=s2.id, ant=None, nuevo=EstadoSolicitudSeguimientoEnum.REGISTRADA, when=t2, usuario_id=uid_cliente, obs=None)
    await pt_repo.insert_bandeja_pendiente_por_cada_taller(db, solicitud_id=s2.id, creado_at=t2)
    b2 = (
        await db.execute(
            select(SolicitudTallerBandeja).where(
                SolicitudTallerBandeja.solicitud_id == s2.id,
                SolicitudTallerBandeja.taller_id == taller_id,
            )
        )
    ).scalar_one_or_none()
    if b2:
        b2.estado = EstadoBandejaTallerEnum.RECHAZADA
        b2.motivo_rechazo = "Cupos llenos en turno noche — reintentar mañana (demo seed)."
        b2.respondido_at = t2 + timedelta(hours=1)

    # --- 3) Taller asignado, bandeja aceptada ---
    t3 = now - timedelta(days=8)
    s3 = await em_repo.insert_solicitud(
        db,
        cliente_id=cliente_id,
        vehiculo_id=v2,
        descripcion_texto=_desc("Choque leve en 3er anillo interno; abolladura puerta delantera."),
        estado=EstadoSolicitudSeguimientoEnum.TALLER_ASIGNADO,
        created_at=t3,
        updated_at=t3,
    )
    s3.taller_id = taller_id
    await _hist(db, solicitud_id=s3.id, ant=None, nuevo=EstadoSolicitudSeguimientoEnum.REGISTRADA, when=t3, usuario_id=uid_cliente, obs=None)
    await _hist(
        db,
        solicitud_id=s3.id,
        ant=EstadoSolicitudSeguimientoEnum.REGISTRADA,
        nuevo=EstadoSolicitudSeguimientoEnum.TALLER_ASIGNADO,
        when=t3 + timedelta(minutes=20),
        usuario_id=uid_resp,
        obs="Taller Santa Cruz aceptó asistencia.",
    )
    await _add_bandeja_manual(
        db,
        solicitud_id=s3.id,
        taller_id=taller_id,
        estado=EstadoBandejaTallerEnum.ACEPTADA,
        creado_at=t3,
        respondido_at=t3 + timedelta(minutes=20),
        motivo=None,
    )

    # --- 4) Técnico asignado ---
    t4 = now - timedelta(days=11)
    s4 = await em_repo.insert_solicitud(
        db,
        cliente_id=cliente_id,
        vehiculo_id=v3,
        descripcion_texto=_desc("Sobre calor en Perú y Paraguay (centro). Revisión en sitio."),
        estado=EstadoSolicitudSeguimientoEnum.TECNICO_ASIGNADO,
        created_at=t4,
        updated_at=t4,
    )
    s4.taller_id = taller_id
    s4.tecnico_id = tecnico_id
    s4.tecnico_asignado_at = t4 + timedelta(minutes=30)
    await _hist(db, solicitud_id=s4.id, ant=None, nuevo=EstadoSolicitudSeguimientoEnum.REGISTRADA, when=t4, usuario_id=uid_cliente, obs=None)
    await _hist(db, solicitud_id=s4.id, ant=EstadoSolicitudSeguimientoEnum.REGISTRADA, nuevo=EstadoSolicitudSeguimientoEnum.TALLER_ASIGNADO, when=t4 + timedelta(minutes=15), usuario_id=uid_resp, obs=None)
    await _hist(
        db,
        solicitud_id=s4.id,
        ant=EstadoSolicitudSeguimientoEnum.TALLER_ASIGNADO,
        nuevo=EstadoSolicitudSeguimientoEnum.TECNICO_ASIGNADO,
        when=t4 + timedelta(minutes=30),
        usuario_id=uid_resp,
        obs=f"Asignación técnica ({settings.SEED_TALLER_NOMBRE_COMERCIAL}).",
    )
    await _add_bandeja_manual(db, solicitud_id=s4.id, taller_id=taller_id, estado=EstadoBandejaTallerEnum.ACEPTADA, creado_at=t4, respondido_at=t4 + timedelta(minutes=15), motivo=None)
    await pt_repo.insert_asignacion_tecnico(
        db,
        solicitud_id=s4.id,
        taller_id=taller_id,
        tecnico_id=tecnico_id,
        estado=EstadoAsignacionTecnicoEnum.ASIGNADO,
        asignado_por_usuario_id=uid_resp,
        observacion="Técnico de guardia — Santa Cruz.",
        created_at=t4 + timedelta(minutes=30),
    )

    # --- 5) En camino + ETA ---
    t5 = now - timedelta(days=14)
    s5 = await em_repo.insert_solicitud(
        db,
        cliente_id=cliente_id,
        vehiculo_id=v0,
        descripcion_texto=_desc("Pinchazo en doble vía La Guardia, sentido Warnes. Rueda de repuesto ok."),
        estado=EstadoSolicitudSeguimientoEnum.EN_CAMINO,
        created_at=t5,
        updated_at=t5,
    )
    s5.taller_id = taller_id
    s5.tecnico_id = tecnico_id
    s5.tecnico_asignado_at = t5 + timedelta(minutes=10)
    s5.tiempo_estimado_min = 25
    await _hist(db, solicitud_id=s5.id, ant=None, nuevo=EstadoSolicitudSeguimientoEnum.REGISTRADA, when=t5, usuario_id=uid_cliente, obs=None)
    await _hist(db, solicitud_id=s5.id, ant=EstadoSolicitudSeguimientoEnum.REGISTRADA, nuevo=EstadoSolicitudSeguimientoEnum.TALLER_ASIGNADO, when=t5 + timedelta(minutes=8), usuario_id=uid_resp, obs=None)
    await _hist(db, solicitud_id=s5.id, ant=EstadoSolicitudSeguimientoEnum.TALLER_ASIGNADO, nuevo=EstadoSolicitudSeguimientoEnum.TECNICO_ASIGNADO, when=t5 + timedelta(minutes=10), usuario_id=uid_resp, obs=None)
    await _hist(db, solicitud_id=s5.id, ant=EstadoSolicitudSeguimientoEnum.TECNICO_ASIGNADO, nuevo=EstadoSolicitudSeguimientoEnum.EN_CAMINO, when=t5 + timedelta(minutes=25), usuario_id=uid_resp, obs="Salida desde taller zona norte SC.")
    await _add_bandeja_manual(db, solicitud_id=s5.id, taller_id=taller_id, estado=EstadoBandejaTallerEnum.ACEPTADA, creado_at=t5, respondido_at=t5 + timedelta(minutes=8), motivo=None)
    await pt_repo.insert_asignacion_tecnico(
        db,
        solicitud_id=s5.id,
        taller_id=taller_id,
        tecnico_id=tecnico_id,
        estado=EstadoAsignacionTecnicoEnum.ASIGNADO,
        asignado_por_usuario_id=uid_resp,
        observacion=None,
        created_at=t5 + timedelta(minutes=10),
    )

    # --- 6) En atención + presupuesto ---
    t6 = now - timedelta(days=18)
    s6 = await em_repo.insert_solicitud(
        db,
        cliente_id=cliente_id,
        vehiculo_id=v1,
        descripcion_texto=_desc("Falla eléctrica: luces tablero intermitentes. Barrio Urbarí."),
        estado=EstadoSolicitudSeguimientoEnum.EN_ATENCION,
        created_at=t6,
        updated_at=t6,
    )
    s6.taller_id = taller_id
    s6.tecnico_id = tecnico_id
    s6.tecnico_asignado_at = t6 + timedelta(minutes=12)
    s6.tiempo_estimado_min = 40
    s6.presupuesto_bob = Decimal("680.00")
    s6.presupuesto_registrado_at = t6 + timedelta(hours=1)
    await _hist(db, solicitud_id=s6.id, ant=None, nuevo=EstadoSolicitudSeguimientoEnum.REGISTRADA, when=t6, usuario_id=uid_cliente, obs=None)
    await _hist(db, solicitud_id=s6.id, ant=EstadoSolicitudSeguimientoEnum.REGISTRADA, nuevo=EstadoSolicitudSeguimientoEnum.TALLER_ASIGNADO, when=t6 + timedelta(minutes=10), usuario_id=uid_resp, obs=None)
    await _hist(db, solicitud_id=s6.id, ant=EstadoSolicitudSeguimientoEnum.TALLER_ASIGNADO, nuevo=EstadoSolicitudSeguimientoEnum.TECNICO_ASIGNADO, when=t6 + timedelta(minutes=12), usuario_id=uid_resp, obs=None)
    await _hist(db, solicitud_id=s6.id, ant=EstadoSolicitudSeguimientoEnum.TECNICO_ASIGNADO, nuevo=EstadoSolicitudSeguimientoEnum.EN_CAMINO, when=t6 + timedelta(minutes=30), usuario_id=uid_resp, obs=None)
    await _hist(db, solicitud_id=s6.id, ant=EstadoSolicitudSeguimientoEnum.EN_CAMINO, nuevo=EstadoSolicitudSeguimientoEnum.EN_ATENCION, when=t6 + timedelta(hours=1), usuario_id=uid_resp, obs="Presupuesto acordado en sitio (demo).")
    await _add_bandeja_manual(db, solicitud_id=s6.id, taller_id=taller_id, estado=EstadoBandejaTallerEnum.ACEPTADA, creado_at=t6, respondido_at=t6 + timedelta(minutes=10), motivo=None)
    await pt_repo.insert_asignacion_tecnico(
        db,
        solicitud_id=s6.id,
        taller_id=taller_id,
        tecnico_id=tecnico_id,
        estado=EstadoAsignacionTecnicoEnum.ASIGNADO,
        asignado_por_usuario_id=uid_resp,
        observacion=None,
        created_at=t6 + timedelta(minutes=12),
    )

    # --- 7) Finalizada + pago + comisión (890) ---
    t7 = now - timedelta(days=22)
    m7 = Decimal("890.00")
    s7 = await em_repo.insert_solicitud(
        db,
        cliente_id=cliente_id,
        vehiculo_id=v2,
        descripcion_texto=_desc("Cambio de aceite y revisión frenos — Av. San Martín, Santa Cruz."),
        estado=EstadoSolicitudSeguimientoEnum.FINALIZADA,
        created_at=t7,
        updated_at=t7,
    )
    s7.taller_id = taller_id
    s7.tecnico_id = tecnico_id
    s7.tecnico_asignado_at = t7 + timedelta(minutes=5)
    s7.presupuesto_bob = m7
    s7.presupuesto_registrado_at = t7 + timedelta(hours=2)
    s7.finalizada_at = t7 + timedelta(hours=4)
    await _hist(db, solicitud_id=s7.id, ant=None, nuevo=EstadoSolicitudSeguimientoEnum.REGISTRADA, when=t7, usuario_id=uid_cliente, obs=None)
    await _hist(db, solicitud_id=s7.id, ant=EstadoSolicitudSeguimientoEnum.REGISTRADA, nuevo=EstadoSolicitudSeguimientoEnum.TALLER_ASIGNADO, when=t7 + timedelta(minutes=4), usuario_id=uid_resp, obs=None)
    await _hist(db, solicitud_id=s7.id, ant=EstadoSolicitudSeguimientoEnum.TALLER_ASIGNADO, nuevo=EstadoSolicitudSeguimientoEnum.TECNICO_ASIGNADO, when=t7 + timedelta(minutes=5), usuario_id=uid_resp, obs=None)
    await _hist(db, solicitud_id=s7.id, ant=EstadoSolicitudSeguimientoEnum.TECNICO_ASIGNADO, nuevo=EstadoSolicitudSeguimientoEnum.EN_ATENCION, when=t7 + timedelta(hours=2), usuario_id=uid_resp, obs=None)
    await _hist(db, solicitud_id=s7.id, ant=EstadoSolicitudSeguimientoEnum.EN_ATENCION, nuevo=EstadoSolicitudSeguimientoEnum.FINALIZADA, when=t7 + timedelta(hours=4), usuario_id=uid_resp, obs="Servicio cerrado; cliente pagó QR (demo).")
    await _add_bandeja_manual(db, solicitud_id=s7.id, taller_id=taller_id, estado=EstadoBandejaTallerEnum.ACEPTADA, creado_at=t7, respondido_at=t7 + timedelta(minutes=4), motivo=None)
    a7a = await pt_repo.insert_asignacion_tecnico(
        db,
        solicitud_id=s7.id,
        taller_id=taller_id,
        tecnico_id=tecnico_id,
        estado=EstadoAsignacionTecnicoEnum.ASIGNADO,
        asignado_por_usuario_id=uid_resp,
        observacion="Primera asignación",
        created_at=t7 + timedelta(minutes=5),
    )
    a7a.estado = EstadoAsignacionTecnicoEnum.REASIGNADO
    await pt_repo.insert_asignacion_tecnico(
        db,
        solicitud_id=s7.id,
        taller_id=taller_id,
        tecnico_id=tecnico_id,
        estado=EstadoAsignacionTecnicoEnum.ASIGNADO,
        asignado_por_usuario_id=uid_resp,
        observacion="Reasignación confirmada (mismo técnico, demo historial).",
        created_at=t7 + timedelta(minutes=8),
    )
    await _pago_y_comision(db, solicitud_id=s7.id, cliente_id=cliente_id, taller_id=taller_id, monto=m7, when=t7 + timedelta(hours=3))

    # --- 8) Otra finalizada con monto distinto (reporte por técnico) ---
    t8 = now - timedelta(days=35)
    m8 = Decimal("1245.50")
    s8 = await em_repo.insert_solicitud(
        db,
        cliente_id=cliente_id,
        vehiculo_id=v3,
        descripcion_texto=_desc("Grúa liviana — traslado desde Urubó hasta taller zona norte."),
        estado=EstadoSolicitudSeguimientoEnum.FINALIZADA,
        created_at=t8,
        updated_at=t8,
    )
    s8.taller_id = taller_id
    s8.tecnico_id = tecnico_id
    s8.tecnico_asignado_at = t8 + timedelta(hours=1)
    s8.presupuesto_bob = m8
    s8.presupuesto_registrado_at = t8 + timedelta(hours=3)
    s8.finalizada_at = t8 + timedelta(hours=6)
    await _hist(db, solicitud_id=s8.id, ant=None, nuevo=EstadoSolicitudSeguimientoEnum.REGISTRADA, when=t8, usuario_id=uid_cliente, obs=None)
    await _hist(db, solicitud_id=s8.id, ant=EstadoSolicitudSeguimientoEnum.REGISTRADA, nuevo=EstadoSolicitudSeguimientoEnum.TALLER_ASIGNADO, when=t8 + timedelta(minutes=30), usuario_id=uid_resp, obs=None)
    await _hist(db, solicitud_id=s8.id, ant=EstadoSolicitudSeguimientoEnum.TALLER_ASIGNADO, nuevo=EstadoSolicitudSeguimientoEnum.TECNICO_ASIGNADO, when=t8 + timedelta(hours=1), usuario_id=uid_resp, obs=None)
    await _hist(db, solicitud_id=s8.id, ant=EstadoSolicitudSeguimientoEnum.TECNICO_ASIGNADO, nuevo=EstadoSolicitudSeguimientoEnum.FINALIZADA, when=t8 + timedelta(hours=6), usuario_id=uid_resp, obs="Traslado completado.")
    await _add_bandeja_manual(db, solicitud_id=s8.id, taller_id=taller_id, estado=EstadoBandejaTallerEnum.ACEPTADA, creado_at=t8, respondido_at=t8 + timedelta(minutes=30), motivo=None)
    await pt_repo.insert_asignacion_tecnico(
        db,
        solicitud_id=s8.id,
        taller_id=taller_id,
        tecnico_id=tecnico_id,
        estado=EstadoAsignacionTecnicoEnum.ASIGNADO,
        asignado_por_usuario_id=uid_resp,
        observacion=None,
        created_at=t8 + timedelta(hours=1),
    )
    await _pago_y_comision(db, solicitud_id=s8.id, cliente_id=cliente_id, taller_id=taller_id, monto=m8, when=t8 + timedelta(hours=5))

    # --- 9) Cancelada por cliente ---
    t9 = now - timedelta(days=40)
    s9 = await em_repo.insert_solicitud(
        db,
        cliente_id=cliente_id,
        vehiculo_id=v0,
        descripcion_texto=_desc("Pedido duplicado por error — cancelar asistencia."),
        estado=EstadoSolicitudSeguimientoEnum.CANCELADA,
        created_at=t9,
        updated_at=t9,
    )
    await _hist(db, solicitud_id=s9.id, ant=None, nuevo=EstadoSolicitudSeguimientoEnum.REGISTRADA, when=t9, usuario_id=uid_cliente, obs=None)
    await _hist(db, solicitud_id=s9.id, ant=EstadoSolicitudSeguimientoEnum.REGISTRADA, nuevo=EstadoSolicitudSeguimientoEnum.CANCELADA, when=t9 + timedelta(minutes=5), usuario_id=uid_cliente, obs="Cancelado por el cliente (demo).")
    await pt_repo.insert_bandeja_pendiente_por_cada_taller(db, solicitud_id=s9.id, creado_at=t9)
    b9 = (
        await db.execute(
            select(SolicitudTallerBandeja).where(
                SolicitudTallerBandeja.solicitud_id == s9.id,
                SolicitudTallerBandeja.taller_id == taller_id,
            )
        )
    ).scalar_one_or_none()
    if b9:
        b9.estado = EstadoBandejaTallerEnum.EXPIRADA
        b9.respondido_at = t9 + timedelta(minutes=5)

    # --- 10) Bandeja expirada sin cancelar solicitud (sigue registrada) ---
    t10 = now - timedelta(days=48)
    s10 = await em_repo.insert_solicitud(
        db,
        cliente_id=cliente_id,
        vehiculo_id=v1,
        descripcion_texto=_desc("Consulta preventiva motor — ya resolvió solo; sin taller."),
        estado=EstadoSolicitudSeguimientoEnum.REGISTRADA,
        created_at=t10,
        updated_at=t10,
    )
    await _hist(db, solicitud_id=s10.id, ant=None, nuevo=EstadoSolicitudSeguimientoEnum.REGISTRADA, when=t10, usuario_id=uid_cliente, obs=None)
    await pt_repo.insert_bandeja_pendiente_por_cada_taller(db, solicitud_id=s10.id, creado_at=t10)
    b10 = (
        await db.execute(
            select(SolicitudTallerBandeja).where(
                SolicitudTallerBandeja.solicitud_id == s10.id,
                SolicitudTallerBandeja.taller_id == taller_id,
            )
        )
    ).scalar_one_or_none()
    if b10:
        b10.estado = EstadoBandejaTallerEnum.EXPIRADA
        b10.respondido_at = t10 + timedelta(days=3)

    # Evidencia HTTPS dummy (una foto) en solicitud 1 — cumple validación URL
    await em_repo.insert_evidencia(
        db,
        solicitud_id=s1.id,
        tipo=TipoEvidenciaSolicitudEnum.FOTO,
        archivo_url="https://picsum.photos/seed/sc-santa-cruz-demo/800/600",
        mime_type="image/jpeg",
        nombre_archivo="llanta_cristo_demo.jpg",
        tamano_bytes=120_000,
        created_at=t1 + timedelta(minutes=3),
    )

    logger.info("Demo SC: insertadas 10 solicitudes demo + evidencia (marcador %s).", DEMO_MARKER)
