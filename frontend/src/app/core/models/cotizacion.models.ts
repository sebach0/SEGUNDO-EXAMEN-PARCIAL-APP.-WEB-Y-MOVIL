/**
 * Modelos TypeScript para Cotizaciones — Ciclo 4 Segunda Fase.
 * Alineados con los schemas Pydantic del backend.
 */

export type EstadoCotizacion = 'ENVIADA' | 'ACEPTADA' | 'RECHAZADA' | 'EXPIRADA';

export const ESTADO_COTIZACION_LABELS: Record<EstadoCotizacion, string> = {
  ENVIADA:   'Enviada',
  ACEPTADA:  'Aceptada',
  RECHAZADA: 'Rechazada',
  EXPIRADA:  'Expirada',
};

export interface CotizacionItem {
  id: number;
  cotizacion_id: number;
  descripcion: string;
  cantidad: number;
  precio_unitario: number;
  subtotal: number;
}

export interface CotizacionItemIn {
  descripcion: string;
  cantidad: number;
  precio_unitario: number;
}

export interface ServicioOfrecido {
  id: number;
  nombre: string;
  codigo: string;
}

export interface CotizacionContexto {
  distancia_km: number | null;
  tarifa_traslado_bs_km: number;
  costo_traslado_estimado: number | null;
  servicios_disponibles: ServicioOfrecido[];
  tiene_grua: boolean;
  cotizacion_activa: boolean;
  taller_tiene_ubicacion: boolean;
  taller_lat: number | null;
  taller_lng: number | null;
  incidente_lat: number | null;
  incidente_lng: number | null;
  eta_sugerida_min: number | null;
}

export interface Cotizacion {
  id: number;
  solicitud_id: number;
  taller_id: number;
  taller_nombre: string | null;
  estado: EstadoCotizacion;
  descripcion_danio: string;
  detalle_servicio: string;
  monto_total: number;
  tiempo_estimado_llegada_min: number | null;
  tiempo_estimado_reparacion_min: number | null;
  incluye_grua: boolean;
  garantia_descripcion: string | null;
  comentarios: string | null;
  distancia_km: number | null;
  servicios_ofrecidos: ServicioOfrecido[];
  seleccionada_at: string | null;
  creado_at: string;
  actualizado_at: string;
  items: CotizacionItem[];
}

export interface CotizacionCreateIn {
  descripcion_danio: string;
  detalle_servicio: string;
  monto_total: number;
  tiempo_estimado_llegada_min?: number | null;
  tiempo_estimado_reparacion_min?: number | null;
  incluye_grua?: boolean;
  garantia_descripcion?: string | null;
  comentarios?: string | null;
  items?: CotizacionItemIn[];
}

// ── Catálogo de servicios ─────────────────────────────────────────────────────

export interface ServicioCatalogo {
  id: number;
  nombre: string;
  descripcion: string | null;
  codigo: string;
}

// ── KPIs ──────────────────────────────────────────────────────────────────────

export interface TallerEficiente {
  taller_id: number;
  nombre_comercial: string;
  tiempo_promedio_min: number;
  total_atendidos: number;
}

export interface ZonaIncidencia {
  zona: string;
  total: number;
}

export interface KpiSummary {
  tiempo_promedio_asignacion_min: number | null;
  tiempo_promedio_llegada_min: number | null;
  tiempo_promedio_atencion_min: number | null;
  incidentes_activos: number;
  incidentes_finalizados: number;
  incidentes_cancelados: number;
  cumplimiento_sla_pct: number | null;
  incidentes_por_tipo: Record<string, number>;
  zonas_con_mas_incidentes: ZonaIncidencia[];
  talleres_mas_eficientes: TallerEficiente[];
}
