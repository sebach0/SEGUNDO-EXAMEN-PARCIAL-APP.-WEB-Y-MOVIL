import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { from, Observable } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { OfflineQueueService } from './offline-queue.service';
import type {
  SyncResult,
  SyncStatusItem,
  WebSyncPayload,
  OfflineEvent,
  SolicitudWebSyncPayload,
  SolicitudSyncResult,
} from '../models/ciclo4.models';

/**
 * SyncService — Ciclo 4
 *
 * Responsabilidades:
 * 1. Enviar eventos offline acumulados en IndexedDB al backend.
 * 2. Consultar el estado de sincronización desde el backend.
 * 3. Procesar respuestas parciales (algunos OK, algunos con error).
 * 4. Auto-sincronizar cuando se recupera la conexión.
 */
@Injectable({ providedIn: 'root' })
export class SyncService {
  private readonly http = inject(HttpClient);
  private readonly queue = inject(OfflineQueueService);
  private readonly syncBase = `${environment.apiUrl}/sync`;

  // ── Enviar eventos web offline ────────────────────────────────────────────

  /**
   * POST /api/sync/web/events
   * Envía los eventos offline al backend y actualiza el estado local en IndexedDB.
   */
  syncWebEvents(events: OfflineEvent[]): Observable<SyncResult> {
    const payload: WebSyncPayload = {
      eventos: events.map((e) => ({
        client_uuid: e.client_uuid,
        incidente_id: e.incidente_id,
        tipo_evento: e.tipo_evento,
        payload: e.payload,
        registrado_local_en: e.registrado_local_en,
      })),
    };
    return this.http.post<SyncResult>(`${this.syncBase}/web/events`, payload);
  }

  // ── Consultar estado de sincronización ────────────────────────────────────

  /**
   * GET /api/sync/status
   * Devuelve los registros de sincronización del usuario autenticado.
   */
  getSyncStatus(): Observable<SyncStatusItem[]> {
    return this.http.get<SyncStatusItem[]>(`${this.syncBase}/status`);
  }

  // ── Sync hacia flujo real (solicitudes_emergencia) — Opción A ────────────

  /**
   * POST /api/app/taller/emergencias/sync-web
   * Envía eventos offline con solicitud_id al backend (flujo real).
   * El interceptor inyecta automáticamente el token de taller responsable
   * porque la URL contiene /app/taller.
   */
  syncSolicitudWebEvents(events: OfflineEvent[]): Observable<SolicitudSyncResult> {
    const payload: SolicitudWebSyncPayload = {
      eventos: events
        .filter((e) => e.solicitud_id != null)
        .map((e) => ({
          client_uuid: e.client_uuid,
          solicitud_id: e.solicitud_id!,
          tipo_evento: e.tipo_evento,
          payload: e.payload,
          registrado_local_en: e.registrado_local_en,
        })),
    };
    const tallerBase = `${environment.apiUrl}/app/taller/emergencias`;
    return this.http.post<SolicitudSyncResult>(`${tallerBase}/sync-web`, payload);
  }

  // ── Auto-sincronización ───────────────────────────────────────────────────

  /**
   * Recupera eventos pendientes de IndexedDB y los envía al backend.
   * Separa por _entidad:
   *   - 'solicitud_evento' → POST /api/app/taller/emergencias/sync-web (flujo real)
   *   - cualquier otro    → POST /api/sync/web/events               (flujo ciclo4)
   * Actualiza el estado local de cada registro según la respuesta.
   * Llama este método cuando se detecta `window.online`.
   */
  syncPendingAutomatically(): Observable<SyncResult> {
    return from(this.queue.getPendingEvents()).pipe(
      switchMap(async (pending) => {
        if (!pending.length) {
          return { total: 0, sincronizados: 0, con_error: 0, detalle: [] } satisfies SyncResult;
        }

        // Separar por tipo de flujo
        const solicitudEventos = pending.filter((e) => e._entidad === 'solicitud_evento');
        const ciclo4Eventos = pending.filter((e) => e._entidad !== 'solicitud_evento');

        // Marcar todos como "enviado" antes de transmitir
        for (const ev of pending) {
          await this.queue.markAsSent(ev.client_uuid);
        }

        const resultados: SyncResult = { total: 0, sincronizados: 0, con_error: 0, detalle: [] };

        const procesar = async (
          events: OfflineEvent[],
          syncFn: (evs: OfflineEvent[]) => Observable<{ detalle: { client_uuid: string; sincronizado: boolean; error?: string | null }[] }>,
        ): Promise<void> => {
          if (!events.length) return;
          resultados.total += events.length;
          await new Promise<void>((resolve) => {
            syncFn(events).subscribe({
              next: async (result) => {
                for (const item of result.detalle) {
                  if (item.sincronizado) {
                    await this.queue.markAsSynced(item.client_uuid);
                    resultados.sincronizados++;
                  } else {
                    await this.queue.markAsError(item.client_uuid, item.error ?? 'Error desconocido');
                    resultados.con_error++;
                    resultados.detalle.push({
                      client_uuid: item.client_uuid,
                      incidente_id: 0,
                      tipo_evento: '',
                      sincronizado: false,
                      error: item.error ?? 'Error desconocido',
                    });
                  }
                }
                resolve();
              },
              error: async (err) => {
                const errorMsg = (err as { message?: string })?.message ?? 'Sin conexión';
                for (const ev of events) {
                  await this.queue.markAsError(ev.client_uuid, errorMsg);
                  resultados.con_error++;
                }
                resultados.total += events.length;
                resolve();
              },
            });
          });
        };

        // Flujo real (solicitud_evento)
        await procesar(solicitudEventos, (evs) => this.syncSolicitudWebEvents(evs));
        // Flujo ciclo4 (incidente)
        await procesar(ciclo4Eventos, (evs) => this.syncWebEvents(evs));

        return resultados;
      }),
    );
  }
}
