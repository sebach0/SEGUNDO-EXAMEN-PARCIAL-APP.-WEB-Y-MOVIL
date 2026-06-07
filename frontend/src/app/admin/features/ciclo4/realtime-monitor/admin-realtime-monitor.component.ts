import {
  Component,
  inject,
  OnInit,
  OnDestroy,
  ChangeDetectorRef,
  ChangeDetectionStrategy,
} from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Subscription } from 'rxjs';
import type { RealtimeEvent } from '../../../../core/models/ciclo4.models';
import { INCIDENT_STATUS_LABELS } from '../../../../core/models/ciclo4.models';
import { AdminAuthService } from '../../../../core/services/admin-auth.service';
import { environment } from '../../../../../environments/environment';

/** Solicitud activa del flujo real (solicitudes_emergencia). */
interface SolicitudActiva {
  id: number;
  estado: string;
  taller_id: number | null;
  tecnico_id: number | null;
  cliente_id: number;
  tiempo_estimado_min: number | null;
  created_at: string | null;
  asignado_en: string | null;
  en_camino_en: string | null;
}

/**
 * AdminRealtimeMonitorComponent — Ciclo 4 (Monitor Admin Completo)
 *
 * Ruta: /admin/panel/ciclo4/realtime-monitor
 *
 * Conecta al WebSocket /ws/admin/feed y lista solicitudes activas reales.
 * Muestra cambios de estado en tiempo real sin necesidad de refrescar.
 */
@Component({
  selector: 'app-admin-realtime-monitor',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, DatePipe],
  templateUrl: './admin-realtime-monitor.component.html',
  styleUrl: './admin-realtime-monitor.component.scss',
})
export class AdminRealtimeMonitorComponent implements OnInit, OnDestroy {
  private readonly http = inject(HttpClient);
  private readonly auth = inject(AdminAuthService);
  private readonly cdr = inject(ChangeDetectorRef);

  readonly statusLabels = INCIDENT_STATUS_LABELS;

  // ── Estado de solicitudes activas ─────────────────────────────────────────
  solicitudes: SolicitudActiva[] = [];
  loadingSolicitudes = true;
  solicitudesError: string | null = null;

  // ── Feed de eventos WS ────────────────────────────────────────────────────
  recentEvents: RealtimeEvent[] = [];
  wsStatus: 'connecting' | 'connected' | 'disconnected' = 'connecting';
  wsError: string | null = null;

  // ── WS internals ──────────────────────────────────────────────────────────
  private ws: WebSocket | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectAttempt = 0;
  private destroyed = false;

  private subs: Subscription[] = [];

  ngOnInit(): void {
    this.loadSolicitudes();
    this._connectWs();
  }

  ngOnDestroy(): void {
    this.destroyed = true;
    this._clearTimer();
    if (this.ws) {
      this.ws.onclose = null;
      this.ws.close();
    }
    this.subs.forEach((s) => s.unsubscribe());
  }

  // ── REST: solicitudes activas ─────────────────────────────────────────────

  loadSolicitudes(): void {
    this.loadingSolicitudes = true;
    this.solicitudesError = null;
    this.http
      .get<SolicitudActiva[]>(`${environment.apiUrl}/incidents/admin/solicitudes-activas`)
      .subscribe({
        next: (list) => {
          this.solicitudes = list;
          this.loadingSolicitudes = false;
          this.cdr.markForCheck();
        },
        error: (err) => {
          this.loadingSolicitudes = false;
          const d = (err as { error?: { detail?: string } })?.error?.detail;
          this.solicitudesError = d ?? 'No se pudieron cargar las solicitudes activas.';
          this.cdr.markForCheck();
        },
      });
  }

  // ── WebSocket admin feed ──────────────────────────────────────────────────

  private _buildWsUrl(): string {
    const token = this.auth.getAccessToken() ?? '';
    const baseWs = window.location.origin.replace(/^http/, 'ws');
    return `${baseWs}/api/ws/admin/feed?token=${token}`;
  }

  private _connectWs(): void {
    if (this.destroyed) return;
    const url = this._buildWsUrl();
    const ws = new WebSocket(url);
    this.ws = ws;
    this.wsStatus = 'connecting';
    this.cdr.markForCheck();

    ws.onopen = () => {
      this.reconnectAttempt = 0;
      this.wsStatus = 'connected';
      this.wsError = null;
      this.cdr.markForCheck();
    };

    ws.onmessage = (ev: MessageEvent) => {
      try {
        const data = JSON.parse(ev.data as string) as RealtimeEvent;
        // Ignorar el handshake ADMIN_CONNECTED
        if (data.type === 'ADMIN_CONNECTED') return;
        this.recentEvents = [data, ...this.recentEvents].slice(0, 50);
        // Si el evento es un cambio de estado, actualizar la lista
        if (data.type === 'ESTADO_CAMBIADO') {
          this._applyEstadoCambio(data);
        }
        this.cdr.markForCheck();
      } catch {
        // mensaje no parseable — ignorar
      }
    };

    ws.onerror = () => {
      this.wsStatus = 'disconnected';
      this.wsError = 'Error de conexión con el feed en tiempo real.';
      this.cdr.markForCheck();
    };

    ws.onclose = () => {
      if (!this.destroyed) {
        this.wsStatus = 'disconnected';
        this._scheduleReconnect();
        this.cdr.markForCheck();
      }
    };
  }

  private _applyEstadoCambio(event: RealtimeEvent): void {
    const id = event.incident_id;
    const idx = this.solicitudes.findIndex((s) => s.id === id);
    if (idx >= 0 && event.status) {
      this.solicitudes = [...this.solicitudes];
      this.solicitudes[idx] = { ...this.solicitudes[idx], estado: event.status };
      // Si finalizó o canceló, recargar la lista completa
      if (event.status === 'FINALIZADO' || event.status === 'CANCELADO') {
        setTimeout(() => this.loadSolicitudes(), 2000);
      }
    }
  }

  private _scheduleReconnect(): void {
    const delay = Math.min(1000 * 2 ** this.reconnectAttempt, 30_000);
    this.reconnectAttempt++;
    this._clearTimer();
    this.reconnectTimer = setTimeout(() => {
      if (!this.destroyed) this._connectWs();
    }, delay);
  }

  private _clearTimer(): void {
    if (this.reconnectTimer != null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  // ── UI ────────────────────────────────────────────────────────────────────

  statusClass(estado: string): string {
    const map: Record<string, string> = {
      PENDIENTE: 'badge--warning',
      BUSCANDO_TALLER: 'badge--info',
      REGISTRADA: 'badge--info',
      EN_REVISION: 'badge--warning',
      TALLER_ASIGNADO: 'badge--cyan',
      TECNICO_ASIGNADO: 'badge--cyan',
      EN_CAMINO: 'badge--warning',
      EN_ATENCION: 'badge--success',
      FINALIZADO: 'badge--muted',
      FINALIZADA: 'badge--muted',
      CANCELADO: 'badge--danger',
      CANCELADA: 'badge--danger',
    };
    return map[estado] ?? 'badge--muted';
  }

  /** Etiqueta legible para estados del flujo real o ciclo4. */
  statusLabel(estado: string): string {
    const ciclo4 = this.statusLabels as Record<string, string>;
    const solicitud: Record<string, string> = {
      REGISTRADA: 'Registrada',
      EN_REVISION: 'En revisión',
      TECNICO_ASIGNADO: 'Técnico asignado',
      FINALIZADA: 'Finalizada',
      CANCELADA: 'Cancelada',
    };
    return ciclo4[estado] ?? solicitud[estado] ?? estado;
  }

  wsStatusClass(): string {
    return {
      connecting: 'ws-dot--amber',
      connected: 'ws-dot--green',
      disconnected: 'ws-dot--red',
    }[this.wsStatus];
  }

  wsStatusLabel(): string {
    return {
      connecting: 'Conectando…',
      connected: 'En tiempo real',
      disconnected: 'Sin conexión WS',
    }[this.wsStatus];
  }

  trackByEvent(_: number, ev: RealtimeEvent): string {
    return `${ev.incident_id}-${ev.emitted_at}`;
  }

  trackBySol(_: number, s: SolicitudActiva): number {
    return s.id;
  }
}
