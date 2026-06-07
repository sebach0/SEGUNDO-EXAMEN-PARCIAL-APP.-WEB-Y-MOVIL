import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import type { Cotizacion, CotizacionContexto, CotizacionCreateIn, ServicioCatalogo, KpiSummary } from '../models/cotizacion.models';

@Injectable({ providedIn: 'root' })
export class CotizacionService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiUrl;
  /** Portal responsable: el interceptor envía Bearer de taller en /app/taller/* */
  private readonly tallerBase = `${environment.apiUrl}/app/taller`;

  /** Lista cotizaciones de una solicitud (portal taller) */
  listar(solicitudId: number): Observable<Cotizacion[]> {
    return this.http.get<Cotizacion[]>(
      `${this.tallerBase}/cotizaciones/solicitudes/${solicitudId}`,
    );
  }

  /** Distancia y servicios del taller para armar la oferta (portal taller) */
  contextoOferta(solicitudId: number): Observable<CotizacionContexto> {
    return this.http.get<CotizacionContexto>(
      `${this.tallerBase}/cotizaciones/solicitudes/${solicitudId}/contexto-oferta`,
    );
  }

  /** El taller propone una cotización (portal taller) */
  proponer(solicitudId: number, body: CotizacionCreateIn): Observable<Cotizacion> {
    return this.http.post<Cotizacion>(
      `${this.tallerBase}/cotizaciones/solicitudes/${solicitudId}`,
      body,
    );
  }

  /** El cliente selecciona una cotización (bloquea las demás) */
  seleccionar(solicitudId: number, cotizacionId: number): Observable<Cotizacion> {
    return this.http.post<Cotizacion>(
      `${this.base}/cotizaciones/solicitudes/${solicitudId}/cotizacion/${cotizacionId}/seleccionar`,
      {},
    );
  }

  // ── Servicios del taller ────────────────────────────────────────────────────

  /** Catálogo global de servicios */
  getCatalogo(): Observable<ServicioCatalogo[]> {
    return this.http.get<ServicioCatalogo[]>(`${this.base}/talleres/catalogo/servicios`);
  }

  /** Servicios que ofrece un taller */
  getServiciosTaller(tallerId: number): Observable<ServicioCatalogo[]> {
    return this.http.get<ServicioCatalogo[]>(`${this.base}/talleres/${tallerId}/servicios`);
  }

  /** Actualiza los servicios del taller (full-replace) */
  actualizarServiciosTaller(tallerId: number, servicioIds: number[]): Observable<ServicioCatalogo[]> {
    return this.http.put<ServicioCatalogo[]>(`${this.base}/talleres/${tallerId}/servicios`, {
      servicio_ids: servicioIds,
    });
  }

  /** Activa/desactiva grúa */
  actualizarGrua(tallerId: number, tieneGrua: boolean): Observable<unknown> {
    return this.http.patch(`${this.base}/talleres/${tallerId}/grua`, { tiene_grua: tieneGrua });
  }

  // ── KPIs ────────────────────────────────────────────────────────────────────

  getKpiSummary(params?: {
    desde?: string;
    hasta?: string;
    taller_id?: number;
  }): Observable<KpiSummary> {
    let url = `${this.base}/kpis/summary`;
    const qp: string[] = [];
    if (params?.desde) qp.push(`desde=${params.desde}`);
    if (params?.hasta) qp.push(`hasta=${params.hasta}`);
    if (params?.taller_id != null) qp.push(`taller_id=${params.taller_id}`);
    if (qp.length) url += '?' + qp.join('&');
    return this.http.get<KpiSummary>(url);
  }
}
