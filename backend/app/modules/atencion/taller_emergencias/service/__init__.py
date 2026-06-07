# Paquete de servicio: bandeja, asignaciones técnicas, reportes (mismo contrato público que antes).
from .asignaciones import (
    asignar_tecnico_a_solicitud,
    asignar_tecnico_automatico,
    liberar_tecnico_si_sin_servicios,
    listar_asignaciones_tecnico,
)
from .bandeja import (
    aceptar_solicitud,
    actualizar_disponibilidad,
    listar_disponibles,
    obtener_detalle_bandeja,
    obtener_disponibilidad,
    rechazar_solicitud,
)
from .reportes import (
    listar_comisiones_taller,
    listar_historial_atenciones,
    obtener_reporte_dashboard_taller,
    obtener_resumen_comisiones,
)

__all__ = [
    "aceptar_solicitud",
    "actualizar_disponibilidad",
    "asignar_tecnico_a_solicitud",
    "asignar_tecnico_automatico",
    "liberar_tecnico_si_sin_servicios",
    "listar_asignaciones_tecnico",
    "listar_comisiones_taller",
    "listar_disponibles",
    "listar_historial_atenciones",
    "obtener_detalle_bandeja",
    "obtener_disponibilidad",
    "obtener_reporte_dashboard_taller",
    "obtener_resumen_comisiones",
    "rechazar_solicitud",
]
