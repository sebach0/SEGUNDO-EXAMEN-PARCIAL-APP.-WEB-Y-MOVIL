# API portal taller — emergencias (ciclo 3 fase 1: bandeja + disponibilidad)
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.modules.incidentes.emergencias.models import EstadoSolicitudSeguimientoEnum
from app.modules.talleres_y_tecnicos.taller_responsable.router import require_taller_responsable
from app.modules.talleres_y_tecnicos.talleres.models import Taller
from app.modules.acceso_y_administracion.usuarios.models import Usuario

from . import service
from .schemas import (
    AsignacionTecnicoRead,
    AsignarTecnicoIn,
    AsignarTecnicoOut,
    BandejaIncidenteBaseRead,
    ComisionTallerRead,
    HistorialAtencionRead,
    RechazarBandejaIn,
    ReporteTallerDashboardRead,
    ResumenComisionesRead,
    SolicitudBandejaDetalleRead,
    TallerDisponibilidadRead,
    TallerDisponibilidadUpdateIn,
)

router = APIRouter(prefix="/app/taller/emergencias", tags=["Emergencias (taller)"])


@router.get(
    "/bandeja/disponibles",
    response_model=list[BandejaIncidenteBaseRead],
    dependencies=[Depends(require_permission("solicitudes_taller:leer"))],
)
async def listar_bandeja_disponibles(
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    """Solicitudes PENDIENTES en la bandeja del taller (vista operativa)."""
    _, taller = ctx
    return await service.listar_disponibles(taller.id, db)


@router.get(
    "/bandeja/{bandeja_id}",
    response_model=SolicitudBandejaDetalleRead,
    dependencies=[Depends(require_permission("solicitudes_taller:leer"))],
)
async def detalle_bandeja(
    bandeja_id: int,
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    """CU25 — información estructurada del incidente para una fila de bandeja."""
    _, taller = ctx
    return await service.obtener_detalle_bandeja(taller.id, bandeja_id, db)


@router.post(
    "/bandeja/{bandeja_id}/aceptar",
    response_model=SolicitudBandejaDetalleRead,
    dependencies=[Depends(require_permission("solicitudes_taller:aceptar"))],
)
async def aceptar_bandeja(
    bandeja_id: int,
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    """CU26 — aceptar asistencia; actualiza solicitud y expira otras bandejas pendientes."""
    user, taller = ctx
    return await service.aceptar_solicitud(user, taller.id, bandeja_id, db)


@router.post(
    "/bandeja/{bandeja_id}/rechazar",
    response_model=SolicitudBandejaDetalleRead,
    dependencies=[Depends(require_permission("solicitudes_taller:rechazar"))],
)
async def rechazar_bandeja(
    bandeja_id: int,
    body: RechazarBandejaIn,
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    """CU27 — rechazar con motivo."""
    user, taller = ctx
    return await service.rechazar_solicitud(user, taller.id, bandeja_id, body, db)


@router.get(
    "/disponibilidad",
    response_model=TallerDisponibilidadRead,
    dependencies=[Depends(require_permission("disponibilidad:gestionar"))],
)
async def get_disponibilidad(
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    """CU29 — lectura (crea fila por defecto si aún no existe)."""
    _, taller = ctx
    return await service.obtener_disponibilidad(taller.id, db)


@router.put(
    "/disponibilidad",
    response_model=TallerDisponibilidadRead,
    dependencies=[Depends(require_permission("disponibilidad:gestionar"))],
    status_code=status.HTTP_200_OK,
)
async def put_disponibilidad(
    body: TallerDisponibilidadUpdateIn,
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    """CU29 — actualizar banderas y capacidad declarada."""
    user, taller = ctx
    return await service.actualizar_disponibilidad(user, taller.id, body, db)


@router.post(
    "/solicitudes/{solicitud_id}/asignar-tecnico",
    response_model=AsignarTecnicoOut,
    dependencies=[Depends(require_permission("tecnicos:asignar"))],
)
async def asignar_tecnico(
    solicitud_id: int,
    body: AsignarTecnicoIn,
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    """CU28 — asignar o reasignar técnico del taller a la solicitud."""
    user, taller = ctx
    return await service.asignar_tecnico_a_solicitud(user, taller.id, solicitud_id, body, db)


@router.get(
    "/solicitudes/{solicitud_id}/asignaciones",
    response_model=list[AsignacionTecnicoRead],
    dependencies=[Depends(require_permission("solicitudes_taller:leer"))],
)
async def listar_asignaciones_tecnico(
    solicitud_id: int,
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    """Historial de asignaciones de técnico para la solicitud (mismo taller)."""
    _, taller = ctx
    return await service.listar_asignaciones_tecnico(taller.id, solicitud_id, db)


@router.get(
    "/historial-atenciones",
    response_model=list[HistorialAtencionRead],
    dependencies=[Depends(require_permission("historial_atenciones:leer"))],
)
async def historial_atenciones(
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
    estado: EstadoSolicitudSeguimientoEnum | None = Query(None),
    desde: date | None = Query(None),
    hasta: date | None = Query(None),
    limit: int = Query(200, ge=1, le=500),
):
    """CU30 — solicitudes atendidas por este taller (filtros opcionales por fecha y estado)."""
    _, taller = ctx
    return await service.listar_historial_atenciones(
        taller.id, db, estado=estado, desde=desde, hasta=hasta, limit=limit
    )


@router.get(
    "/comisiones/resumen",
    response_model=ResumenComisionesRead,
    dependencies=[Depends(require_permission("comisiones:leer"))],
)
async def resumen_comisiones(
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    """CU31 — totales de comisiones del taller."""
    _, taller = ctx
    return await service.obtener_resumen_comisiones(taller.id, db)


@router.get(
    "/comisiones",
    response_model=list[ComisionTallerRead],
    dependencies=[Depends(require_permission("comisiones:leer"))],
)
async def listar_comisiones(
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    """CU31 — listado de comisiones con datos del pago asociado si existe."""
    _, taller = ctx
    return await service.listar_comisiones_taller(taller.id, db)


@router.get(
    "/reportes/dashboard",
    response_model=ReporteTallerDashboardRead,
    dependencies=[Depends(require_permission("comisiones:leer"))],
)
async def reporte_dashboard_taller(
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
    desde: date | None = Query(
        None,
        description="Inicio de periodo (inclusive). Comisiones: filtra por `calculado_at`. Solicitudes: por `created_at`.",
    ),
    hasta: date | None = Query(
        None,
        description="Fin de periodo (inclusive).",
    ),
):
    """
    Resumen operativo e inteligencia financiera: totales de comisiones, neto agregado por técnico,
    conteo de solicitudes por estado y ofertas pendientes en bandeja.
    """
    _, taller = ctx
    return await service.obtener_reporte_dashboard_taller(
        taller.id, db, desde=desde, hasta=hasta
    )
