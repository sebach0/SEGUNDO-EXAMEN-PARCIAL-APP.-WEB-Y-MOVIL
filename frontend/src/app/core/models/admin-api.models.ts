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
