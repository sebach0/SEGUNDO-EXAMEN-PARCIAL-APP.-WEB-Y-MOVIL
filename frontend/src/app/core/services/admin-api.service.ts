import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import type {
  AccionBitacora,
  AdminDashboardKpisDto,
  AdminFinanzasReportes,
  AdminFinanzasResumen,
  AssignmentResultDto,
  BitacoraDto,
  IncidentReportReadDto,
  PerformanceReportReadDto,
  PermisoDto,
  RolDto,
  RolPermisosDto,
  TallerCreatePayload,
  TallerDto,
  TallerUpdatePayload,
  TenantCreatePayload,
  TenantDto,
  TenantMembersDto,
  TenantUpdatePayload,
  UsuarioCreatePayload,
  UsuarioListDto,
  UsuarioUpdatePayload,
  WorkshopReportReadDto,
  WorkshopSlaDetailDto,
  WorkshopSlaDto,
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

  listAdminEmergencias(estado?: string): Observable<import('../models/admin-api.models').EmergenciaAdminDto[]> {
    let params = new HttpParams();
    if (estado) params = params.set('estado', estado);
    return this.http.get<import('../models/admin-api.models').EmergenciaAdminDto[]>(
      `${this.base}/incidents/admin/emergencias`, { params }
    );
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

  // ── Ciclo 5 — Tenants (CU43) ───────────────────────────────────────────────

  listTenants(): Observable<TenantDto[]> {
    return this.http.get<TenantDto[]>(`${this.base}/admin/tenants/`);
  }

  getTenant(id: number): Observable<TenantDto> {
    return this.http.get<TenantDto>(`${this.base}/admin/tenants/${id}`);
  }

  createTenant(body: TenantCreatePayload): Observable<TenantDto> {
    return this.http.post<TenantDto>(`${this.base}/admin/tenants/`, body);
  }

  updateTenant(id: number, body: TenantUpdatePayload): Observable<TenantDto> {
    return this.http.patch<TenantDto>(`${this.base}/admin/tenants/${id}`, body);
  }

  activateTenant(id: number): Observable<TenantDto> {
    return this.http.patch<TenantDto>(`${this.base}/admin/tenants/${id}/activate`, {});
  }

  deactivateTenant(id: number): Observable<TenantDto> {
    return this.http.patch<TenantDto>(`${this.base}/admin/tenants/${id}/deactivate`, {});
  }

  // ── Ciclo 5 — Asignaciones (CU44) ──────────────────────────────────────────

  getTenantMembers(tenantId: number): Observable<TenantMembersDto> {
    return this.http.get<TenantMembersDto>(`${this.base}/admin/tenants/${tenantId}/members`);
  }

  assignUsersToTenant(tenantId: number, ids: number[]): Observable<AssignmentResultDto> {
    return this.http.post<AssignmentResultDto>(
      `${this.base}/admin/tenants/${tenantId}/assign-users`,
      { ids },
    );
  }

  assignWorkshopsToTenant(tenantId: number, ids: number[]): Observable<AssignmentResultDto> {
    return this.http.post<AssignmentResultDto>(
      `${this.base}/admin/tenants/${tenantId}/assign-workshops`,
      { ids },
    );
  }

  assignTechniciansToTenant(tenantId: number, ids: number[]): Observable<AssignmentResultDto> {
    return this.http.post<AssignmentResultDto>(
      `${this.base}/admin/tenants/${tenantId}/assign-technicians`,
      { ids },
    );
  }

  patchUserTenant(userId: number, tenantId: number): Observable<AssignmentResultDto> {
    return this.http.patch<AssignmentResultDto>(`${this.base}/admin/users/${userId}/tenant`, {
      tenant_id: tenantId,
    });
  }

  patchWorkshopTenant(workshopId: number, tenantId: number): Observable<AssignmentResultDto> {
    return this.http.patch<AssignmentResultDto>(
      `${this.base}/admin/workshops/${workshopId}/tenant`,
      { tenant_id: tenantId },
    );
  }

  // ── Ciclo 5 — KPI Dashboard (CU45) ─────────────────────────────────────────

  getAdminDashboardKpis(filters?: {
    tenant_id?: number;
    desde?: string;
    hasta?: string;
    taller_id?: number;
    zona_id?: number;
  }): Observable<AdminDashboardKpisDto> {
    let params = new HttpParams();
    if (filters?.tenant_id != null) params = params.set('tenant_id', String(filters.tenant_id));
    if (filters?.desde) params = params.set('desde', filters.desde);
    if (filters?.hasta) params = params.set('hasta', filters.hasta);
    if (filters?.taller_id != null) params = params.set('taller_id', String(filters.taller_id));
    if (filters?.zona_id != null) params = params.set('zona_id', String(filters.zona_id));
    return this.http.get<AdminDashboardKpisDto>(`${this.base}/admin/dashboard/kpis`, { params });
  }

  // ── Ciclo 5 — Reportes (CU46) ──────────────────────────────────────────────

  getIncidentsReport(filters?: {
    tenant_id?: number;
    desde?: string;
    hasta?: string;
    taller_id?: number;
    zona_id?: number;
    estado?: string;
  }): Observable<IncidentReportReadDto> {
    let params = new HttpParams();
    if (filters?.tenant_id != null) params = params.set('tenant_id', String(filters.tenant_id));
    if (filters?.desde) params = params.set('desde', filters.desde);
    if (filters?.hasta) params = params.set('hasta', filters.hasta);
    if (filters?.taller_id != null) params = params.set('taller_id', String(filters.taller_id));
    if (filters?.zona_id != null) params = params.set('zona_id', String(filters.zona_id));
    if (filters?.estado) params = params.set('estado', filters.estado);
    return this.http.get<IncidentReportReadDto>(`${this.base}/admin/reports/incidents`, { params });
  }

  getPerformanceReport(filters?: {
    tenant_id?: number;
    desde?: string;
    hasta?: string;
  }): Observable<PerformanceReportReadDto> {
    let params = new HttpParams();
    if (filters?.tenant_id != null) params = params.set('tenant_id', String(filters.tenant_id));
    if (filters?.desde) params = params.set('desde', filters.desde);
    if (filters?.hasta) params = params.set('hasta', filters.hasta);
    return this.http.get<PerformanceReportReadDto>(`${this.base}/admin/reports/performance`, { params });
  }

  getWorkshopsReport(filters?: {
    tenant_id?: number;
    desde?: string;
    hasta?: string;
  }): Observable<WorkshopReportReadDto> {
    let params = new HttpParams();
    if (filters?.tenant_id != null) params = params.set('tenant_id', String(filters.tenant_id));
    if (filters?.desde) params = params.set('desde', filters.desde);
    if (filters?.hasta) params = params.set('hasta', filters.hasta);
    return this.http.get<WorkshopReportReadDto>(`${this.base}/admin/reports/workshops`, { params });
  }

  exportReportCsv(filters?: {
    tenant_id?: number;
    desde?: string;
    hasta?: string;
    estado?: string;
  }): Observable<Blob> {
    let params = new HttpParams();
    if (filters?.tenant_id != null) params = params.set('tenant_id', String(filters.tenant_id));
    if (filters?.desde) params = params.set('desde', filters.desde);
    if (filters?.hasta) params = params.set('hasta', filters.hasta);
    if (filters?.estado) params = params.set('estado', filters.estado);
    return this.http.get(`${this.base}/admin/reports/export/csv`, {
      params,
      responseType: 'blob',
    });
  }

  // ── Ciclo 5 — SLA por taller (CU50) ────────────────────────────────────────

  getSlaWorkshops(filters?: {
    tenant_id?: number;
    desde?: string;
    hasta?: string;
    taller_id?: number;
    zona_id?: number;
  }): Observable<WorkshopSlaDto[]> {
    let params = new HttpParams();
    if (filters?.tenant_id != null) params = params.set('tenant_id', String(filters.tenant_id));
    if (filters?.desde) params = params.set('desde', filters.desde);
    if (filters?.hasta) params = params.set('hasta', filters.hasta);
    if (filters?.taller_id != null) params = params.set('taller_id', String(filters.taller_id));
    if (filters?.zona_id != null) params = params.set('zona_id', String(filters.zona_id));
    return this.http.get<WorkshopSlaDto[]>(`${this.base}/admin/sla/workshops`, { params });
  }

  getSlaWorkshopDetail(workshopId: number, filters?: {
    tenant_id?: number;
    desde?: string;
    hasta?: string;
  }): Observable<WorkshopSlaDetailDto> {
    let params = new HttpParams();
    if (filters?.tenant_id != null) params = params.set('tenant_id', String(filters.tenant_id));
    if (filters?.desde) params = params.set('desde', filters.desde);
    if (filters?.hasta) params = params.set('hasta', filters.hasta);
    return this.http.get<WorkshopSlaDetailDto>(
      `${this.base}/admin/sla/workshops/${workshopId}`,
      { params },
    );
  }
}
