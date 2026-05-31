from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MensajeSolicitudCreateIn(BaseModel):
    mensaje: str = Field(..., min_length=1, max_length=4000)


class MensajeSolicitudRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    solicitud_id: int
    emisor_usuario_id: int
    receptor_usuario_id: int
    mensaje: str
    created_at: datetime
    leido_at: datetime | None
