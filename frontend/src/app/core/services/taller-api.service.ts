import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import type {
  EspecialidadDto,
  MiTallerDto,
  MiTallerUpdatePayload,
  RegistroTallerPayload,
  TallerDashboardDto,
  TecnicoPortalCreatePayload,
  TecnicoPortalDto,
  TecnicoPortalUpdatePayload,
} from '../models/taller-api.models';
import type { ServicioCatalogo } from '../models/cotizacion.models';

@Injectable({ providedIn: 'root' })
export class TallerApiService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/app/taller`;

  registro(body: RegistroTallerPayload): Observable<MiTallerDto> {
    return this.http.post<MiTallerDto>(`${this.base}/registro`, body);
  }

  getDashboard(): Observable<TallerDashboardDto> {
    return this.http.get<TallerDashboardDto>(`${this.base}/dashboard`);
  }

  getMiTaller(): Observable<MiTallerDto> {
    return this.http.get<MiTallerDto>(`${this.base}/mi-taller`);
  }

  updateMiTaller(body: MiTallerUpdatePayload): Observable<MiTallerDto> {
    return this.http.put<MiTallerDto>(`${this.base}/mi-taller`, body);
  }

  listTecnicos(): Observable<TecnicoPortalDto[]> {
    return this.http.get<TecnicoPortalDto[]>(`${this.base}/tecnicos`);
  }

  getTecnico(id: number): Observable<TecnicoPortalDto> {
    return this.http.get<TecnicoPortalDto>(`${this.base}/tecnicos/${id}`);
  }

  createTecnico(body: TecnicoPortalCreatePayload): Observable<TecnicoPortalDto> {
    return this.http.post<TecnicoPortalDto>(`${this.base}/tecnicos`, body);
  }

  updateTecnico(id: number, body: TecnicoPortalUpdatePayload): Observable<TecnicoPortalDto> {
    return this.http.put<TecnicoPortalDto>(`${this.base}/tecnicos/${id}`, body);
  }

  listEspecialidades(): Observable<EspecialidadDto[]> {
    return this.http.get<EspecialidadDto[]>(`${environment.apiUrl}/especialidades`);
  }

  /** Servicios ofrecidos por el taller autenticado (portal responsable). */
  getMisServicios(): Observable<ServicioCatalogo[]> {
    return this.http.get<ServicioCatalogo[]>(`${this.base}/servicios`);
  }

  /** Actualiza servicios del taller autenticado (full-replace). */
  actualizarMisServicios(servicioIds: number[]): Observable<ServicioCatalogo[]> {
    return this.http.put<ServicioCatalogo[]>(`${this.base}/servicios`, {
      servicio_ids: servicioIds,
    });
  }

  /** Activa/desactiva grúa del taller autenticado. */
  actualizarMiGrua(tieneGrua: boolean): Observable<MiTallerDto> {
    return this.http.patch<MiTallerDto>(`${this.base}/grua`, { tiene_grua: tieneGrua });
  }
}
