export type EstadoTaller = 'PENDIENTE' | 'ACTIVO' | 'SUSPENDIDO' | 'INACTIVO';
export type EstadoTecnico = 'ACTIVO' | 'INACTIVO';

export interface RegistroTallerPayload {
  nombre_comercial: string;
  email: string;
  telefono: string;
  direccion: string;
  ciudad: string;
  descripcion?: string | null;
  responsable_nombre_completo: string;
  password: string;
}

export interface MiTallerDto {
  id: number;
  nombre_comercial: string;
  telefono_contacto: string;
  email_contacto: string;
  direccion: string;
  ciudad: string;
  descripcion: string | null;
  estado: EstadoTaller;
  created_at: string | null;
  responsable_nombres: string;
  responsable_apellidos: string;
  responsable_email: string;
  responsable_telefono: string;
  pendiente_verificacion_email?: boolean;
}

export interface MiTallerUpdatePayload {
  nombre_comercial?: string;
  telefono_contacto?: string;
  email_contacto?: string;
  direccion?: string;
  ciudad?: string;
  descripcion?: string | null;
  usuario?: {
    nombres?: string;
    apellidos?: string;
    telefono?: string;
  };
}

export interface TallerDashboardDto {
  tecnicos_registrados: number;
  tecnicos_activos: number;
  disponibilidad_general: string;
  taller_estado: EstadoTaller;
}

export interface EspecialidadDto {
  id: number;
  nombre: string;
  descripcion: string | null;
}

export interface TecnicoPortalDto {
  id: number;
  usuario_id: number;
  taller_id: number;
  nombres: string;
  apellidos: string;
  email: string;
  telefono: string;
  documento: string | null;
  especialidad_id: number | null;
  especialidad_nombre: string | null;
  disponibilidad: string | null;
  estado: EstadoTecnico;
  created_at: string | null;
  resumen_actividad: string | null;
}

export interface TecnicoPortalCreatePayload {
  nombre_completo: string;
  email: string;
  telefono: string;
  password: string;
  documento?: string | null;
  especialidad_id?: number | null;
  disponibilidad?: string | null;
  estado?: EstadoTecnico;
}

export interface TecnicoPortalUpdatePayload {
  nombre_completo?: string;
  email?: string;
  telefono?: string;
  documento?: string | null;
  especialidad_id?: number | null;
  disponibilidad?: string | null;
  estado?: EstadoTecnico;
}
