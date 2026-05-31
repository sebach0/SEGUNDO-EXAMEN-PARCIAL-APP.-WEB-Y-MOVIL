# Schemas Pydantic — administración de clientes (API `/clientes` vía `usuarios.router`).
# Contratos app móvil: `schemas_movil.py`.
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ClienteCreate(BaseModel):
    usuario_id: int
    ciudad: Optional[str] = None
    direccion: Optional[str] = None


class ClienteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int
    ciudad: Optional[str]
    direccion: Optional[str]
    created_at: Optional[datetime]
