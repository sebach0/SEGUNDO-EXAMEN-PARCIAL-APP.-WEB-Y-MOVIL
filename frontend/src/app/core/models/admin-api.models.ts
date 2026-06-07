export type EstadoUsuario = 'ACTIVO' | 'INACTIVO' | 'BLOQUEADO' | 'PENDIENTE';
export type EstadoTaller = 'PENDIENTE' | 'ACTIVO' | 'SUSPENDIDO' | 'INACTIVO';
export type AccionBitacora =
  | 'CREAR'
  | 'ACTUALIZAR'
  | 'ELIMINAR'
  | 'INICIAR_SESION'
  | 'CERRAR_SESION'
  | 'RESTABLECER_CONTRASENA'
  | 'ASIGNAR_ROL'
  | 'ASIGNAR_PERMISO'
  | 'CONSULTAR';

export interface RolDto {
  id: number;
  nombre: string;
  descripcion: string | null;
  created_at: string | null;
}

export interface RolPermisosDto {
  rol_id: number;
  permiso_ids: number[];
}

export interface PermisoDto {
  id: number;
  codigo: string;
  nombre: string;
  modulo: string;
  descripcion: string | null;
}

export interface UsuarioListDto {
  id: number;
  nombres: string;
  apellidos: string;
  username: string | null;
  email: string;
  telefono: string;
  estado: EstadoUsuario;
  ultimo_acceso_at: string | null;
  created_at: string | null;
  /** Presente en listados y GET detalle; puede faltar en respuestas POST legacy. */
  roles?: string[];
}

export interface UsuarioCreatePayload {
  nombres: string;
  apellidos: string;
  email: string;
  telefono: string;
  password: string;
  username?: string | null;
  estado?: EstadoUsuario;
}

export interface UsuarioUpdatePayload {
  nombres?: string;
  apellidos?: string;
  telefono?: string;
  username?: string | null;
  estado?: EstadoUsuario;
}

export interface BitacoraDto {
  id: number;
  usuario_id: number | null;
  modulo: string;
  entidad: string;
  entidad_id: number | null;
  accion: AccionBitacora;
  descripcion: string | null;
  ip_address: string | null;
  created_at: string;
}

export interface TallerDto {
  id: number;
  usuario_responsable_id: number;
  nombre_comercial: string;
  telefono_contacto: string;
  email_contacto: string;
  direccion: string;
  ciudad: string;
  descripcion: string | null;
  estado: EstadoTaller;
  created_at: string | null;
}

export interface TallerCreatePayload {
  usuario_responsable_id: number;
  nombre_comercial: string;
  telefono_contacto: string;
  email_contacto: string;
  direccion: string;
  ciudad: string;
  descripcion?: string | null;
  estado?: EstadoTaller;
}

export interface TallerUpdatePayload {
  nombre_comercial?: string;
  telefono_contacto?: string;
  email_contacto?: string;
  direccion?: string;
  ciudad?: string;
  descripcion?: string | null;
  estado?: EstadoTaller;
}

/** Resumen financiero global (solo ADMIN) — decimales como string (JSON). */
export interface TallerComisionFila {
  taller_id: number;
  nombre_comercial: string;
  n_comisiones: number;
  total_monto_servicio: string;
  total_comision_plataforma: string;
  total_neto_taller: string;
}

export interface AdminFinanzasResumen {
  porcentaje_plataforma: string;
  moneda: string;
  desde: string | null;
  hasta: string | null;
  n_comisiones: number;
  total_monto_servicio: string;
  total_comision_plataforma: string;
  total_neto_taller: string;
  n_pagos_pagados: number;
  total_monto_pagos: string;
  n_solicitudes_finalizadas: number;
  n_talleres_con_comision: number;
  ticket_promedio_pagado: string;
  tasa_conversion_pago_pct: string;
  por_taller: TallerComisionFila[];
}

export interface AdminComisionSerieFila {
  fecha: string;
  n_comisiones: number;
  total_monto_servicio: string;
  total_comision_plataforma: string;
  total_neto_taller: string;
}

export interface AdminFinanzasReportes {
  resumen: AdminFinanzasResumen;
  top_talleres: TallerComisionFila[];
  serie_diaria: AdminComisionSerieFila[];
}

// ── Ciclo 5 — Tenants (CU43 / CU44) ─────────────────────────────────────────

export type EstadoTenant = 'ACTIVO' | 'INACTIVO' | 'SUSPENDIDO';

export interface TenantDto {
  id: number;
  nombre: string;
  slug: string;
  estado: EstadoTenant;
  creado_en: string;
  actualizado_en: string | null;
}

export interface TenantCreatePayload {
  nombre: string;
  slug: string;
  estado?: EstadoTenant;
}

export interface TenantUpdatePayload {
  nombre?: string;
  slug?: string;
  estado?: EstadoTenant;
}

export interface TenantMemberUsuario {
  id: number;
  nombres: string;
  apellidos: string;
  email: string;
  estado: EstadoUsuario;
}

export interface TenantMemberTaller {
  id: number;
  nombre_comercial: string;
  ciudad: string;
  estado: EstadoTaller;
}

export interface TenantMemberTecnico {
  id: number;
  usuario_id: number;
  taller_id: number;
  estado: string;
}

export interface TenantMembersDto {
  tenant_id: number;
  usuarios: TenantMemberUsuario[];
  talleres: TenantMemberTaller[];
  tecnicos: TenantMemberTecnico[];
}

export interface AssignmentResultDto {
  message: string;
  tenant_id: number | null;
  assigned: number[];
  skipped?: number[];
  errors?: string[];
}

// ── Ciclo 5 — KPI Dashboard (CU45) ──────────────────────────────────────────

export interface IncidentByTypeDto {
  tipo: string;
  total: number;
}

export interface TallerEficienteDto {
  taller_id: number;
  nombre_comercial: string;
  tiempo_promedio_min: number;
  total_atendidos: number;
}

export interface ZonaIncidenciaDto {
  zona: string;
  total: number;
}

export interface AdminDashboardKpisDto {
  tenant_id: number | null;
  total_incidents: number;
  average_assignment_minutes: number | null;
  average_arrival_minutes: number | null;
  average_total_minutes: number | null;
  active_incidents: number;
  completed_incidents: number;
  cancelled_cases: number;
  sla_compliance_percentage: number | null;
  incidents_by_type: IncidentByTypeDto[];
  incidents_by_zone: ZonaIncidenciaDto[];
  top_workshops: TallerEficienteDto[];
}

// ── Ciclo 5 — Reportes (CU46) ────────────────────────────────────────────────

export interface ReportTotalsDto {
  total: number;
  finalizados: number;
  cancelados: number;
  cumplimiento_sla_pct: number | null;
}

export interface IncidentReportRowDto {
  solicitud_id: number;
  cliente: string | null;
  vehiculo_placa: string | null;
  tipo_incidente: string | null;
  zona: string | null;
  taller: string | null;
  estado: string;
  reportado_en: string | null;
  asignado_en: string | null;
  en_atencion_en: string | null;
  finalizado_en: string | null;
  minutos_asignacion: number | null;
  minutos_llegada: number | null;
  cumple_sla: boolean | null;
  monto_pagado: number | null;
}

export interface IncidentReportReadDto {
  items: IncidentReportRowDto[];
  totals: ReportTotalsDto;
  message: string | null;
}

export interface PerformanceReportReadDto {
  promedio_asignacion_min: number | null;
  promedio_llegada_min: number | null;
  promedio_total_min: number | null;
  cumplimiento_sla_pct: number | null;
  total_incidentes: number;
  message: string | null;
}

export interface WorkshopReportRowDto {
  taller_id: number;
  nombre_comercial: string;
  total_servicios: number;
  finalizados: number;
  cancelados: number;
  promedio_asignacion_min: number | null;
  promedio_llegada_min: number | null;
  cumplimiento_sla_pct: number | null;
}

export interface WorkshopReportReadDto {
  items: WorkshopReportRowDto[];
  totals: ReportTotalsDto;
  message: string | null;
}

// ── Ciclo 5 — SLA (CU50) ─────────────────────────────────────────────────────

export interface WorkshopSlaDto {
  workshop_id: number;
  workshop_name: string;
  total_cases: number;
  completed_cases: number;
  cancelled_cases: number;
  average_assignment_minutes: number | null;
  average_arrival_minutes: number | null;
  sla_compliance_percentage: number | null;
  cases_out_of_sla: number;
}

export interface SlaCaseDetailDto {
  solicitud_id: number;
  reportado_en: string | null;
  finalizado_en: string | null;
  sla_minutos: number | null;
  minutos_totales: number;
  cumple_sla: boolean;
}

export interface WorkshopSlaDetailDto {
  workshop: WorkshopSlaDto;
  cases_out_of_sla: SlaCaseDetailDto[];
}
