# Schemas Pydantic — Tenants (Ciclo 5 CU43–CU44)
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

EstadoTenantLiteral = Literal["ACTIVO", "INACTIVO", "SUSPENDIDO"]
_ESTADOS_VALIDOS = frozenset({"ACTIVO", "INACTIVO", "SUSPENDIDO"})


class TenantCreateIn(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=150)
    slug: str = Field(..., min_length=1, max_length=80, pattern=r"^[a-z0-9\-]+$")
    estado: EstadoTenantLiteral = "ACTIVO"


class TenantUpdateIn(BaseModel):
    nombre: str | None = Field(None, min_length=1, max_length=150)
    slug: str | None = Field(None, min_length=1, max_length=80, pattern=r"^[a-z0-9\-]+$")
    estado: EstadoTenantLiteral | None = None

    @field_validator("nombre", "slug", mode="before")
    @classmethod
    def strip_optional(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s or None


class TenantRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    nombre: str
    slug: str
    estado: str
    creado_en: datetime
    actualizado_en: datetime | None = None


class TenantMemberUserRead(BaseModel):
    id: int
    nombres: str
    apellidos: str
    email: str
    username: str | None = None


class TenantMemberWorkshopRead(BaseModel):
    id: int
    nombre_comercial: str
    ciudad: str
    estado: str


class TenantMemberTechnicianRead(BaseModel):
    id: int
    usuario_id: int
    taller_id: int
    taller_nombre: str | None = None
    estado: str


class TenantMembersRead(BaseModel):
    tenant_id: int
    usuarios: list[TenantMemberUserRead]
    talleres: list[TenantMemberWorkshopRead]
    tecnicos: list[TenantMemberTechnicianRead]


class AssignIdsIn(BaseModel):
    ids: list[int] = Field(..., min_length=1)


class AssignTenantIn(BaseModel):
    tenant_id: int = Field(..., ge=1)


class AssignmentItemRead(BaseModel):
    id: int
    tipo: Literal["usuario", "taller", "tecnico"]
    tenant_id_anterior: int | None = None


class AssignmentResultOut(BaseModel):
    message: str = "Asignación completada"
    tenant_id: int
    assigned: list[AssignmentItemRead]
    skipped: list[int] = Field(default_factory=list)
