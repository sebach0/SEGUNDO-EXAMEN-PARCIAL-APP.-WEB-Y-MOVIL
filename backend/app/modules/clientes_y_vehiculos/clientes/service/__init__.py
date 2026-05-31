# Casos de uso cliente: acceso, registro/perfil, vehículos (app móvil).
from .acceso import get_cliente_row_for_usuario, require_cliente_rol
from .registro_perfil import (
    get_mi_perfil,
    mi_perfil_read,
    registro_cliente_publico,
    update_mi_perfil,
)
from .vehiculos_cliente import (
    actualizar_mi_vehiculo,
    crear_mi_vehiculo,
    get_mi_vehiculo,
    list_mis_vehiculos,
)

__all__ = [
    "actualizar_mi_vehiculo",
    "crear_mi_vehiculo",
    "get_cliente_row_for_usuario",
    "get_mi_perfil",
    "get_mi_vehiculo",
    "list_mis_vehiculos",
    "mi_perfil_read",
    "registro_cliente_publico",
    "require_cliente_rol",
    "update_mi_perfil",
]
