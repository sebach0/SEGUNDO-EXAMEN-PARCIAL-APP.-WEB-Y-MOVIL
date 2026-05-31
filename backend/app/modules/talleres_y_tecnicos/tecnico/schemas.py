from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.incidentes.emergencias.models import EstadoSolicitudSeguimientoEnum


class ServicioAsignadoRead(BaseModel):
    """Alineado a vw_servicios_asignados_tecnico (CU32)."""

    model_config = ConfigDict(from_attributes=True)

    solicitud_id: int
    tecnico_id: int
    taller_id: int | None
    estado: EstadoSolicitudSeguimientoEnum
    tiempo_estimado_min: int | None
    created_at: datetime
    updated_at: datetime
    cliente_id: int
    nombres: str
    apellidos: str
    telefono: str
    placa: str
    marca: str | None
    modelo: str | None
    tipo_vehiculo: str | None
    latitud: Decimal | None
    longitud: Decimal | None
    direccion_referencia: str | None
    categoria_incidente: str | None = None
    nivel_prioridad: str | None = None
    presupuesto_bob: Decimal | None = None
    presupuesto_registrado_at: datetime | None = None


class UbicacionClienteActualRead(BaseModel):
    """Ubicación actual del cliente (CU33)."""

    solicitud_id: int
    latitud: Decimal
    longitud: Decimal
    precision_metros: Decimal | None
    direccion_referencia: str | None
    registrado_at: datetime


class ActualizarEstadoServicioIn(BaseModel):
    nuevo_estado: EstadoSolicitudSeguimientoEnum
    observacion: str | None = Field(default=None, max_length=2000)
    presupuesto_bob: Decimal | None = Field(
        default=None,
        gt=0,
        description="Obligatorio al pasar a EN_ATENCION: monto cotizado en BOB.",
    )

    @model_validator(mode="after")
    def _presupuesto_si_en_atencion(self) -> "ActualizarEstadoServicioIn":
        if self.nuevo_estado == EstadoSolicitudSeguimientoEnum.EN_ATENCION:
            if self.presupuesto_bob is None:
                raise ValueError("presupuesto_bob es obligatorio al marcar EN_ATENCION (monto en BOB).")
            # Pydantic v2 en este entorno falla con max_digits/decimal_places en Field para Decimal.
            # Validamos formato monetario aquí: hasta 12 dígitos totales y 2 decimales.
            valor = self.presupuesto_bob.normalize()
            decimales = max(0, -valor.as_tuple().exponent)
            if decimales > 2:
                raise ValueError("presupuesto_bob debe tener como máximo 2 decimales.")
            digitos_totales = len(valor.as_tuple().digits)
            if digitos_totales > 12:
                raise ValueError("presupuesto_bob excede el máximo de 12 dígitos.")
        return self
