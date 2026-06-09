import {
  Component,
  inject,
  OnInit,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AdminApiService } from '../../../core/services/admin-api.service';
import { CotizacionService } from '../../../core/services/cotizacion.service';
import type { AdminDashboardKpisDto } from '../../../core/models/admin-api.models';
import type { KpiSummary } from '../../../core/models/cotizacion.models';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';

@Component({
  selector: 'app-admin-kpis-unified',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, FormsModule],
  templateUrl: './admin-kpis-unified.component.html',
  styleUrl: './admin-kpis-unified.component.scss',
})
export class AdminKpisUnifiedComponent implements OnInit {
  private readonly api    = inject(AdminApiService);
  private readonly cotSvc = inject(CotizacionService);
  private readonly cdr    = inject(ChangeDetectorRef);

  desde      = '';
  hasta      = '';
  tallerIdStr = '';

  loading    = true;
  error: string | null = null;

  kpisOp:  KpiSummary | null          = null;
  kpisAdv: AdminDashboardKpisDto | null = null;

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading = true;
    this.error   = null;
    this.cdr.markForCheck();

    const taller_id = this.tallerIdStr ? Number(this.tallerIdStr) : undefined;

    forkJoin({
      op:  this.cotSvc.getKpiSummary({ desde: this.desde || undefined, hasta: this.hasta || undefined })
             .pipe(catchError(() => of(null))),
      adv: this.api.getAdminDashboardKpis({ desde: this.desde || undefined, hasta: this.hasta || undefined, taller_id })
             .pipe(catchError(() => of(null))),
    }).subscribe({
      next: ({ op, adv }) => {
        this.kpisOp  = op;
        this.kpisAdv = adv;
        this.loading = false;
        if (!op && !adv) this.error = 'No se pudieron cargar los KPIs. Verifica tu sesión y permisos.';
        this.cdr.markForCheck();
      },
      error: () => {
        this.loading = false;
        this.error = 'Error al cargar los KPIs.';
        this.cdr.markForCheck();
      },
    });
  }

  clearFilters(): void {
    this.desde       = '';
    this.hasta       = '';
    this.tallerIdStr = '';
    this.load();
  }

  formatMin(val: number | null | undefined): string {
    if (val == null) return '—';
    if (val < 60) return `${val.toFixed(1)} min`;
    return `${(val / 60).toFixed(1)} h`;
  }

  formatPct(val: number | null | undefined): string {
    if (val == null) return '—';
    return `${val.toFixed(1)} %`;
  }

  slaClass(pct: number | null | undefined): string {
    if (pct == null) return '';
    if (pct >= 90) return 'ukpi__card--green';
    if (pct >= 70) return 'ukpi__card--yellow';
    return 'ukpi__card--red';
  }

  opTipoEntries(): { tipo: string; total: number }[] {
    if (!this.kpisOp?.incidentes_por_tipo) return [];
    return Object.entries(this.kpisOp.incidentes_por_tipo).map(([tipo, total]) => ({ tipo, total }));
  }
}
