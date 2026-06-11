from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.incidentes.emergencias.models import EstadoSolicitudSeguimientoEnum, TipoEvidenciaSolicitudEnum
from app.modules.pagos_y_comisiones.pagos.models import EstadoPagoEnum
from app.modules.atencion.taller_emergencias.models import (
    EstadoAsignacionTecnicoEnum,
    EstadoBandejaTallerEnum,
    EstadoComisionTallerEnum,
)


class BandejaIncidenteBaseRead(BaseModel):
    """Información estructurada del incidente (alineada a vw_solicitudes_disponibles_taller)."""

    model_config = ConfigDict(from_attributes=True)

    bandeja_id: int
    taller_id: int
    solicitud_id: int
    estado_solicitud: EstadoSolicitudSeguimientoEnum
    descripcion_texto: str | None
    created_at: datetime
    vehiculo_id: int
    placa: str
    marca: str | None
    modelo: str | None
    tipo_vehiculo: str | None
    cliente_id: int
    nombres: str
    apellidos: str
    latitud: Decimal | None
    longitud: Decimal | None
    direccion_referencia: str | None
    ai_payload: dict | None = Field(
        None,
        description="Pipeline IA (clasificación, prioridad, resumen) asociado a la solicitud.",
    )
    nivel_prioridad: str | None = Field(
        default=None,
        description="Nivel de prioridad sugerido (IA o reglas), p.ej. ALTA, MEDIA, BAJA, REVISION_MANUAL.",
    )


class SolicitudEvidenciaTallerRead(BaseModel):
    """Evidencia foto/audio asociada a la solicitud (lectura taller)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo: TipoEvidenciaSolicitudEnum
    archivo_url: str
    mime_type: str | None
    nombre_archivo: str | None
    created_at: datetime


class SolicitudBandejaDetalleRead(BandejaIncidenteBaseRead):
    estado_bandeja: EstadoBandejaTallerEnum
    motivo_rechazo: str | None
    creado_at: datetime
    respondido_at: datetime | None
    evidencias: list[SolicitudEvidenciaTallerRead] = Field(default_factory=list)


class TallerDisponibilidadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    taller_id: int
    acepta_nuevas_solicitudes: bool
    capacidad_maxima_diaria: int
    servicios_activos: int
    observacion: str | None
    updated_at: datetime
    updated_by_usuario_id: int | None


class TallerDisponibilidadUpdateIn(BaseModel):
    acepta_nuevas_solicitudes: bool | None = None
    capacidad_maxima_diaria: int | None = Field(default=None, ge=1, le=500)
    observacion: str | None = Field(default=None, max_length=2000)


class RechazarBandejaIn(BaseModel):
    motivo_rechazo: str = Field(min_length=3, max_length=2000)


class AsignarTecnicoIn(BaseModel):
    tecnico_id: int = Field(ge=1)
    observacion: str | None = Field(default=None, max_length=2000)
    tiempo_estimado_min: int | None = Field(
        default=None,
        ge=1,
        le=10080,
        description="Minutos estimados hasta la llegada del técnico (ETA). Opcional.",
    )


class AsignacionTecnicoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    solicitud_id: int
    taller_id: int
    tecnico_id: int
    estado: EstadoAsignacionTecnicoEnum
    asignado_por_usuario_id: int | None
    observacion: str | None
    created_at: datetime


class AsignarTecnicoOut(BaseModel):
    solicitud_id: int
    estado_solicitud: EstadoSolicitudSeguimientoEnum
    tecnico_id: int | None
    tecnico_asignado_at: datetime | None
    asignacion: AsignacionTecnicoRead


class HistorialAtencionRead(BaseModel):
    """CU30 — alineado a vw_historial_atenciones_taller (filtrado por taller en servicio)."""

    model_config = ConfigDict(from_attributes=True)

    solicitud_id: int
    bandeja_id: int | None = Field(
        default=None,
        description="Fila de bandeja del taller para esta solicitud (enlace al detalle CU25).",
    )
    taller_id: int | None
    tecnico_id: int | None
    estado: EstadoSolicitudSeguimientoEnum
    created_at: datetime
    finalizada_at: datetime | None
    nombres: str
    apellidos: str
    placa: str
    marca: str | None
    modelo: str | None
    tipo_vehiculo: str | None


class ItemDesgloseCotizacionRead(BaseModel):
    """Ítem de cotización aceptada para el desglose de comisión."""
    model_config = ConfigDict(from_attributes=True)
    descripcion: str
    cantidad: Decimal
    precio_unitario: Decimal
    subtotal: Decimal


class ComisionTallerRead(BaseModel):
    """CU31 — fila de comisiones_taller + datos opcionales del pago + desglose cotización."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    solicitud_id: int
    bandeja_id: int | None = Field(
        default=None,
        description="Bandeja del taller para abrir el detalle web (CU25).",
    )
    taller_id: int
    pago_id: int | None
    porcentaje_plataforma: Decimal
    monto_servicio: Decimal
    monto_comision: Decimal
    monto_taller_neto: Decimal
    estado: EstadoComisionTallerEnum
    calculado_at: datetime
    liquidado_at: datetime | None
    pago_monto: Decimal | None = None
    pago_estado: EstadoPagoEnum | None = None
    pago_pagado_at: datetime | None = None
    pago_moneda: str | None = None
    cotizacion_items: list[ItemDesgloseCotizacionRead] = Field(default_factory=list)


class ResumenComisionesRead(BaseModel):
    """CU31 — equivalente a vw_resumen_comisiones_taller por taller."""

    taller_id: int
    total_registros: int
    total_servicios: Decimal
    total_comision: Decimal
    total_neto: Decimal


class ReporteTecnicoGananciasRead(BaseModel):
    """Montos agregados por técnico (vía comisión vinculada a solicitud con `tecnico_id`)."""

    tecnico_id: int
    nombres: str
    apellidos: str
    comisiones_registradas: int
    total_monto_servicio: Decimal
    total_monto_comision: Decimal
    total_monto_taller_neto: Decimal


class ReporteTallerDashboardRead(BaseModel):
    """KPIs operativos y financieros del taller (periodo de comisiones por `calculado_at`)."""

    taller_id: int
    periodo_desde: date | None = Field(None, description="Fecha inicio inclusive (solicitud / comisiones).")
    periodo_hasta: date | None = Field(None, description="Fecha fin inclusive.")
    resumen_comisiones: ResumenComisionesRead
    bandeja_pendientes: int = Field(
        ...,
        description="Filas PENDIENTE en la bandeja de este taller (no filtrado por fechas).",
    )
    solicitudes_por_estado: dict[str, int] = Field(
        default_factory=dict,
        description="Conteo de solicitudes creadas en el periodo (por `created_at`) agrupado por estado.",
    )
    ganancias_por_tecnico: list[ReporteTecnicoGananciasRead] = Field(default_factory=list)
