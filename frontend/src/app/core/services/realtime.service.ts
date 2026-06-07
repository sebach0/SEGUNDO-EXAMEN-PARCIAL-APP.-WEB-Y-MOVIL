import { Injectable, NgZone, inject } from '@angular/core';
import {
  Subject,
  Observable,
  filter,
  BehaviorSubject,
} from 'rxjs';
import type { RealtimeEvent, RealtimeEventType } from '../models/ciclo4.models';
import { TallerAuthService } from './taller-auth.service';
import { environment } from '../../../environments/environment';

/**
 * RealtimeService — Ciclo 4
 *
 * Maneja la conexión WebSocket al endpoint:
 *   ws(s)://host/ws/incidents/{incident_id}?token={jwt}
 *
 * Características:
 * - Reconexión automática con backoff exponencial (máx. 30s).
 * - Expone todos los eventos como Observable<RealtimeEvent>.
 * - Filtra por tipo para status updates y tracking updates.
 * - Emite estado de conexión: 'connected' | 'reconnecting' | 'disconnected'.
 */

export type WsConnectionStatus = 'connected' | 'reconnecting' | 'disconnected';

@Injectable({ providedIn: 'root' })
export class RealtimeService {
  private readonly auth = inject(TallerAuthService);
  private readonly zone = inject(NgZone);

  private ws: WebSocket | null = null;
  private currentIncidentId: number | null = null;
  private reconnectAttempt = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private destroyed = false;

  private readonly _events$ = new Subject<RealtimeEvent>();
  private readonly _status$ = new BehaviorSubject<WsConnectionStatus>('disconnected');

  // ── API pública ───────────────────────────────────────────────────────────

  /** Observable de TODOS los eventos WebSocket recibidos. */
  events$(): Observable<RealtimeEvent> {
    return this._events$.asObservable();
  }

  /** Observable del estado de conexión. */
  connectionStatus$(): Observable<WsConnectionStatus> {
    return this._status$.asObservable();
  }

  /** Filtra eventos de tipo ESTADO_CAMBIADO. */
  statusUpdates$(): Observable<RealtimeEvent> {
    return this._events$.pipe(filter((e) => e.type === 'ESTADO_CAMBIADO'));
  }

  /** Filtra eventos de tipo TRACKING_UPDATE. */
  trackingUpdates$(): Observable<RealtimeEvent> {
    return this._events$.pipe(filter((e) => e.type === 'TRACKING_UPDATE'));
  }

  /** Filtra eventos de ETA actualizado (flujo solicitudes unificado). */
  etaUpdates$(): Observable<RealtimeEvent> {
    return this._events$.pipe(filter((e) => e.type === 'ETA_ACTUALIZADO'));
  }

  /** Filtra avisos de servicio retrasado. */
  retrasoUpdates$(): Observable<RealtimeEvent> {
    return this._events$.pipe(filter((e) => e.type === 'SERVICIO_RETRASADO'));
  }

  /** Conecta al WebSocket del incidente. Desconecta el anterior si existe. */
  connectToIncident(incidentId: number): void {
    if (this.currentIncidentId === incidentId && this.ws?.readyState === WebSocket.OPEN) {
      return; // Ya conectado al mismo incidente
    }
    this.disconnect();
    this.destroyed = false;
    this.currentIncidentId = incidentId;
    this.reconnectAttempt = 0;
    this._connect();
  }

  /** Desconecta el WebSocket y detiene la reconexión. */
  disconnect(): void {
    this.destroyed = true;
    this._clearReconnectTimer();
    if (this.ws) {
      this.ws.onclose = null; // evitar disparo de reconexión al cerrar manualmente
      this.ws.close();
      this.ws = null;
    }
    this._status$.next('disconnected');
    this.currentIncidentId = null;
  }

  // ── Internos ──────────────────────────────────────────────────────────────

  private _buildWsUrl(incidentId: number): string {
    const token = this.auth.getAccessToken() ?? '';
    // WS en dev: ws://localhost:4200/api/ws/... → proxy lo reenvía al backend
    // En prod: wss://<domain>/api/ws/...
    const baseWs = window.location.origin.replace(/^http/, 'ws');
    return `${baseWs}/api/ws/incidents/${incidentId}?token=${token}`;
  }

  private _connect(): void {
    if (this.destroyed || this.currentIncidentId == null) return;

    const url = this._buildWsUrl(this.currentIncidentId);
    this.zone.runOutsideAngular(() => {
      const ws = new WebSocket(url);
      this.ws = ws;

      ws.onopen = () => {
        this.zone.run(() => {
          this.reconnectAttempt = 0;
          this._status$.next('connected');
        });
      };

      ws.onmessage = (event: MessageEvent) => {
        this.zone.run(() => {
          try {
            const data = JSON.parse(event.data as string) as RealtimeEvent;
            this._events$.next(data);
          } catch {
            // Mensaje no parseable — ignorar
          }
        });
      };

      ws.onerror = () => {
        // onerror siempre precede a onclose; la reconexión se maneja en onclose
        this.zone.run(() => this._status$.next('reconnecting'));
      };

      ws.onclose = () => {
        this.zone.run(() => {
          if (!this.destroyed) {
            this._scheduleReconnect();
          }
        });
      };
    });
  }

  private _scheduleReconnect(): void {
    this._status$.next('reconnecting');
    const delay = Math.min(1000 * 2 ** this.reconnectAttempt, 30_000);
    this.reconnectAttempt++;
    this.reconnectTimer = setTimeout(() => {
      if (!this.destroyed) this._connect();
    }, delay);
  }

  private _clearReconnectTimer(): void {
    if (this.reconnectTimer != null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }
}
