import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import type {
  AccionBitacora,
  AdminFinanzasReportes,
  AdminFinanzasResumen,
  BitacoraDto,
  PermisoDto,
  RolDto,
  RolPermisosDto,
  TallerCreatePayload,
  TallerDto,
  TallerUpdatePayload,
  UsuarioCreatePayload,
  UsuarioListDto,
  UsuarioUpdatePayload,
} from '../models/admin-api.models';

@Injectable({ providedIn: 'root' })
export class AdminApiService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiUrl;

  listUsuarios(): Observable<UsuarioListDto[]> {
    return this.http.get<UsuarioListDto[]>(`${this.base}/usuarios/`);
  }

  getUsuario(id: number): Observable<UsuarioListDto> {
    return this.http.get<UsuarioListDto>(`${this.base}/usuarios/${id}`);
  }

  createUsuario(body: UsuarioCreatePayload): Observable<UsuarioListDto> {
    return this.http.post<UsuarioListDto>(`${this.base}/usuarios/`, body);
  }

  updateUsuario(id: number, body: UsuarioUpdatePayload): Observable<UsuarioListDto> {
    // Backend devuelve UsuarioRead; reinyectamos roles en el componente si hace falta.
    return this.http.put<UsuarioListDto>(`${this.base}/usuarios/${id}`, body);
  }

  deleteUsuario(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/usuarios/${id}`);
  }

  assignRoles(usuarioId: number, rolIds: number[]): Observable<void> {
    return this.http.put<void>(`${this.base}/usuarios/${usuarioId}/roles`, {
      rol_ids: rolIds,
    });
  }

  listRoles(): Observable<RolDto[]> {
    return this.http.get<RolDto[]>(`${this.base}/roles/`);
  }

  createRol(nombre: string, descripcion: string | null): Observable<RolDto> {
    return this.http.post<RolDto>(`${this.base}/roles/`, { nombre, descripcion });
  }

  getRolPermisoIds(rolId: number): Observable<RolPermisosDto> {
    return this.http.get<RolPermisosDto>(`${this.base}/roles/${rolId}/permisos`);
  }

  setRolPermisos(rolId: number, permisoIds: number[]): Observable<void> {
    return this.http.put<void>(`${this.base}/roles/${rolId}/permisos`, {
      permiso_ids: permisoIds,
    });
  }

  listPermisos(): Observable<PermisoDto[]> {
    return this.http.get<PermisoDto[]>(`${this.base}/permisos/`);
  }

  listBitacora(filters: {
    usuario_id?: number;
    modulo?: string;
    accion?: AccionBitacora;
    desde?: string;
    hasta?: string;
    limit?: number;
    offset?: number;
  }): Observable<BitacoraDto[]> {
    let params = new HttpParams();
    if (filters.usuario_id != null) {
      params = params.set('usuario_id', String(filters.usuario_id));
    }
    if (filters.modulo) params = params.set('modulo', filters.modulo);
    if (filters.accion) params = params.set('accion', filters.accion);
    if (filters.desde) params = params.set('desde', filters.desde);
    if (filters.hasta) params = params.set('hasta', filters.hasta);
    if (filters.limit != null) params = params.set('limit', String(filters.limit));
    if (filters.offset != null) params = params.set('offset', String(filters.offset));
    return this.http.get<BitacoraDto[]>(`${this.base}/bitacora/`, { params });
  }

  listTalleres(): Observable<TallerDto[]> {
    return this.http.get<TallerDto[]>(`${this.base}/talleres/`);
  }

  getTaller(id: number): Observable<TallerDto> {
    return this.http.get<TallerDto>(`${this.base}/talleres/${id}`);
  }

  createTaller(body: TallerCreatePayload): Observable<TallerDto> {
    return this.http.post<TallerDto>(`${this.base}/talleres/`, body);
  }

  updateTaller(id: number, body: TallerUpdatePayload): Observable<TallerDto> {
    return this.http.put<TallerDto>(`${this.base}/talleres/${id}`, body);
  }

  getFinanzasResumen(filters?: { desde?: string; hasta?: string }): Observable<AdminFinanzasResumen> {
    let params = new HttpParams();
    if (filters?.desde) params = params.set('desde', filters.desde);
    if (filters?.hasta) params = params.set('hasta', filters.hasta);
    return this.http.get<AdminFinanzasResumen>(`${this.base}/admin/finanzas/resumen`, { params });
  }

  getFinanzasReportes(filters?: { desde?: string; hasta?: string }): Observable<AdminFinanzasReportes> {
    let params = new HttpParams();
    if (filters?.desde) params = params.set('desde', filters.desde);
    if (filters?.hasta) params = params.set('hasta', filters.hasta);
    return this.http.get<AdminFinanzasReportes>(`${this.base}/admin/finanzas/reportes`, { params });
  }
}
