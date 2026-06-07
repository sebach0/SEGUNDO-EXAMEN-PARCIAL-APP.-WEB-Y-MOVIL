import { Component, inject, OnInit, ChangeDetectorRef, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CotizacionService } from '../../../../core/services/cotizacion.service';
import type { KpiSummary } from '../../../../core/models/cotizacion.models';

/**
 * OperationalDashboardComponent — Ciclo 4 Segunda Fase
 *
 * Ruta: /admin/panel/ciclo4/kpis
 *
 * Dashboard de KPIs operacionales conectado a GET /api/kpis/summary.
 * Sin datos hardcodeados — todos vienen de la base de datos.
 */
@Component({
  selector: 'app-operational-dashboard',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, FormsModule],
  templateUrl: './operational-dashboard.component.html',
  styleUrl: './operational-dashboard.component.scss',
})
export class OperationalDashboardComponent implements OnInit {
  private readonly cotSvc = inject(CotizacionService);
  private readonly cdr    = inject(ChangeDetectorRef);

  kpis: KpiSummary | null = null;
  loading = true;
  error: string | null = null;

  // Filtros
  desde = '';
  hasta = '';

  ngOnInit(): void {
    this.loadKpis();
  }

  loadKpis(): void {
    this.loading = true;
    this.error   = null;
    this.cdr.markForCheck();

    this.cotSvc.getKpiSummary({
      desde: this.desde || undefined,
      hasta: this.hasta || undefined,
    }).subscribe({
      next: (data) => {
        this.kpis    = data;
        this.loading = false;
        this.cdr.markForCheck();
      },
      error: () => {
        this.loading = false;
        this.error   = 'No se pudieron cargar los KPIs. Verifica tu sesión y permisos.';
        this.cdr.markForCheck();
      },
    });
  }

  formatMin(min: number | null | undefined): string {
    if (min == null) return '—';
    if (min < 60) return `${min.toFixed(1)} min`;
    return `${(min / 60).toFixed(1)} h`;
  }

  formatPct(pct: number | null | undefined): string {
    if (pct == null) return '—';
    return `${pct.toFixed(1)} %`;
  }

  incidentesPorTipoEntries(): { tipo: string; total: number }[] {
    if (!this.kpis?.incidentes_por_tipo) return [];
    return Object.entries(this.kpis.incidentes_por_tipo).map(([tipo, total]) => ({ tipo, total }));
  }
}
