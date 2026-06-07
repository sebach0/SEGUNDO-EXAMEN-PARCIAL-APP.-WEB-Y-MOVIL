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
import type { WorkshopSlaDetailDto, WorkshopSlaDto } from '../../../../core/models/admin-api.models';

@Component({
  selector: 'app-admin-sla',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, FormsModule],
  templateUrl: './admin-sla.component.html',
  styleUrl: './admin-sla.component.scss',
})
export class AdminSlaComponent implements OnInit {
  private readonly api = inject(AdminApiService);
  private readonly cdr = inject(ChangeDetectorRef);

  workshops: WorkshopSlaDto[] = [];
  detail: WorkshopSlaDetailDto | null = null;
  detailWorkshopId: number | null = null;

  loading = true;
  loadingDetail = false;
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
    this.detail = null;
    this.detailWorkshopId = null;
    this.cdr.markForCheck();

    const taller_id = this.tallerIdStr ? Number(this.tallerIdStr) : undefined;

    this.api
      .getSlaWorkshops({
        desde: this.desde || undefined,
        hasta: this.hasta || undefined,
        taller_id,
      })
      .subscribe({
        next: (data) => {
          this.workshops = data;
          this.loading = false;
          this.cdr.markForCheck();
        },
        error: () => {
          this.loading = false;
          this.error = 'No se pudo cargar el SLA. Verifica permisos (sla:leer).';
          this.cdr.markForCheck();
        },
      });
  }

  loadDetail(workshopId: number): void {
    if (this.detailWorkshopId === workshopId) {
      this.detail = null;
      this.detailWorkshopId = null;
      this.cdr.markForCheck();
      return;
    }
    this.loadingDetail = true;
    this.detailWorkshopId = workshopId;
    this.cdr.markForCheck();

    this.api
      .getSlaWorkshopDetail(workshopId, {
        desde: this.desde || undefined,
        hasta: this.hasta || undefined,
      })
      .subscribe({
        next: (d) => {
          this.detail = d;
          this.loadingDetail = false;
          this.cdr.markForCheck();
        },
        error: () => {
          this.loadingDetail = false;
          this.detail = null;
          this.cdr.markForCheck();
        },
      });
  }

  slaClass(pct: number | null | undefined): string {
    if (pct == null) return '';
    if (pct >= 90) return 'sla--green';
    if (pct >= 70) return 'sla--yellow';
    return 'sla--red';
  }

  formatPct(val: number | null | undefined): string {
    if (val == null) return '—';
    return `${val.toFixed(1)} %`;
  }

  formatMin(val: number | null | undefined): string {
    if (val == null) return '—';
    return `${val.toFixed(1)} min`;
  }

  formatDate(d: string | null | undefined): string {
    if (!d) return '—';
    return new Date(d).toLocaleString('es-BO');
  }

  clearFilters(): void {
    this.desde = '';
    this.hasta = '';
    this.tallerIdStr = '';
    this.load();
  }
}
