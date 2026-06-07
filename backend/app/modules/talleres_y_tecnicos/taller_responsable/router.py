# API portal web taller — ciclo 1 (registro público + sesión responsable).
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import get_current_user_permisos
from app.modules.acceso_y_administracion.usuarios.models import Usuario
from app.modules.acceso_y_administracion.roles.models import Rol, UsuarioRol
from app.modules.talleres_y_tecnicos.talleres.models import Taller

from . import service
from app.modules.talleres_y_tecnicos.talleres import service as talleres_service
from app.modules.talleres_y_tecnicos.talleres.schemas import (
    ActualizarGruaIn,
    ActualizarServiciosTallerIn,
    ServicioCatalogoRead,
)

from app.modules.cotizaciones import service as cotizaciones_service
from app.modules.cotizaciones.schemas import (
    CotizacionContextoRead,
    CotizacionCreateIn,
    CotizacionRead,
)

from .schemas import (
    RegistroTallerIn,
    MiTallerRead,
    MiTallerUpdate,
    TecnicoPortalCreate,
    TecnicoPortalUpdate,
    TecnicoPortalRead,
    TallerDashboardRead,
)

router = APIRouter(prefix="/app/taller", tags=["App taller (responsable)"])


async def require_taller_responsable(
    data: tuple[Usuario, list[str]] = Depends(get_current_user_permisos),
    db: AsyncSession = Depends(get_db),
) -> tuple[Usuario, Taller]:
    user, _perms = data
    r = await db.execute(
        select(Rol.nombre)
        .join(UsuarioRol, UsuarioRol.rol_id == Rol.id)
        .where(UsuarioRol.usuario_id == user.id)
    )
    roles = {row[0] for row in r.fetchall()}
    if "TALLER_RESPONSABLE" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el responsable de taller puede usar el portal.",
        )
    t = await db.execute(select(Taller).where(Taller.usuario_responsable_id == user.id))
    taller = t.scalar_one_or_none()
    if not taller:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No hay taller asociado a tu cuenta.",
        )
    return user, taller


@router.post("/registro", response_model=MiTallerRead, status_code=status.HTTP_201_CREATED)
async def registro_taller(body: RegistroTallerIn, db: AsyncSession = Depends(get_db)):
    """Alta pública: usuario responsable + rol + taller pendiente de validación."""
    return await service.registro_taller_publico(body, db)


@router.get("/dashboard", response_model=TallerDashboardRead)
async def dashboard(
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    user, _ = ctx
    return await service.dashboard_taller(user.id, db)


@router.get("/mi-taller", response_model=MiTallerRead)
async def mi_taller(
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    user, _ = ctx
    return await service.get_mi_taller(user.id, db)


@router.put("/mi-taller", response_model=MiTallerRead)
async def actualizar_mi_taller(
    body: MiTallerUpdate,
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    user, _ = ctx
    return await service.update_mi_taller(user.id, body, db)


@router.get("/tecnicos", response_model=list[TecnicoPortalRead])
async def listar_tecnicos(
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    _, taller = ctx
    return await service.list_tecnicos_portal(taller.id, db)


@router.get("/tecnicos/{tecnico_id}", response_model=TecnicoPortalRead)
async def obtener_tecnico(
    tecnico_id: int,
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    _, taller = ctx
    return await service.get_tecnico_portal(tecnico_id, taller.id, db)


@router.post("/tecnicos", response_model=TecnicoPortalRead, status_code=status.HTTP_201_CREATED)
async def crear_tecnico(
    body: TecnicoPortalCreate,
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    user, taller = ctx
    return await service.create_tecnico_portal(taller.id, body, user.id, db)


@router.put("/tecnicos/{tecnico_id}", response_model=TecnicoPortalRead)
async def actualizar_tecnico(
    tecnico_id: int,
    body: TecnicoPortalUpdate,
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    user, taller = ctx
    return await service.update_tecnico_portal(tecnico_id, taller.id, body, user.id, db)


@router.get("/servicios", response_model=list[ServicioCatalogoRead])
async def listar_mis_servicios(
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    """Servicios que ofrece el taller del responsable autenticado."""
    _, taller = ctx
    return await talleres_service.get_servicios_taller(taller.id, db)


@router.put("/servicios", response_model=list[ServicioCatalogoRead])
async def actualizar_mis_servicios(
    body: ActualizarServiciosTallerIn,
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    """Actualiza el catálogo de servicios del taller autenticado (full-replace)."""
    user, taller = ctx
    return await talleres_service.actualizar_servicios_taller(
        taller.id, body.servicio_ids, db, user.id
    )


@router.patch("/grua", response_model=MiTallerRead)
async def actualizar_mi_grua(
    body: ActualizarGruaIn,
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    """Activa o desactiva el servicio de grúa del taller autenticado."""
    user, taller = ctx
    await talleres_service.actualizar_grua(taller.id, body.tiene_grua, db, user.id)
    return await service.get_mi_taller(user.id, db)


@router.get(
    "/cotizaciones/solicitudes/{solicitud_id}",
    response_model=list[CotizacionRead],
)
async def listar_cotizaciones_solicitud(
    solicitud_id: int,
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    """Cotizaciones de una solicitud (portal taller; usa token /app/taller)."""
    _ = ctx
    return await cotizaciones_service.listar_cotizaciones(solicitud_id=solicitud_id, db=db)


@router.get(
    "/cotizaciones/solicitudes/{solicitud_id}/contexto-oferta",
    response_model=CotizacionContextoRead,
)
async def contexto_oferta_cotizacion(
    solicitud_id: int,
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    """Distancia y servicios del taller autenticado para armar la oferta."""
    _, taller = ctx
    return await cotizaciones_service.contexto_oferta_taller(
        solicitud_id=solicitud_id,
        taller_id=taller.id,
        db=db,
    )


@router.post(
    "/cotizaciones/solicitudes/{solicitud_id}",
    response_model=CotizacionRead,
    status_code=status.HTTP_201_CREATED,
)
async def proponer_cotizacion_solicitud(
    solicitud_id: int,
    body: CotizacionCreateIn,
    ctx: tuple[Usuario, Taller] = Depends(require_taller_responsable),
    db: AsyncSession = Depends(get_db),
):
    """Envía cotización al marketplace para la solicitud indicada."""
    _, taller = ctx
    return await cotizaciones_service.proponer_cotizacion(
        solicitud_id=solicitud_id,
        taller_id=taller.id,
        body=body,
        db=db,
    )
