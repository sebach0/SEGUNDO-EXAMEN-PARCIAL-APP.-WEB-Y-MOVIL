import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { TallerEmergenciasApiService } from '../../../../core/services/taller-emergencias-api.service';
import type { BandejaIncidenteBaseDto, EstadoSolicitudSeguimiento } from '../../../../core/models/taller-emergencias.models';

@Component({
  selector: 'app-taller-emergencias-bandeja',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './taller-emergencias-bandeja.component.html',
  styleUrl: './taller-emergencias-bandeja.component.scss',
})
export class TallerEmergenciasBandejaComponent implements OnInit {
  private readonly api = inject(TallerEmergenciasApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  rows: BandejaIncidenteBaseDto[] = [];
  search = '';
  estadoSolicitud: EstadoSolicitudSeguimiento | '' = '';
  loading = true;
  error: string | null = null;
  successFlash: string | null = null;

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
    this.route.queryParamMap.subscribe((q) => {
      const ok = q.get('ok');
      if (ok === 'aceptada') {
        this.successFlash = 'Solicitud aceptada correctamente.';
        void this.router.navigate([], { relativeTo: this.route, queryParams: {}, replaceUrl: true });
      } else if (ok === 'rechazada') {
        this.successFlash = 'Solicitud rechazada.';
        void this.router.navigate([], { relativeTo: this.route, queryParams: {}, replaceUrl: true });
      }
    });
    this.reload();
  }

  reload(): void {
    this.loading = true;
    this.error = null;
    this.api.listBandejaDisponibles().subscribe({
      next: (list) => {
        this.rows = list;
        this.loading = false;
      },
      error: (err) => {
        this.loading = false;
        this.error = this.msg(err, 'No se pudo cargar la bandeja de solicitudes.');
      },
    });
  }

  dismissFlash(): void {
    this.successFlash = null;
  }

  get filtered(): BandejaIncidenteBaseDto[] {
    let r = this.rows;
    if (this.estadoSolicitud) {
      r = r.filter((x) => x.estado_solicitud === this.estadoSolicitud);
    }
    const q = this.search.trim().toLowerCase();
    if (!q) return r;
    return r.filter(
      (x) =>
        x.placa.toLowerCase().includes(q) ||
        `${x.nombres} ${x.apellidos}`.toLowerCase().includes(q) ||
        (x.marca && x.marca.toLowerCase().includes(q)) ||
        (x.modelo && x.modelo.toLowerCase().includes(q)) ||
        String(x.solicitud_id).includes(q),
    );
  }

  private msg(err: { error?: { detail?: unknown } }, fallback: string): string {
    const d = err?.error?.detail;
    if (typeof d === 'string') return d;
    if (Array.isArray(d) && d.length && typeof d[0] === 'object' && d[0] !== null && 'msg' in d[0]) {
      return String((d[0] as { msg: string }).msg);
    }
    return fallback;
  }

  /** Código de prioridad (p. ej. ALTA); usa `nivel_prioridad` o `ai_payload.prioridad` como respaldo. */
  private prioridadCodigo(r: BandejaIncidenteBaseDto): string | null {
    if (r.nivel_prioridad) return r.nivel_prioridad;
    const p = r.ai_payload?.['prioridad'];
    if (p && typeof p === 'object' && 'nivel_prioridad' in p) {
      const n = (p as { nivel_prioridad?: unknown }).nivel_prioridad;
      if (typeof n === 'string') return n;
    }
    return null;
  }

  prioridadTexto(r: BandejaIncidenteBaseDto): string | null {
    const c = this.prioridadCodigo(r);
    if (!c) return null;
    const m: Record<string, string> = {
      ALTA: 'Alta',
      MEDIA: 'Media',
      BAJA: 'Baja',
      REVISION_MANUAL: 'Revisión manual',
    };
    return m[c] ?? c;
  }

  prioridadPillClass(r: BandejaIncidenteBaseDto): string {
    const c = this.prioridadCodigo(r);
    if (c === 'ALTA') return 'emg__pill--pri-alta';
    if (c === 'MEDIA') return 'emg__pill--pri-media';
    if (c === 'BAJA') return 'emg__pill--pri-baja';
    if (c === 'REVISION_MANUAL') return 'emg__pill--pri-revision';
    return 'emg__pill--pri-unknown';
  }
}
