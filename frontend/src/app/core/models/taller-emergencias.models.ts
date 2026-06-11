/** Contratos alineados al módulo `taller_emergencias` (FastAPI). */

export type EstadoSolicitudSeguimiento =
  | 'REGISTRADA'
  | 'EN_REVISION'
  | 'TALLER_ASIGNADO'
  | 'TECNICO_ASIGNADO'
  | 'EN_CAMINO'
  | 'EN_ATENCION'
  | 'FINALIZADA'
  | 'CANCELADA';

export type EstadoBandejaTaller = 'PENDIENTE' | 'ACEPTADA' | 'RECHAZADA' | 'EXPIRADA';

export type TipoEvidenciaSolicitud = 'FOTO' | 'AUDIO';

export interface SolicitudEvidenciaTallerDto {
  id: number;
  tipo: TipoEvidenciaSolicitud;
  archivo_url: string;
  mime_type: string | null;
  nombre_archivo: string | null;
  created_at: string;
}

export interface BandejaIncidenteBaseDto {
  bandeja_id: number;
  taller_id: number;
  solicitud_id: number;
  estado_solicitud: EstadoSolicitudSeguimiento;
  descripcion_texto: string | null;
  created_at: string;
  vehiculo_id: number;
  placa: string;
  marca: string | null;
  modelo: string | null;
  tipo_vehiculo: string | null;
  cliente_id: number;
  nombres: string;
  apellidos: string;
  latitud: string | null;
  longitud: string | null;
  direccion_referencia: string | null;
  /** Nivel de prioridad sugerido (IA o reglas), p.ej. ALTA, MEDIA, BAJA. */
  nivel_prioridad?: string | null;
  /** Pipeline IA (post-crear solicitud): misma forma que almacena el backend. */
  ai_payload?: Record<string, unknown> | null;
}

export interface SolicitudBandejaDetalleDto extends BandejaIncidenteBaseDto {
  estado_bandeja: EstadoBandejaTaller;
  motivo_rechazo: string | null;
  creado_at: string;
  respondido_at: string | null;
  /** Fotos y audios adjuntos por el cliente. */
  evidencias?: SolicitudEvidenciaTallerDto[];
}

export interface TallerDisponibilidadDto {
  taller_id: number;
  acepta_nuevas_solicitudes: boolean;
  capacidad_maxima_diaria: number;
  servicios_activos: number;
  observacion: string | null;
  updated_at: string;
  updated_by_usuario_id: number | null;
}

export interface TallerDisponibilidadUpdatePayload {
  acepta_nuevas_solicitudes?: boolean;
  capacidad_maxima_diaria?: number;
  observacion?: string | null;
}

export interface RechazarBandejaPayload {
  motivo_rechazo: string;
}

/** POST `/app/taller/emergencias/solicitudes/{id}/asignar-tecnico` */
export interface AsignarTecnicoPayload {
  tecnico_id: number;
  observacion?: string | null;
  /** Minutos hasta llegada aproximada; el backend la guarda en la solicitud (ETA móvil). */
  tiempo_estimado_min?: number | null;
}

export type EstadoAsignacionTecnico = 'ASIGNADO' | 'REASIGNADO' | 'CANCELADO';

export interface AsignacionTecnicoDto {
  id: number;
  solicitud_id: number;
  taller_id: number;
  tecnico_id: number;
  estado: EstadoAsignacionTecnico;
  asignado_por_usuario_id: number | null;
  observacion: string | null;
  created_at: string;
}

export interface AsignarTecnicoResultDto {
  solicitud_id: number;
  estado_solicitud: EstadoSolicitudSeguimiento;
  tecnico_id: number | null;
  tecnico_asignado_at: string | null;
  asignacion: AsignacionTecnicoDto;
}

/** GET `/app/taller/emergencias/reportes/dashboard` */
export interface ResumenComisionesDto {
  taller_id: number;
  total_registros: number;
  total_servicios: string;
  total_comision: string;
  total_neto: string;
}

export interface ReporteTecnicoGananciasDto {
  tecnico_id: number;
  nombres: string;
  apellidos: string;
  comisiones_registradas: number;
  total_monto_servicio: string;
  total_monto_comision: string;
  total_monto_taller_neto: string;
}

export interface ReporteTallerDashboardDto {
  taller_id: number;
  periodo_desde: string | null;
  periodo_hasta: string | null;
  resumen_comisiones: ResumenComisionesDto;
  bandeja_pendientes: number;
  solicitudes_por_estado: Record<string, number>;
  ganancias_por_tecnico: ReporteTecnicoGananciasDto[];
}

/** GET `/app/taller/emergencias/historial-atenciones` */
export interface HistorialAtencionDto {
  solicitud_id: number;
  bandeja_id?: number | null;
  taller_id: number | null;
  tecnico_id: number | null;
  estado: EstadoSolicitudSeguimiento;
  created_at: string;
  finalizada_at: string | null;
  nombres: string;
  apellidos: string;
  placa: string;
  marca: string | null;
  modelo: string | null;
  tipo_vehiculo: string | null;
}

export type EstadoComisionTaller = 'PENDIENTE' | 'CALCULADA' | 'LIQUIDADA' | 'ANULADA';

export type EstadoPago = string;

export interface ItemDesgloseCotizacionDto {
  descripcion: string;
  cantidad: string;
  precio_unitario: string;
  subtotal: string;
}

/** GET `/app/taller/emergencias/comisiones` */
export interface ComisionTallerDto {
  id: number;
  solicitud_id: number;
  bandeja_id?: number | null;
  taller_id: number;
  pago_id: number | null;
  porcentaje_plataforma: string;
  monto_servicio: string;
  monto_comision: string;
  monto_taller_neto: string;
  estado: EstadoComisionTaller;
  calculado_at: string;
  liquidado_at: string | null;
  pago_monto: string | null;
  pago_estado: EstadoPago | null;
  pago_pagado_at: string | null;
  pago_moneda: string | null;
  cotizacion_items: ItemDesgloseCotizacionDto[];
}
