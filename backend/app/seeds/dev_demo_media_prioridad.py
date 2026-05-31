# Seed idempotente: notificaciones in-app, chat por solicitud, ai_payload enriquecido,
# disponibilidad taller principal y segundo taller en Santa Cruz + bandeja demo multi-taller.
# Depende de cliente/taller/técnico y de solicitudes [DEMO-SC] (dev_demo_santa_cruz).
from __future__ import annotations

import logging
from datetime import timedelta
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.core.timeutil import utc_now_naive
from app.modules.comunicacion_y_notificaciones.mensajes_solicitud import repository as msg_repo
from app.modules.comunicacion_y_notificaciones.mensajes_solicitud.models import SolicitudMensaje
from app.modules.comunicacion_y_notificaciones.notificaciones import repository as notif_repo
from app.modules.comunicacion_y_notificaciones.notificaciones.models import Notificacion, TipoNotificacionEnum
from app.modules.acceso_y_administracion.roles.models import Rol
from app.modules.acceso_y_administracion.roles.service import asignar_roles_usuario
from app.modules.incidentes.emergencias import repository as em_repo
from app.modules.incidentes.emergencias.models import SolicitudEmergencia
from app.modules.atencion.taller_emergencias import repository as pt_repo
from app.modules.atencion.taller_emergencias.models import EstadoBandejaTallerEnum, SolicitudTallerBandeja
from app.modules.talleres_y_tecnicos.talleres import service as talleres_service
from app.modules.talleres_y_tecnicos.talleres.models import EstadoTallerEnum, Taller
from app.modules.acceso_y_administracion.usuarios import service as usuarios_service
from app.modules.acceso_y_administracion.usuarios.models import EstadoUsuarioEnum, Usuario
from app.seeds.dev_demo_santa_cruz import DEMO_MARKER, _ctx_demo
from app.seeds.identidades_demo_sc import TALLER_SECUNDARIO_LAT, TALLER_SECUNDARIO_LNG

logger = logging.getLogger(__name__)

DEMO_MEDIA_TAG = "[DEMO-MEDIA]"
GATE_TITULO = f"{DEMO_MEDIA_TAG} seed v1"


def _ai_payload_demo_variant(idx: int) -> dict:
    """JSON alineado a mobile `SolicitudAiPayloadV1` + backend IA (snake_case)."""
    bases = [
        (
            "LLANTA",
            "ALTA",
            "Cliente en 3er anillo (Santa Cruz) con llanta pinchada; riesgo de circular en caliente.",
        ),
        (
            "BATERIA",
            "MEDIA",
            "Batería descargada en zona Equipetrol; sin arranque pero sin riesgo inmediato.",
        ),
        (
            "CHOQUE",
            "REVISION_MANUAL",
            "Choque leve con posible daño estructural leve; conviene revisión presencial.",
        ),
    ]
    cat, nivel, resumen_line = bases[idx % len(bases)]
    return {
        "version": 1,
        "_seed_media": True,
        "clasificacion": {
            "categoria": cat,
            "confianza": 0.82 - (idx % 3) * 0.05,
            "fuentes": ["texto", "imagen"] if idx % 2 == 0 else ["texto"],
            "damages": [
                {
                    "label": cat,
                    "confidence": 0.78,
                    "severity": "MEDIA",
                    "reasons": ["Coincide con descripción del cliente", "Contexto vial Santa Cruz"],
                    "evidence_support": {"image": [], "audio": [], "text": []},
                    "conflict": {"has_conflict": False, "details": []},
                }
            ],
            "requires_manual_review": cat == "CHOQUE",
            "conflict_notes": [],
        },
        "prioridad": {
            "nivel_prioridad": nivel,
            "motivo": [
                "Incidente en vía urbana Santa Cruz de la Sierra",
                "Horario diurno, tráfico habitual en zona céntrica",
            ],
            "score": 0.71,
            "damages_considerados": [cat],
        },
        "resumen_estructurado": {
            "resumen": resumen_line,
            "ficha": {
                "tipo_problema": cat,
                "ubicacion_valida": True,
                "evidencia_audio": False,
                "evidencia_imagen": idx % 2 == 0,
                "incertidumbre": "BAJA",
            },
            "danos_detectados": [cat],
        },
        "transcripcion_audio": "Estoy parado en la doble vía, manden auxilio por favor."
        if idx % 2 == 0
        else None,
        "hallazgos_vision": ["Vehículo visible en carril", "Sin humo aparente a simple vista"]
        if idx % 2 == 0
        else [],
        "sugerencia_asignacion": {
            "candidatos": [],
            "mejor_taller_id": None,
        },
    }


async def _rol_taller_responsable_id(db: AsyncSession) -> int | None:
    r = await db.execute(select(Rol.id).where(Rol.nombre == "TALLER_RESPONSABLE"))
    row = r.scalar_one_or_none()
    if row is None:
        logger.error("Demo media: no existe rol TALLER_RESPONSABLE.")
        return None
    return int(row)


async def _gate_aplicado(db: AsyncSession, *, usuario_cliente_id: int) -> bool:
    r2 = await db.execute(
        select(func.count(Notificacion.id)).where(
            Notificacion.usuario_id == usuario_cliente_id,
            Notificacion.titulo == GATE_TITULO,
        )
    )
    return int(r2.scalar_one() or 0) > 0


async def _ensure_taller_competidor_sc(
    db: AsyncSession,
    *,
    rol_id: int,
) -> int | None:
    email = (settings.SEED_TALLER2_EMAIL or "").strip().lower()
    password = settings.SEED_TALLER2_PASSWORD or ""
    telefono = (settings.SEED_TALLER2_TELEFONO or "").strip()
    if not email or not password or not telefono:
        logger.warning(
            "Demo media: omitido segundo taller (definen SEED_TALLER2_EMAIL, SEED_TALLER2_PASSWORD, SEED_TALLER2_TELEFONO)."
        )
        return None

    now = utc_now_naive()
    ur = await db.execute(select(Usuario).where(Usuario.email == email))
    user = ur.scalar_one_or_none()

    if user is None:
        u = await usuarios_service.create_usuario(
            {
                "nombres": settings.SEED_TALLER2_RESPONSABLE_NOMBRES,
                "apellidos": settings.SEED_TALLER2_RESPONSABLE_APELLIDOS,
                "email": email,
                "telefono": telefono,
                "password": password,
                "username": None,
                "estado": EstadoUsuarioEnum.ACTIVO,
            },
            db,
            ejecutor_id=None,
        )
        await asignar_roles_usuario(u.id, [rol_id], db)
        user = u
        logger.info("Demo media: usuario taller competidor creado (%s)", email)
    else:
        if not verify_password(password, user.password_hash):
            user.password_hash = hash_password(password)
            user.updated_at = now
        if user.estado != EstadoUsuarioEnum.ACTIVO:
            user.estado = EstadoUsuarioEnum.ACTIVO
            user.updated_at = now
        await asignar_roles_usuario(user.id, [rol_id], db)

    tr = await db.execute(select(Taller).where(Taller.usuario_responsable_id == user.id))
    taller = tr.scalar_one_or_none()
    if taller is None:
        async with db.begin_nested():
            try:
                taller = await talleres_service.create_taller(
                    {
                        "usuario_responsable_id": user.id,
                        "nombre_comercial": settings.SEED_TALLER2_NOMBRE_COMERCIAL,
                        "telefono_contacto": telefono,
                        "email_contacto": email,
                        "direccion": settings.SEED_TALLER2_DIRECCION,
                        "ciudad": settings.SEED_TALLER2_CIUDAD,
                        "latitud": TALLER_SECUNDARIO_LAT,
                        "longitud": TALLER_SECUNDARIO_LNG,
                        "descripcion": settings.SEED_TALLER2_DESCRIPCION,
                        "estado": EstadoTallerEnum.ACTIVO,
                    },
                    db,
                    ejecutor_id=user.id,
                )
            except IntegrityError:
                logger.warning("Demo media: carrera al crear taller competidor; se reconsulta.")
        tr2 = await db.execute(select(Taller).where(Taller.usuario_responsable_id == user.id))
        taller = tr2.scalar_one_or_none()
    if taller is None:
        logger.error("Demo media: no se pudo asegurar taller competidor para %s", email)
        return None

    taller.nombre_comercial = settings.SEED_TALLER2_NOMBRE_COMERCIAL
    taller.telefono_contacto = telefono
    taller.email_contacto = email
    taller.direccion = settings.SEED_TALLER2_DIRECCION
    taller.ciudad = settings.SEED_TALLER2_CIUDAD
    taller.latitud = TALLER_SECUNDARIO_LAT
    taller.longitud = TALLER_SECUNDARIO_LNG
    taller.descripcion = settings.SEED_TALLER2_DESCRIPCION
    taller.estado = EstadoTallerEnum.ACTIVO
    taller.updated_at = now
    await db.flush()

    disp = await pt_repo.get_disponibilidad(db, taller_id=taller.id)
    if disp is None:
        await pt_repo.insert_disponibilidad_default(db, taller_id=taller.id, updated_at=now)
        disp = await pt_repo.get_disponibilidad(db, taller_id=taller.id)
    if disp is not None:
        disp.acepta_nuevas_solicitudes = True
        disp.capacidad_maxima_diaria = 12
        disp.servicios_activos = 2
        disp.observacion = f"{DEMO_MEDIA_TAG} Turno extendido y grúa liviana disponibles (Santa Cruz)."
        disp.updated_at = now
        await db.flush()

    logger.info("Demo media: taller competidor id=%s (%s)", taller.id, taller.nombre_comercial)
    return taller.id


async def _backfill_bandeja_para_taller(
    db: AsyncSession,
    *,
    taller_id: int,
    creado_at,
) -> None:
    """Filas PENDIENTE en solicitudes [DEMO-SC] que aún no tengan bandeja para este taller."""
    ids_r = await db.execute(
        select(SolicitudEmergencia.id).where(SolicitudEmergencia.descripcion_texto.like(f"{DEMO_MARKER}%"))
    )
    sids = [int(x[0]) for x in ids_r.fetchall()]
    for sid in sids:
        ex = await db.execute(
            select(SolicitudTallerBandeja.id).where(
                SolicitudTallerBandeja.solicitud_id == sid,
                SolicitudTallerBandeja.taller_id == taller_id,
            )
        )
        if ex.scalar_one_or_none() is not None:
            continue
        db.add(
            SolicitudTallerBandeja(
                solicitud_id=sid,
                taller_id=taller_id,
                estado=EstadoBandejaTallerEnum.PENDIENTE,
                creado_at=creado_at,
            )
        )
    await db.flush()


async def _seed_disponibilidad_taller_principal(
    db: AsyncSession,
    *,
    taller_id: int,
    usuario_responsable_id: int,
) -> None:
    now = utc_now_naive()
    row = await pt_repo.get_disponibilidad(db, taller_id=taller_id)
    if row is None:
        row = await pt_repo.insert_disponibilidad_default(db, taller_id=taller_id, updated_at=now)
    if row.observacion and DEMO_MEDIA_TAG in (row.observacion or ""):
        return
    row.acepta_nuevas_solicitudes = True
    row.capacidad_maxima_diaria = 18
    row.servicios_activos = 3
    row.observacion = (
        f"{DEMO_MEDIA_TAG} Cupos ampliados esta semana en Santa Cruz. "
        "Atención 08:00–20:00; prioridad vía rápida y 3er anillo."
    )
    row.updated_by_usuario_id = usuario_responsable_id
    row.updated_at = now
    await db.flush()
    logger.info("Demo media: disponibilidad actualizada taller_id=%s", taller_id)


async def _seed_ai_payloads(db: AsyncSession) -> None:
    r = await db.execute(
        select(SolicitudEmergencia.id, SolicitudEmergencia.ai_payload)
        .where(SolicitudEmergencia.descripcion_texto.like(f"{DEMO_MARKER}%"))
        .order_by(SolicitudEmergencia.id)
        .limit(6)
    )
    rows = r.fetchall()
    now = utc_now_naive()
    for i, (sid, existing) in enumerate(rows):
        if isinstance(existing, dict) and existing.get("_seed_media") is True:
            continue
        await em_repo.update_solicitud_ai_payload(
            db,
            solicitud_id=int(sid),
            payload=_ai_payload_demo_variant(i),
            updated_at=now,
        )
    if rows:
        logger.info("Demo media: ai_payload enriquecido en hasta %s solicitudes [DEMO-SC].", len(rows))


async def _seed_notificaciones(
    db: AsyncSession,
    *,
    uid_cliente: int,
    uid_tecnico: int | None,
    solicitud_ids: list[int],
) -> None:
    now = utc_now_naive()
    sid0 = solicitud_ids[0] if solicitud_ids else None
    sid1 = solicitud_ids[1] if len(solicitud_ids) > 1 else sid0

    items: list[tuple[int, int | None, TipoNotificacionEnum, str, str]] = [
        (
            uid_cliente,
            sid0,
            TipoNotificacionEnum.SOLICITUD_CREADA,
            f"{DEMO_MEDIA_TAG} Solicitud registrada",
            "Tu pedido de auxilio quedó registrado en Santa Cruz. Te avisamos cuando haya novedades.",
        ),
        (
            uid_cliente,
            sid1,
            TipoNotificacionEnum.TALLER_ASIGNADO,
            f"{DEMO_MEDIA_TAG} Taller en camino",
            "Un taller de la zona aceptó tu caso y está coordinando la asistencia.",
        ),
        (
            uid_cliente,
            sid0,
            TipoNotificacionEnum.TECNICO_ASIGNADO,
            f"{DEMO_MEDIA_TAG} Técnico asignado",
            "Ya hay un técnico asignado; podés escribirle por el chat de la solicitud.",
        ),
        (
            uid_cliente,
            sid0,
            TipoNotificacionEnum.ESTADO_ACTUALIZADO,
            f"{DEMO_MEDIA_TAG} Estado actualizado",
            "Actualizamos el estado de tu emergencia en el seguimiento.",
        ),
        (
            uid_cliente,
            sid0,
            TipoNotificacionEnum.MENSAJE_NUEVO,
            f"{DEMO_MEDIA_TAG} Mensaje nuevo",
            "Tenés un mensaje nuevo en el chat de la solicitud.",
        ),
    ]
    if uid_tecnico:
        items.append(
            (
                uid_tecnico,
                sid0,
                TipoNotificacionEnum.MENSAJE_NUEVO,
                f"{DEMO_MEDIA_TAG} Cliente escribió",
                "El cliente te escribió en el chat de la solicitud.",
            )
        )

    for uid, sid, tipo, titulo, msg in items:
        await notif_repo.insert_notificacion(
            db,
            usuario_id=uid,
            solicitud_id=sid,
            tipo=tipo,
            titulo=titulo[:150],
            mensaje=msg,
            created_at=now - timedelta(minutes=5),
        )

    await notif_repo.insert_notificacion(
        db,
        usuario_id=uid_cliente,
        solicitud_id=sid0,
        tipo=TipoNotificacionEnum.SOLICITUD_CREADA,
        titulo=GATE_TITULO,
        mensaje="Marcador interno del entorno de prueba (no borrar): evita duplicar datos de media prioridad.",
        created_at=now - timedelta(minutes=1),
    )
    logger.info("Demo media: notificaciones in-app insertadas (cliente + técnico si aplica).")


async def _seed_mensajes(
    db: AsyncSession,
    *,
    solicitud_id: int,
    uid_cliente: int,
    uid_tecnico: int,
) -> None:
    chk = await db.execute(
        select(func.count())
        .select_from(SolicitudMensaje)
        .where(
            SolicitudMensaje.solicitud_id == solicitud_id,
            SolicitudMensaje.mensaje.like(f"%{DEMO_MEDIA_TAG}%"),
        )
    )
    if int(chk.scalar_one() or 0) > 0:
        return

    now = utc_now_naive()
    thread = [
        (
            uid_cliente,
            uid_tecnico,
            f"{DEMO_MEDIA_TAG} Hola, ¿me pueden decir más o menos en cuánto llegan? Estoy en doble vía hacia Warnes.",
        ),
        (
            uid_tecnico,
            uid_cliente,
            f"{DEMO_MEDIA_TAG} Buen día, ya salimos del taller. En unos 25 minutos estaríamos por ahí, según el tráfico del 3er anillo.",
        ),
        (
            uid_cliente,
            uid_tecnico,
            f"{DEMO_MEDIA_TAG} Listo, comparto ubicación en vivo desde la app.",
        ),
    ]
    for i, (emisor, receptor, texto) in enumerate(thread):
        await msg_repo.insert_mensaje(
            db,
            solicitud_id=solicitud_id,
            emisor_usuario_id=emisor,
            receptor_usuario_id=receptor,
            texto=texto,
            created_at=now - timedelta(minutes=28 - i * 6),
        )
    await db.flush()
    logger.info("Demo media: hilo de chat seed solicitud_id=%s", solicitud_id)


async def ensure_demo_media_prioridad(
    db: AsyncSession,
    *,
    require_enabled_flag: bool = True,
) -> None:
    """
    Enriquece datos demo: comunicaciones, IA JSON, disponibilidad, segundo taller + bandeja.
    Idempotente (marcador GATE en notificación del cliente).
    """
    if require_enabled_flag and not settings.SEED_DEMO_MEDIA_PRIORIDAD_ON_START:
        return

    ctx = await _ctx_demo(db)
    if ctx is None:
        logger.warning("Demo media: sin contexto demo (cliente/taller).")
        return
    cliente_id, taller_id, tecnico_id, uid_cliente, uid_resp, _vids = ctx
    if await _gate_aplicado(db, usuario_cliente_id=uid_cliente):
        logger.info("Demo media: ya aplicado (gate), se omite.")
        return

    demo_count = await db.execute(
        select(func.count())
        .select_from(SolicitudEmergencia)
        .where(
            SolicitudEmergencia.cliente_id == cliente_id,
            SolicitudEmergencia.descripcion_texto.like(f"{DEMO_MARKER}%"),
        )
    )
    if int(demo_count.scalar_one() or 0) < 1:
        logger.warning("Demo media: no hay solicitudes [DEMO-SC]; corré ensure_demo_santa_cruz_datos antes.")
        return

    rol_id = await _rol_taller_responsable_id(db)
    if rol_id is None:
        return

    taller2_id = await _ensure_taller_competidor_sc(db, rol_id=rol_id)
    now = utc_now_naive()
    if taller2_id is not None:
        await _backfill_bandeja_para_taller(db, taller_id=taller2_id, creado_at=now)

    await _seed_disponibilidad_taller_principal(
        db, taller_id=taller_id, usuario_responsable_id=uid_resp
    )
    await _seed_ai_payloads(db)

    sids_r = await db.execute(
        select(SolicitudEmergencia.id)
        .where(
            SolicitudEmergencia.cliente_id == cliente_id,
            SolicitudEmergencia.descripcion_texto.like(f"{DEMO_MARKER}%"),
        )
        .order_by(SolicitudEmergencia.id)
    )
    solicitud_ids = [int(x[0]) for x in sids_r.fetchall()]

    uid_tecnico: int | None = None
    if tecnico_id:
        uid_tecnico = await msg_repo.get_tecnico_usuario_id_for_solicitud(db, tecnico_row_id=tecnico_id)

    await _seed_notificaciones(
        db,
        uid_cliente=uid_cliente,
        uid_tecnico=uid_tecnico,
        solicitud_ids=solicitud_ids,
    )

    chat_sid_r = await db.execute(
        select(SolicitudEmergencia.id)
        .where(
            SolicitudEmergencia.descripcion_texto.like(f"{DEMO_MARKER}%"),
            SolicitudEmergencia.tecnico_id.isnot(None),
        )
        .order_by(SolicitudEmergencia.id)
        .limit(1)
    )
    chat_sid = chat_sid_r.scalar_one_or_none()
    if chat_sid is not None and uid_tecnico is not None:
        await _seed_mensajes(
            db,
            solicitud_id=int(chat_sid),
            uid_cliente=uid_cliente,
            uid_tecnico=uid_tecnico,
        )

    logger.info("Demo media prioridad: completado.")
