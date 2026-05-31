import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { TallerApiService } from '../../../core/services/taller-api.service';
import { TallerEmergenciasApiService } from '../../../core/services/taller-emergencias-api.service';
import { TallerAuthService } from '../../../core/services/taller-auth.service';
import type { TallerDashboardDto } from '../../../core/models/taller-api.models';
import type { ReporteTallerDashboardDto } from '../../../core/models/taller-emergencias.models';

function toIsoDateLocal(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

@Component({
  selector: 'app-taller-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  templateUrl: './taller-dashboard.component.html',
  styleUrl: './taller-dashboard.component.scss',
})
export class TallerDashboardComponent implements OnInit {
  private readonly api = inject(TallerApiService);
  private readonly emergenciasApi = inject(TallerEmergenciasApiService);
  readonly auth = inject(TallerAuthService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  data: TallerDashboardDto | null = null;
  loading = true;
  error: string | null = null;
  permisoDenegado: string | null = null;

  reporte: ReporteTallerDashboardDto | null = null;
  reporteLoading = false;
  reporteError: string | null = null;
  estadosReporte: { label: string; n: number }[] = [];

  /** Filtro de periodo para el reporte (comisiones por `calculado_at`, solicitudes por `created_at`). */
  desdeStr = '';
  hastaStr = '';

  ngOnInit(): void {
    this.route.queryParamMap.subscribe((q) => {
      if (q.get('denegado') === '1') {
        this.permisoDenegado =
          'No tenés permiso para acceder a esa sección. Si necesitás emergencias en el panel, pedí que te asignen los permisos correspondientes.';
        void this.router.navigate([], { relativeTo: this.route, queryParams: {}, replaceUrl: true });
      }
    });

    const hasta = new Date();
    const desde = new Date();
    desde.setDate(desde.getDate() - 30);
    this.desdeStr = toIsoDateLocal(desde);
    this.hastaStr = toIsoDateLocal(hasta);

    this.api.getDashboard().subscribe({
      next: (d) => {
        this.data = d;
        this.loading = false;
        if (this.puedeVerReportesFinancieros()) {
          this.cargarReporte();
        }
      },
      error: () => {
        this.loading = false;
        this.error = 'No se pudo cargar el resumen del taller.';
      },
    });
  }

  cargarReporte(): void {
    if (!this.puedeVerReportesFinancieros()) return;
    this.reporteLoading = true;
    this.reporteError = null;
    this.emergenciasApi
      .getReporteDashboard({
        desde: this.desdeStr || undefined,
        hasta: this.hastaStr || undefined,
      })
      .subscribe({
        next: (r) => {
          this.reporte = r;
          this.estadoChipsDe(r);
          this.reporteLoading = false;
        },
        error: (e: { status?: number }) => {
          this.reporteLoading = false;
          if (e?.status === 403) {
            this.reporteError = 'Tu rol no incluye permiso para ver reportes financieros (`comisiones:leer`).';
          } else {
            this.reporteError = 'No se pudo cargar el reporte inteligente del taller.';
          }
        },
      });
  }

  /** Misma regla que `TallerShellComponent.nav`: sin lista de permisos → se muestran todos los enlaces. */
  puedeVerSolicitudesEmergencias(): boolean {
    const p = this.auth.getMe()?.permisos;
    if (!p?.length) return true;
    return p.includes('solicitudes_taller:leer');
  }

  puedeGestionarDisponibilidadEmergencias(): boolean {
    const p = this.auth.getMe()?.permisos;
    if (!p?.length) return true;
    return p.includes('disponibilidad:gestionar');
  }

  puedeVerReportesFinancieros(): boolean {
    const p = this.auth.getMe()?.permisos;
    if (!p?.length) return true;
    return p.includes('comisiones:leer');
  }

  parseDecimal(s: string): number {
    const n = Number(s);
    return Number.isFinite(n) ? n : 0;
  }

  formatoMoneda(val: string | number): string {
    const n = typeof val === 'string' ? this.parseDecimal(val) : val;
    return new Intl.NumberFormat('es-BO', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(n);
  }

  private estadoChipsDe(r: ReporteTallerDashboardDto): void {
    const order = [
      'REGISTRADA',
      'EN_REVISION',
      'TALLER_ASIGNADO',
      'TECNICO_ASIGNADO',
      'EN_CAMINO',
      'EN_ATENCION',
      'FINALIZADA',
      'CANCELADA',
    ];
    const map = r.solicitudes_por_estado ?? {};
    const labels: Record<string, string> = {
      REGISTRADA: 'Registrada',
      EN_REVISION: 'En revisión',
      TALLER_ASIGNADO: 'Taller asignado',
      TECNICO_ASIGNADO: 'Técnico asignado',
      EN_CAMINO: 'En camino',
      EN_ATENCION: 'En atención',
      FINALIZADA: 'Finalizada',
      CANCELADA: 'Cancelada',
    };
    const entries = Object.entries(map).filter(([, n]) => n > 0);
    entries.sort((a, b) => order.indexOf(a[0]) - order.indexOf(b[0]));
    this.estadosReporte = entries.map(([k, n]) => ({ label: labels[k] ?? k, n }));
  }
}
