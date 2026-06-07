# Schemas Pydantic — Tenants
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class TenantCreateIn(BaseModel):
    nombre: str = Field(..., max_length=150)
    slug: str = Field(..., max_length=80, pattern=r"^[a-z0-9\-]+$")
    estado: str = Field("ACTIVO")


class TenantRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    nombre: str
    slug: str
    estado: str
    creado_en: datetime
