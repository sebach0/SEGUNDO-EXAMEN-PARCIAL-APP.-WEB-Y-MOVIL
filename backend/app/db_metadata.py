# ImportaciĂłn lateral: registra todas las tablas en Base.metadata (Alembic autogenerate).
# Orden: dependencias FK (Usuario antes que mĂłdulos que la referencian).
from app.modules.acceso_y_administracion.usuarios import models as _usuarios_models  # noqa: F401
from app.modules.clientes_y_vehiculos.clientes import models as _clientes_models  # noqa: F401
from app.modules.acceso_y_administracion.permisos import models as _permisos_models  # noqa: F401
from app.modules.acceso_y_administracion.roles import models as _roles_models  # noqa: F401
from app.modules.acceso_y_administracion.auth import models as _auth_models  # noqa: F401
from app.modules.talleres_y_tecnicos.talleres import models as _talleres_models  # noqa: F401
from app.modules.clientes_y_vehiculos.vehiculos import models as _vehiculos_models  # noqa: F401
from app.modules.acceso_y_administracion.bitacora import models as _bitacora_models  # noqa: F401
from app.modules.incidentes.emergencias import models as _emergencias_models  # noqa: F401
from app.modules.comunicacion_y_notificaciones.notificaciones import models as _notificaciones_models  # noqa: F401
from app.modules.comunicacion_y_notificaciones.mensajes_solicitud import models as _mensajes_solicitud_models  # noqa: F401
from app.modules.comunicacion_y_notificaciones.dispositivos_push import models as _dispositivos_push_models  # noqa: F401
from app.modules.pagos_y_comisiones.pagos import models as _pagos_models  # noqa: F401
# ── Ciclo 4 — orden: tenants primero (referenciado por el resto) ──────────────
from app.modules.ciclo4.tenants import models as _tenants_models          # noqa: F401
from app.modules.ciclo4.incidentes import models as _ciclo4_inc_models    # noqa: F401
from app.modules.ciclo4.sync import models as _ciclo4_sync_models         # noqa: F401
# ── Ciclo 4 Segunda Fase ───────────────────────────────────────────────────────
from app.modules.cotizaciones import models as _cotizaciones_models        # noqa: F401
