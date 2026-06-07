import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import type {
  Incident,
  IncidentDetalle,
  TrackingPoint,
  TrackingPayload,
  CambiarEstadoPayload,
  SyncStatusItem,
  WebSyncPayload,
  SyncResult,
} from '../models/ciclo4.models';

/**
 * IncidentService — Ciclo 4
 *
 * Consume los endpoints REST del backend FastAPI para el módulo de incidentes.
 * El interceptor `apiAuthInterceptor` inyecta automáticamente el Bearer token
 * porque las URLs contienen `/api/`.
 *
 * Base URL: /api/incidents  (backend: router con prefix="/incidents")
 */
@Injectable({ providedIn: 'root' })
export class IncidentService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/incidents`;

  /** GET /api/incidents — Lista incidentes del tenant actual (filtrado automático por JWT). */
  listIncidents(): Observable<Incident[]> {
    return this.http.get<Incident[]>(this.base);
  }

  /** GET /api/incidents/{id} — Detalle completo con historial y tracking reciente. */
  getIncidentById(id: number): Observable<IncidentDetalle> {
    return this.http.get<IncidentDetalle>(`${this.base}/${id}`);
  }

  /** GET /api/incidents/{id}/tracking — Puntos GPS del incidente. */
  getIncidentTracking(id: number): Observable<TrackingPoint[]> {
    return this.http.get<TrackingPoint[]>(`${this.base}/${id}/tracking`);
  }

  /**
   * PATCH /api/incidents/{id}/status — Cambiar estado del incidente.
   * Registra historial y emite evento WebSocket en el backend.
   */
  updateIncidentStatus(id: number, payload: CambiarEstadoPayload): Observable<Incident> {
    return this.http.patch<Incident>(`${this.base}/${id}/status`, payload);
  }

  /**
   * POST /api/incidents/{id}/tracking — Enviar punto GPS de tracking.
   */
  sendTrackingUpdate(id: number, payload: TrackingPayload): Observable<TrackingPoint> {
    return this.http.post<TrackingPoint>(`${this.base}/${id}/tracking`, payload);
  }
}
