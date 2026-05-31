import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import type {
  AsignacionTecnicoDto,
  AsignarTecnicoPayload,
  AsignarTecnicoResultDto,
  BandejaIncidenteBaseDto,
  ComisionTallerDto,
  HistorialAtencionDto,
  RechazarBandejaPayload,
  ResumenComisionesDto,
  SolicitudBandejaDetalleDto,
  TallerDisponibilidadDto,
  TallerDisponibilidadUpdatePayload,
  ReporteTallerDashboardDto,
  EstadoSolicitudSeguimiento,
} from '../models/taller-emergencias.models';

@Injectable({ providedIn: 'root' })
export class TallerEmergenciasApiService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/app/taller/emergencias`;

  listBandejaDisponibles(): Observable<BandejaIncidenteBaseDto[]> {
    return this.http.get<BandejaIncidenteBaseDto[]>(`${this.base}/bandeja/disponibles`);
  }

  getBandejaDetalle(bandejaId: number): Observable<SolicitudBandejaDetalleDto> {
    return this.http.get<SolicitudBandejaDetalleDto>(`${this.base}/bandeja/${bandejaId}`);
  }

  aceptarBandeja(bandejaId: number): Observable<SolicitudBandejaDetalleDto> {
    return this.http.post<SolicitudBandejaDetalleDto>(`${this.base}/bandeja/${bandejaId}/aceptar`, {});
  }

  rechazarBandeja(bandejaId: number, body: RechazarBandejaPayload): Observable<SolicitudBandejaDetalleDto> {
    return this.http.post<SolicitudBandejaDetalleDto>(`${this.base}/bandeja/${bandejaId}/rechazar`, body);
  }

  getDisponibilidad(): Observable<TallerDisponibilidadDto> {
    return this.http.get<TallerDisponibilidadDto>(`${this.base}/disponibilidad`);
  }

  putDisponibilidad(body: TallerDisponibilidadUpdatePayload): Observable<TallerDisponibilidadDto> {
    return this.http.put<TallerDisponibilidadDto>(`${this.base}/disponibilidad`, body);
  }

  /** Asignar o reasignar técnico a la solicitud. */
  asignarTecnico(solicitudId: number, body: AsignarTecnicoPayload): Observable<AsignarTecnicoResultDto> {
    return this.http.post<AsignarTecnicoResultDto>(
      `${this.base}/solicitudes/${solicitudId}/asignar-tecnico`,
      body,
    );
  }

  listarAsignacionesTecnico(solicitudId: number): Observable<AsignacionTecnicoDto[]> {
    return this.http.get<AsignacionTecnicoDto[]>(`${this.base}/solicitudes/${solicitudId}/asignaciones`);
  }

  getReporteDashboard(params?: { desde?: string; hasta?: string }): Observable<ReporteTallerDashboardDto> {
    let p = new HttpParams();
    if (params?.desde) p = p.set('desde', params.desde);
    if (params?.hasta) p = p.set('hasta', params.hasta);
    return this.http.get<ReporteTallerDashboardDto>(`${this.base}/reportes/dashboard`, { params: p });
  }

  listHistorialAtenciones(params?: {
    estado?: EstadoSolicitudSeguimiento;
    desde?: string;
    hasta?: string;
    limit?: number;
  }): Observable<HistorialAtencionDto[]> {
    let p = new HttpParams();
    if (params?.estado) p = p.set('estado', params.estado);
    if (params?.desde) p = p.set('desde', params.desde);
    if (params?.hasta) p = p.set('hasta', params.hasta);
    if (params?.limit != null) p = p.set('limit', String(params.limit));
    return this.http.get<HistorialAtencionDto[]>(`${this.base}/historial-atenciones`, { params: p });
  }

  getResumenComisiones(): Observable<ResumenComisionesDto> {
    return this.http.get<ResumenComisionesDto>(`${this.base}/comisiones/resumen`);
  }

  listComisiones(): Observable<ComisionTallerDto[]> {
    return this.http.get<ComisionTallerDto[]>(`${this.base}/comisiones`);
  }
}
