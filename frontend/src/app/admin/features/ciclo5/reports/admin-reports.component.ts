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
import type {
  IncidentReportReadDto,
  PerformanceReportReadDto,
  WorkshopReportReadDto,
} from '../../../../core/models/admin-api.models';

type ReportTab = 'incidentes' | 'performance' | 'talleres';

@Component({
  selector: 'app-admin-reports',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, FormsModule],
  templateUrl: './admin-reports.component.html',
  styleUrl: './admin-reports.component.scss',
})
export class AdminReportsComponent implements OnInit {
  private readonly api = inject(AdminApiService);
  private readonly cdr = inject(ChangeDetectorRef);

  activeTab: ReportTab = 'incidentes';

  // Filtros
  desde = '';
  hasta = '';
  estado = '';

  loading = false;
  error: string | null = null;
  exportBusy = false;

  incidents: IncidentReportReadDto | null = null;
  performance: PerformanceReportReadDto | null = null;
  workshops: WorkshopReportReadDto | null = null;

  readonly estadoOpts = [
    { value: '', label: 'Todos' },
    { value: 'REGISTRADA', label: 'Registrada' },
    { value: 'EN_REVISION', label: 'En revisión' },
    { value: 'TALLER_ASIGNADO', label: 'Taller asignado' },
    { value: 'EN_CAMINO', label: 'En camino' },
    { value: 'EN_ATENCION', label: 'En atención' },
    { value: 'FINALIZADA', label: 'Finalizada' },
    { value: 'CANCELADA', label: 'Cancelada' },
  ];

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading = true;
    this.error = null;
    this.cdr.markForCheck();

    const filters = {
      desde: this.desde || undefined,
      hasta: this.hasta || undefined,
      estado: this.estado || undefined,
    };

    if (this.activeTab === 'incidentes') {
      this.api.getIncidentsReport(filters).subscribe({
        next: (d) => { this.incidents = d; this.loading = false; this.cdr.markForCheck(); },
        error: () => { this.loading = false; this.error = 'No se pudo generar el reporte.'; this.cdr.markForCheck(); },
      });
    } else if (this.activeTab === 'performance') {
      this.api.getPerformanceReport(filters).subscribe({
        next: (d) => { this.performance = d; this.loading = false; this.cdr.markForCheck(); },
        error: () => { this.loading = false; this.error = 'No se pudo generar el reporte.'; this.cdr.markForCheck(); },
      });
    } else {
      this.api.getWorkshopsReport(filters).subscribe({
        next: (d) => { this.workshops = d; this.loading = false; this.cdr.markForCheck(); },
        error: () => { this.loading = false; this.error = 'No se pudo generar el reporte.'; this.cdr.markForCheck(); },
      });
    }
  }

  setTab(tab: ReportTab): void {
    this.activeTab = tab;
    this.load();
  }

  exportCsv(): void {
    this.exportBusy = true;
    this.api
      .exportReportCsv({
        desde: this.desde || undefined,
        hasta: this.hasta || undefined,
        estado: this.estado || undefined,
      })
      .subscribe({
        next: (blob) => {
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `reporte-incidentes-${new Date().toISOString().slice(0, 10)}.csv`;
          a.click();
          URL.revokeObjectURL(url);
          this.exportBusy = false;
          this.cdr.markForCheck();
        },
        error: () => {
          this.exportBusy = false;
          this.error = 'No se pudo exportar el CSV.';
          this.cdr.markForCheck();
        },
      });
  }

  formatMin(val: number | null | undefined): string {
    if (val == null) return '—';
    return `${val.toFixed(1)} min`;
  }

  formatPct(val: number | null | undefined): string {
    if (val == null) return '—';
    return `${val.toFixed(1)} %`;
  }

  formatDate(d: string | null | undefined): string {
    if (!d) return '—';
    return new Date(d).toLocaleDateString('es-BO');
  }

  slaLabel(val: boolean | null | undefined): string {
    if (val == null) return '—';
    return val ? '✓' : '✗';
  }

  clearFilters(): void {
    this.desde = '';
    this.hasta = '';
    this.estado = '';
    this.load();
  }
}
