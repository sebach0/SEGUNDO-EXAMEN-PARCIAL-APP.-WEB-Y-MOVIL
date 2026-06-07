import {
  Component,
  inject,
  OnInit,
  OnDestroy,
  ChangeDetectorRef,
  ChangeDetectionStrategy,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { Subscription } from 'rxjs';
import { IncidentService } from '../../../../core/services/incident.service';
import { RealtimeService, type WsConnectionStatus } from '../../../../core/services/realtime.service';
import { RealtimeStatusPanelComponent } from '../realtime-panel/realtime-status-panel.component';
import type {
  IncidentDetalle,
  IncidentStatus,
  TrackingPoint,
} from '../../../../core/models/ciclo4.models';
import {
  INCIDENT_STATUS_LABELS,
  INCIDENT_STATUS_STEPS,
} from '../../../../core/models/ciclo4.models';

/**
 * IncidentRealtimeTrackingComponent — Ciclo 4 (CU36 / CU37)
 *
 * Ruta: /taller/panel/ciclo4/incidentes/:id/tracking
 *
 * Muestra:
 * - Detalle del incidente.
 * - Línea de progreso de estados.
 * - Conexión WebSocket con indicador de estado.
 * - Última ubicación GPS recibida.
 * - Panel de eventos en tiempo real (RealtimeStatusPanelComponent).
 */
@Component({
  selector: 'app-incident-realtime-tracking',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, RouterLink, RealtimeStatusPanelComponent],
  templateUrl: './incident-realtime-tracking.component.html',
  styleUrl: './incident-realtime-tracking.component.scss',
})
export class IncidentRealtimeTrackingComponent implements OnInit, OnDestroy {
  private readonly route = inject(ActivatedRoute);
  private readonly incidentSvc = inject(IncidentService);
  private readonly rt = inject(RealtimeService);
  private readonly cdr = inject(ChangeDetectorRef);

  incidentId: number | null = null;
  incident: IncidentDetalle | null = null;
  loading = true;
  error: string | null = null;

  wsStatus: WsConnectionStatus = 'disconnected';
  lastTracking: TrackingPoint | null = null;

  readonly statusSteps = INCIDENT_STATUS_STEPS;
  readonly statusLabels = INCIDENT_STATUS_LABELS;

  private subs: Subscription[] = [];

  ngOnInit(): void {
    const idSub = this.route.paramMap.subscribe((p) => {
      const raw = Number(p.get('id'));
      this.incidentId = Number.isFinite(raw) && raw > 0 ? raw : null;
      if (this.incidentId) {
        this.loadIncident();
        this.connectWs();
      } else {
        this.loading = false;
        this.error = 'ID de incidente inválido.';
        this.cdr.markForCheck();
      }
    });
    this.subs.push(idSub);
  }

  ngOnDestroy(): void {
    this.subs.forEach((s) => s.unsubscribe());
    this.rt.disconnect();
  }

  // ── Carga inicial ─────────────────────────────────────────────────────────

  loadIncident(): void {
    if (!this.incidentId) return;
    this.loading = true;
    this.error = null;

    this.incidentSvc.getIncidentById(this.incidentId).subscribe({
      next: (inc) => {
        this.incident = inc;
        // Último tracking del historial reciente
        if (inc.tracking_reciente?.length) {
          this.lastTracking = inc.tracking_reciente[inc.tracking_reciente.length - 1];
        }
        this.loading = false;
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.loading = false;
        this.error = this.extractError(err, 'No se pudo cargar el incidente.');
        this.cdr.markForCheck();
      },
    });
  }

  // ── WebSocket ─────────────────────────────────────────────────────────────

  connectWs(): void {
    if (!this.incidentId) return;
    this.rt.connectToIncident(this.incidentId);

    const statusSub = this.rt.connectionStatus$().subscribe((status) => {
      this.wsStatus = status;
      this.cdr.markForCheck();
    });

    const statusEventSub = this.rt.statusUpdates$().subscribe((ev) => {
      if (this.incident && ev.status) {
        this.incident = { ...this.incident, estado: ev.status };
        this.cdr.markForCheck();
      }
    });

    const trackingSub = this.rt.trackingUpdates$().subscribe((ev) => {
      const payload = ev.payload as { latitud?: number; longitud?: number };
      if (payload?.latitud != null && payload?.longitud != null) {
        this.lastTracking = {
          id: 0,
          incidente_id: this.incidentId!,
          taller_id: null,
          tecnico_id: null,
          latitud: payload.latitud,
          longitud: payload.longitud,
          velocidad_kmh: null,
          registrado_en: ev.emitted_at,
        };
        this.cdr.markForCheck();
      }
    });

    this.subs.push(statusSub, statusEventSub, trackingSub);
  }

  // ── Helpers de plantilla ──────────────────────────────────────────────────

  currentStepIndex(): number {
    if (!this.incident) return -1;
    return this.statusSteps.indexOf(this.incident.estado as IncidentStatus);
  }

  isCancelled(): boolean {
    return this.incident?.estado === 'CANCELADO';
  }

  wsStatusLabel(): string {
    const map: Record<WsConnectionStatus, string> = {
      connected: 'Conectado en tiempo real',
      reconnecting: 'Reconectando…',
      disconnected: 'Sin conexión',
    };
    return map[this.wsStatus];
  }

  wsStatusClass(): string {
    const map: Record<WsConnectionStatus, string> = {
      connected: 'ws--connected',
      reconnecting: 'ws--reconnecting',
      disconnected: 'ws--disconnected',
    };
    return map[this.wsStatus];
  }

  mapLink(): string | null {
    if (!this.lastTracking) return null;
    const { latitud: lat, longitud: lng } = this.lastTracking;
    return `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lng}#map=16/${lat}/${lng}`;
  }

  private extractError(err: { error?: { detail?: unknown } }, fallback: string): string {
    const d = err?.error?.detail;
    if (typeof d === 'string') return d;
    return fallback;
  }
}
