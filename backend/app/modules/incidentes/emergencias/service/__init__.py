# Servicio cliente emergencias: solicitudes, ubicaciones, evidencias (mismo contrato público).
from .evidencias import agregar_evidencia, agregar_evidencia_archivo
from .solicitudes import (
    actualizar_texto,
    cancelar_solicitud,
    crear_solicitud,
    listar_solicitudes,
    obtener_detalle,
    obtener_seguimiento,
    obtener_ubicacion_tecnico_compartida_cliente,
)
from .ubicaciones import agregar_ubicacion

__all__ = [
    "actualizar_texto",
    "agregar_evidencia",
    "agregar_evidencia_archivo",
    "agregar_ubicacion",
    "cancelar_solicitud",
    "crear_solicitud",
    "listar_solicitudes",
    "obtener_detalle",
    "obtener_seguimiento",
    "obtener_ubicacion_tecnico_compartida_cliente",
]
