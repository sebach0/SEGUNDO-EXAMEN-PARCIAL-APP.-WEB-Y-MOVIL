import { Component, NgZone, OnDestroy, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { Subject, interval } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { TallerEmergenciasApiService } from '../../../../core/services/taller-emergencias-api.service';
import { TallerApiService } from '../../../../core/services/taller-api.service';
import { TallerAuthService } from '../../../../core/services/taller-auth.service';
import type { EstadoSolicitudSeguimiento, HistorialAtencionDto } from '../../../../core/models/taller-emergencias.models';
import type { TecnicoPortalDto } from '../../../../core/models/taller-api.models';

type HistorialModo = 'mis' | 'historial' | 'servicios';

@Component({
  selector: 'app-taller-emergencias-historial-list',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './taller-emergencias-historial-list.component.html',
  styleUrl: './taller-emergencias-historial-list.component.scss',
})
export class TallerEmergenciasHistorialListComponent implements OnInit, OnDestroy {
  private readonly api = inject(TallerEmergenciasApiService);
  private readonly tallerApi = inject(TallerApiService);
  private readonly auth = inject(TallerAuthService);
  private readonly route = inject(ActivatedRoute);
  private readonly zone = inject(NgZone);
  private readonly destroy$ = new Subject<void>();
  private ws: WebSocket | null = null;

  modo: HistorialModo = 'historial';
  rows: HistorialAtencionDto[] = [];
  tecnicos: TecnicoPortalDto[] = [];
  search = '';
  loading = true;
  error: string | null = null;

  /** Solo modo `historial`: filtro en servidor. */
  estado: EstadoSolicitudSeguimiento | '' = '';
  desde = '';
  hasta = '';

  readonly estados: EstadoSolicitudSeguimiento[] = [
    'REGISTRADA',
    'EN_REVISION',
    'TALLER_ASIGNADO',
    'TECNICO_ASIGNADO',
    'EN_CAMINO',
    'EN_ATENCION',
    'FINALIZADA',
    'CANCELADA',
  ];

  ngOnInit(): void {
    const m = this.route.snapshot.data['historialModo'];
    this.modo = m === 'mis' || m === 'servicios' ? m : 'historial';
    this.tallerApi.listTecnicos().subscribe({
      next: (list) => { this.tecnicos = list; },
      error: () => { this.tecnicos = []; },
    });
    this.reload();
    this._connectTallerFeed();
    interval(30_000).pipe(takeUntil(this.destroy$)).subscribe(() => this._silentReload());
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    if (this.ws) { this.ws.onclose = null; this.ws.close(); this.ws = null; }
  }

  private _connectTallerFeed(): void {
    const token = this.auth.getAccessToken() ?? '';
    const baseWs = window.location.origin.replace(/^http/, 'ws');
    const url = `${baseWs}/api/ws/taller/feed?token=${token}`;
    this.zone.runOutsideAngular(() => {
      const ws = new WebSocket(url);
      this.ws = ws;
      ws.onmessage = () => this.zone.run(() => this._silentReload());
      ws.onclose = () => {
        if (!this.destroy$.closed) {
          setTimeout(() => this._connectTallerFeed(), 5_000);
        }
      };
    });
  }

  private _silentReload(): void {
    const params =
      this.modo === 'historial'
        ? {
            estado: this.estado || undefined,
            desde: this.desde || undefined,
            hasta: this.hasta || undefined,
          }
        : undefined;
    this.api.listHistorialAtenciones(params).subscribe({
      next: (list) => { this.rows = list; },
      error: () => {},
    });
  }

  titulo(): string {
    if (this.modo === 'mis') return 'Mis solicitudes';
    if (this.modo === 'servicios') return 'Servicios asignados';
    return 'Historial de atenciones';
  }

  subtitulo(): string {
    if (this.modo === 'mis') {
      return 'Solicitudes de tu taller en curso o recientes. Las que ya no están en la bandeja «disponibles» aparecen aquí.';
    }
    if (this.modo === 'servicios') {
      return 'Solicitudes con técnico asignado (seguimiento operativo).';
    }
    return 'Consulta completa con filtros por estado y fechas de registro.';
  }

  reload(): void {
    this.loading = true;
    this.error = null;
    const params =
      this.modo === 'historial'
        ? {
            estado: this.estado || undefined,
            desde: this.desde || undefined,
            hasta: this.hasta || undefined,
          }
        : undefined;
    this.api.listHistorialAtenciones(params).subscribe({
      next: (list) => {
        this.rows = list;
        this.loading = false;
      },
      error: (err) => {
        this.loading = false;
        this.error = this.msg(err, 'No se pudo cargar el historial.');
      },
    });
  }

  private porModo(r: HistorialAtencionDto[]): HistorialAtencionDto[] {
    if (this.modo === 'mis') {
      return r.filter((x) => x.estado !== 'FINALIZADA' && x.estado !== 'CANCELADA');
    }
    if (this.modo === 'servicios') {
      return r.filter((x) => x.tecnico_id != null);
    }
    return r;
  }

  get filtered(): HistorialAtencionDto[] {
    let r = this.porModo(this.rows);
    const q = this.search.trim().toLowerCase();
    if (q) {
      r = r.filter(
        (x) =>
          x.placa.toLowerCase().includes(q) ||
          `${x.nombres} ${x.apellidos}`.toLowerCase().includes(q) ||
          (x.marca && x.marca.toLowerCase().includes(q)) ||
          (x.modelo && x.modelo.toLowerCase().includes(q)) ||
          String(x.solicitud_id).includes(q) ||
          (x.tecnico_id != null && String(x.tecnico_id).includes(q)),
      );
    }
    return r;
  }

  nombreTecnico(id: number | null | undefined): string {
    if (id == null) return '—';
    const t = this.tecnicos.find((x) => x.id === id);
    return t ? `${t.nombres} ${t.apellidos}`.trim() : `ID ${id}`;
  }

  linkDetalle(r: HistorialAtencionDto): string[] | null {
    if (r.bandeja_id == null) return null;
    return ['/taller/panel/emergencias/solicitudes', String(r.bandeja_id)];
  }

  estadoUi(e: string): string {
    const m: Record<string, string> = {
      REGISTRADA: 'Registrada',
      EN_REVISION: 'En revisión',
      TALLER_ASIGNADO: 'Taller asignado',
      TECNICO_ASIGNADO: 'Técnico asignado',
      EN_CAMINO: 'En camino',
      EN_ATENCION: 'En atención',
      FINALIZADA: 'Finalizada',
      CANCELADA: 'Cancelada',
    };
    return m[e] ?? e;
  }

  private msg(err: { error?: { detail?: unknown } }, fallback: string): string {
    const d = err?.error?.detail;
    if (typeof d === 'string') return d;
    if (Array.isArray(d) && d.length && typeof d[0] === 'object' && d[0] !== null && 'msg' in d[0]) {
      return String((d[0] as { msg: string }).msg);
    }
    return fallback;
  }
}
