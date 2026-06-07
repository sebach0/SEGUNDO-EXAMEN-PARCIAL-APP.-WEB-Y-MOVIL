import {
  Component,
  inject,
  OnInit,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AdminApiService } from '../../../../core/services/admin-api.service';
import type { AdminDashboardKpisDto } from '../../../../core/models/admin-api.models';

@Component({
  selector: 'app-admin-kpis-dashboard',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, FormsModule],
  templateUrl: './admin-kpis-dashboard.component.html',
  styleUrl: './admin-kpis-dashboard.component.scss',
})
export class AdminKpisDashboardComponent implements OnInit {
  private readonly api = inject(AdminApiService);
  private readonly cdr = inject(ChangeDetectorRef);

  kpis: AdminDashboardKpisDto | null = null;
  loading = true;
  error: string | null = null;

  // Filtros
  desde = '';
  hasta = '';
  tallerIdStr = '';

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading = true;
    this.error = null;
    this.cdr.markForCheck();

    const taller_id = this.tallerIdStr ? Number(this.tallerIdStr) : undefined;

    this.api
      .getAdminDashboardKpis({
        desde: this.desde || undefined,
        hasta: this.hasta || undefined,
        taller_id,
      })
      .subscribe({
        next: (data) => {
          this.kpis = data;
          this.loading = false;
          this.cdr.markForCheck();
        },
        error: () => {
          this.loading = false;
          this.error = 'No se pudieron cargar los KPIs. Verifica permisos (kpis:leer).';
          this.cdr.markForCheck();
        },
      });
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

  slaColor(pct: number | null | undefined): string {
    if (pct == null) return '';
    if (pct >= 90) return 'kpi--green';
    if (pct >= 70) return 'kpi--yellow';
    return 'kpi--red';
  }

  clearFilters(): void {
    this.desde = '';
    this.hasta = '';
    this.tallerIdStr = '';
    this.load();
  }
}
