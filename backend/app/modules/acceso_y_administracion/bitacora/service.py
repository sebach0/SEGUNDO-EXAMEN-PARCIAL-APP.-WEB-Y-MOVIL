# app/modules/bitacora/service.py
# =========================================================
# Servicio de bitácora — función reutilizable para registrar acciones
# Importada por todos los módulos que necesiten auditoría
# =========================================================
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.timeutil import utc_now_naive
from app.modules.acceso_y_administracion.bitacora.models import Bitacora, AccionBitacoraEnum


async def registrar_accion(
    db: AsyncSession,
    modulo: str,
    entidad: str,
    accion: AccionBitacoraEnum,
    descripcion: str | None = None,
    usuario_id: int | None = None,
    entidad_id: int | None = None,
    ip_address: str | None = None,
) -> Bitacora:
    """
    Registra una acción en la bitácora de auditoría.
    
    Esta función es el punto único de escritura para la bitácora.
    Todos los módulos deben usarla AL FINAL de sus operaciones exitosas.
    
    Args:
        db: Sesión de base de datos activa
        modulo: Nombre del módulo (ej: "usuarios", "vehiculos")
        entidad: Nombre de la tabla/entidad afectada
        accion: Tipo de acción del ENUM
        descripcion: Texto libre describiendo qué pasó
        usuario_id: ID del usuario que ejecutó la acción (None si es sistema)
        entidad_id: ID del registro afectado
        ip_address: IP del cliente
    
    Returns:
        Instancia de Bitacora creada (sin commit, se hace en get_db)
    """
    registro = Bitacora(
        usuario_id=usuario_id,
        modulo=modulo,
        entidad=entidad,
        entidad_id=entidad_id,
        accion=accion,
        descripcion=descripcion,
        ip_address=ip_address,
        created_at=utc_now_naive(),
    )
    db.add(registro)
    # No se hace flush/commit aquí — se deja al patrón de get_db
    return registro
