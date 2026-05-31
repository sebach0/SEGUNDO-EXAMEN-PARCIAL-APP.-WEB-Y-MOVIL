from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class TallerComisionFila(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    taller_id: int
    nombre_comercial: str
    n_comisiones: int
    total_monto_servicio: Decimal
    total_comision_plataforma: Decimal
    total_neto_taller: Decimal


class AdminFinanzasResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    porcentaje_plataforma: Decimal
    moneda: str
    desde: datetime | None
    hasta: datetime | None
    n_comisiones: int
    total_monto_servicio: Decimal
    total_comision_plataforma: Decimal
    total_neto_taller: Decimal
    n_pagos_pagados: int
    total_monto_pagos: Decimal
    n_solicitudes_finalizadas: int
    n_talleres_con_comision: int
    ticket_promedio_pagado: Decimal
    tasa_conversion_pago_pct: Decimal
    por_taller: list[TallerComisionFila]


class AdminComisionSerieFila(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    fecha: datetime
    n_comisiones: int
    total_monto_servicio: Decimal
    total_comision_plataforma: Decimal
    total_neto_taller: Decimal


class AdminFinanzasReportes(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    resumen: AdminFinanzasResumen
    top_talleres: list[TallerComisionFila]
    serie_diaria: list[AdminComisionSerieFila]

