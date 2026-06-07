/**
 * Modelos TypeScript para Ciclo #4
 * Alineados con los schemas Pydantic del backend FastAPI.
 */

// ── Estados del incidente ─────────────────────────────────────────────────────

export type IncidentStatus =
  | 'PENDIENTE'
  | 'BUSCANDO_TALLER'
  | 'TALLER_ASIGNADO'
  | 'EN_CAMINO'
  | 'EN_ATENCION'
  | 'FINALIZADO'
  | 'CANCELADO';

export const INCIDENT_STATUS_LABELS: Record<IncidentStatus, string> = {
  PENDIENTE: 'Pendiente',
  BUSCANDO_TALLER: 'Buscando taller',
  TALLER_ASIGNADO: 'Taller asignado',
  EN_CAMINO: 'En camino',
  EN_ATENCION: 'En atención',
  FINALIZADO: 'Finalizado',
  CANCELADO: 'Cancelado',
};

/** Orden lineal para la línea de progreso (excluye CANCELADO) */
export const INCIDENT_STATUS_STEPS: IncidentStatus[] = [
  'PENDIENTE',
  'BUSCANDO_TALLER',
  'TALLER_ASIGNADO',
  'EN_CAMINO',
  'EN_ATENCION',
  'FINALIZADO',
];

// ── Estados de sincronización offline ────────────────────────────────────────

export type SyncLocalStatus = 'pendiente' | 'enviado' | 'sincronizado' | 'error';

export const SYNC_STATUS_LABELS: Record<SyncLocalStatus, string> = {
  pendiente: 'Pendiente',
  enviado: 'Enviado',
  sincronizado: 'Sincronizado',
  error: 'Error',
};

// ── Tipos de origen del incidente ─────────────────────────────────────────────

export type OrigenIncidente = 'ONLINE' | 'OFFLINE';

// ── Incidente (Ciclo 4 — tabla incidentes, NO solicitudes_emergencia) ─────────

export interface Incident {
  id: number;
  tenant_id: number;
  cliente_id: number;
  vehiculo_id: number;
  tipo_incidente_id: number | null;
  zona_id: number | null;
  taller_asignado_id: number | null;
  descripcion: string | null;
  estado: IncidentStatus;
  prioridad: string;
  latitud: number | null;
  longitud: number | null;
  direccion_referencia: string | null;
  sla_minutos: number;
  origen: OrigenIncidente;
  client_uuid: string | null;
  sync_estado: SyncLocalStatus;
  reportado_en: string;
  buscando_taller_en: string | null;
  asignado_en: string | null;
  en_camino_en: string | null;
  en_atencion_en: string | null;
  finalizado_en: string | null;
  cancelado_en: string | null;
  motivo_cancelacion: string | null;
  creado_en: string;
  actualizado_en: string;
}

export interface IncidentDetalle extends Incident {
  historial_estados: HistorialEstadoItem[];
  tracking_reciente: TrackingPoint[];
  eventos_recientes: RealtimeEvent[];
}

// ── Historial de estado ───────────────────────────────────────────────────────

export interface HistorialEstadoItem {
  id: number;
  estado_anterior: string | null;
  estado_nuevo: string;
  usuario_id: number | null;
  comentario: string | null;
  creado_en: string;
}

// ── Tracking GPS ──────────────────────────────────────────────────────────────

export interface TrackingPoint {
  id: number;
  incidente_id: number;
  taller_id: number | null;
  tecnico_id: number | null;
  latitud: number;
  longitud: number;
  velocidad_kmh: number | null;
  registrado_en: string;
}

export interface TrackingPayload {
  latitud: number;
  longitud: number;
  velocidad_kmh?: number | null;
}

// ── Eventos WebSocket tiempo real ─────────────────────────────────────────────

export type RealtimeEventType =
  | 'ESTADO_CAMBIADO'
  | 'TRACKING_UPDATE'
  | 'TALLER_ACEPTO'
  | 'TALLER_RECHAZO'
  | 'AUXILIO_EN_CAMINO'
  | 'SERVICIO_ATENDIDO'
  | 'SERVICIO_FINALIZADO'
  | 'ETA_ACTUALIZADO'
  | 'SERVICIO_RETRASADO';

export interface RealtimeEvent {
  type: RealtimeEventType | string;
  incident_id: number;
  status: IncidentStatus | null;
  message: string | null;
  payload: Record<string, unknown>;
  emitted_at: string;
}

// ── Sincronización offline ────────────────────────────────────────────────────

export type WorkshopActionType =
  | 'ACEPTAR'
  | 'RECHAZAR'
  | 'CAMBIAR_ESTADO'
  | 'OBSERVACION';

export interface OfflineEvent {
  client_uuid: string;
  incidente_id: number;
  solicitud_id?: number;          // Flujo real (unificación Opción A)
  tipo_evento: string;            // ESTADO_CAMBIADO, TALLER_ACEPTO, etc.
  payload: Record<string, unknown>;
  registrado_local_en: string;    // ISO timestamp local
  // Metadatos locales (no se envían al backend)
  _estado_local: SyncLocalStatus;
  _intentos: number;
  _ultimo_error: string | null;
  _entidad: string;               // 'evento' | 'solicitud_evento'
}

export interface SyncResult {
  total: number;
  sincronizados: number;
  con_error: number;
  detalle: SyncResultItem[];
}

export interface SyncResultItem {
  client_uuid: string;
  incidente_id: number;
  tipo_evento: string;
  sincronizado: boolean;
  error: string | null;
}

export interface SyncStatusItem {
  id: number;
  entidad: string;
  client_uuid: string;
  estado_local: SyncLocalStatus;
  intentos: number;
  ultimo_error: string | null;
  incidente_id: number | null;
  registrado_local_en: string | null;
  sincronizado_en: string | null;
  creado_en: string;
}

// ── Payload para PATCH /incidents/{id}/status ─────────────────────────────────

export interface CambiarEstadoPayload {
  nuevo_estado: IncidentStatus;
  comentario?: string | null;
  motivo_cancelacion?: string | null;
}

// ── Payload para POST /sync/web/events ────────────────────────────────────────

export interface WebSyncPayload {
  eventos: WebEventoPayload[];
}

export interface WebEventoPayload {
  client_uuid: string;
  incidente_id: number;
  tipo_evento: string;
  payload: Record<string, unknown>;
  registrado_local_en?: string | null;
}

// ── Payload para POST /api/app/taller/emergencias/sync-web (flujo real) ───────

export interface SolicitudWebSyncPayload {
  eventos: SolicitudWebEventoPayload[];
}

export interface SolicitudWebEventoPayload {
  client_uuid: string;
  solicitud_id: number;
  tipo_evento: string;
  payload: Record<string, unknown>;
  registrado_local_en: string;
}

export interface SolicitudSyncResult {
  total: number;
  sincronizados: number;
  con_error: number;
  detalle: SolicitudSyncResultItem[];
}

export interface SolicitudSyncResultItem {
  client_uuid: string;
  solicitud_id: number;
  tipo_evento: string;
  sincronizado: boolean;
  error: string | null;
}

// ── KPIs (estructura base, sin datos hardcodeados) ────────────────────────────

export interface KpiSummary {
  tiempo_promedio_asignacion_min: number | null;
  tiempo_promedio_llegada_min: number | null;
  incidentes_activos: number | null;
  incidentes_finalizados: number | null;
  incidentes_cancelados: number | null;
  cumplimiento_sla_pct: number | null;
  incidentes_por_tipo: Record<string, number> | null;
  zonas_con_mas_incidentes: { zona: string; total: number }[] | null;
  talleres_mas_eficientes: { taller: string; tiempo_promedio_min: number }[] | null;
}
