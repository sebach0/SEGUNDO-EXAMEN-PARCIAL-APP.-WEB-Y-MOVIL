import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { AdminApiService } from '../../../core/services/admin-api.service';
import type {
  AdminComisionSerieFila,
  AdminFinanzasReportes,
  AdminFinanzasResumen,
  TallerComisionFila,
} from '../../../core/models/admin-api.models';

@Component({
  selector: 'app-admin-finanzas',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './admin-finanzas.component.html',
  styleUrl: './admin-finanzas.component.scss',
})
export class AdminFinanzasComponent implements OnInit {
  private readonly api = inject(AdminApiService);

  finanzas: AdminFinanzasResumen | null = null;
  topTalleres: TallerComisionFila[] = [];
  serieComisiones: AdminComisionSerieFila[] = [];
  desde = '';
  hasta = '';
  loading = false;
  error: string | null = null;

  ngOnInit(): void {
    const now = new Date();
    const prev = new Date();
    prev.setDate(now.getDate() - 30);
    this.desde = this.toDateInput(prev);
    this.hasta = this.toDateInput(now);
    this.load();
  }

  load(): void {
    this.loading = true;
    this.error = null;
    const filters = this.dateFilters();
    forkJoin({
      resumen: this.api.getFinanzasResumen(filters).pipe(catchError(() => of(null))),
      reportes: this.api.getFinanzasReportes(filters).pipe(catchError(() => of(null))),
    }).subscribe({
      next: ({ resumen, reportes }) => {
        const data = this.resolve(resumen, reportes);
        this.finanzas = data?.resumen ?? resumen;
        this.topTalleres = data?.top_talleres ?? this.finanzas?.por_taller?.slice(0, 10) ?? [];
        this.serieComisiones = data?.serie_diaria ?? [];
        this.loading = false;
        if (!this.finanzas) {
          this.error = 'No se pudieron cargar las métricas financieras.';
        }
      },
      error: () => {
        this.loading = false;
        this.error = 'No se pudieron cargar las métricas financieras.';
      },
    });
  }

  totalComisionSerie(): number {
    return this.serieComisiones.reduce((acc, x) => acc + this.toNum(x.total_comision_plataforma), 0);
  }

  maxComisionSerie(): number {
    return this.serieComisiones.reduce((max, x) => {
      const v = this.toNum(x.total_comision_plataforma);
      return v > max ? v : max;
    }, 0);
  }

  barWidthPercent(value: string): number {
    const max = this.maxComisionSerie();
    if (max <= 0) return 0;
    return Math.max(4, Math.round((this.toNum(value) / max) * 100));
  }

  tallerBarWidth(value: string): number {
    const max = this.topTalleres.reduce((m, t) => {
      const v = this.toNum(t.total_comision_plataforma);
      return v > m ? v : m;
    }, 0);
    if (max <= 0) return 0;
    return Math.max(4, Math.round((this.toNum(value) / max) * 100));
  }

  money(value: string | number | null | undefined): string {
    return new Intl.NumberFormat('es-BO', {
      style: 'currency',
      currency: 'BOB',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(this.toNum(value));
  }

  pct(value: string | number | null | undefined): string {
    return `${this.toNum(value).toFixed(2)}%`;
  }

  private resolve(
    resumen: AdminFinanzasResumen | null,
    reportes: AdminFinanzasReportes | null,
  ): AdminFinanzasReportes | null {
    if (reportes?.resumen) return reportes;
    if (!resumen) return null;
    return { resumen, top_talleres: resumen.por_taller.slice(0, 10), serie_diaria: [] };
  }

  private dateFilters(): { desde?: string; hasta?: string } {
    const f: { desde?: string; hasta?: string } = {};
    if (this.desde) f.desde = `${this.desde}T00:00:00`;
    if (this.hasta) f.hasta = `${this.hasta}T23:59:59`;
    return f;
  }

  private toDateInput(date: Date): string {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
  }

  private toNum(value: string | number | null | undefined): number {
    if (typeof value === 'number') return value;
    if (!value) return 0;
    const n = Number(value);
    return Number.isFinite(n) ? n : 0;
  }
}
