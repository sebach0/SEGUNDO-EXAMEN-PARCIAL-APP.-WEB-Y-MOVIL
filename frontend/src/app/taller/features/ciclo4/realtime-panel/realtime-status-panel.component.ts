import { Component, Input, OnInit, OnDestroy, ChangeDetectorRef, inject } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { Subscription } from 'rxjs';
import { RealtimeService } from '../../../../core/services/realtime.service';
import type { RealtimeEvent } from '../../../../core/models/ciclo4.models';

/**
 * RealtimeStatusPanelComponent — Ciclo 4 (CU36 / CU37)
 *
 * Panel reutilizable que muestra los eventos WebSocket en tiempo real
 * de un incidente. Se puede incluir como componente hijo desde
 * IncidentRealtimeTrackingComponent u otros.
 *
 * Uso: <app-realtime-status-panel [incidentId]="123" />
 */
@Component({
  selector: 'app-realtime-status-panel',
  standalone: true,
  imports: [CommonModule, DatePipe],
  templateUrl: './realtime-status-panel.component.html',
  styleUrl: './realtime-status-panel.component.scss',
})
export class RealtimeStatusPanelComponent implements OnInit, OnDestroy {
  @Input({ required: true }) incidentId!: number;

  private readonly rt = inject(RealtimeService);
  private readonly cdr = inject(ChangeDetectorRef);
  private sub?: Subscription;

  events: RealtimeEvent[] = [];

  /** Mapa de tipo de evento → clase CSS del badge */
  readonly badgeClass: Record<string, string> = {
    ESTADO_CAMBIADO: 'badge--info',
    TRACKING_UPDATE: 'badge--muted',
    TALLER_ACEPTO: 'badge--success',
    TALLER_RECHAZO: 'badge--danger',
    AUXILIO_EN_CAMINO: 'badge--warning',
    SERVICIO_ATENDIDO: 'badge--cyan',
    SERVICIO_FINALIZADO: 'badge--success',
  };

  readonly badgeLabel: Record<string, string> = {
    ESTADO_CAMBIADO: 'Estado',
    TRACKING_UPDATE: 'GPS',
    TALLER_ACEPTO: 'Aceptado',
    TALLER_RECHAZO: 'Rechazado',
    AUXILIO_EN_CAMINO: 'En camino',
    SERVICIO_ATENDIDO: 'Atendido',
    SERVICIO_FINALIZADO: 'Finalizado',
  };

  ngOnInit(): void {
    this.sub = this.rt.events$().subscribe((event) => {
      if (event.incident_id !== this.incidentId) return;
      this.events.unshift(event); // nuevo evento al inicio de la lista
      // Limitar a 50 eventos en memoria
      if (this.events.length > 50) this.events.pop();
      this.cdr.markForCheck();
    });
  }

  ngOnDestroy(): void {
    this.sub?.unsubscribe();
  }

  getBadgeClass(type: string): string {
    return this.badgeClass[type] ?? 'badge--muted';
  }

  getBadgeLabel(type: string): string {
    return this.badgeLabel[type] ?? type;
  }
}
