import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { AdminApiService } from '../../../core/services/admin-api.service';
import type {
  AdminComisionSerieFila,
  AdminFinanzasReportes,
  AdminFinanzasResumen,
  BitacoraDto,
  TallerComisionFila,
} from '../../../core/models/admin-api.models';

@Component({
  selector: 'app-admin-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './admin-dashboard.component.html',
  styleUrl: './admin-dashboard.component.scss',
})
export class AdminDashboardComponent implements OnInit {
  private readonly api = inject(AdminApiService);

  totalUsuarios = 0;
  totalTalleres = 0;
  totalRoles = 0;
  actividad: BitacoraDto[] = [];
  finanzas: AdminFinanzasResumen | null = null;
  topTalleres: TallerComisionFila[] = [];
  serieComisiones: AdminComisionSerieFila[] = [];
  desde = '';
  hasta = '';
  loading = true;
  loadingFinanzas = true;
  error: string | null = null;
  finanzasError: string | null = null;

  readonly quick = [
    { path: '/admin/panel/usuarios', label: 'Usuarios' },
    { path: '/admin/panel/roles', label: 'Roles' },
    { path: '/admin/panel/permisos', label: 'Permisos' },
    { path: '/admin/panel/talleres', label: 'Talleres' },
    { path: '/admin/panel/bitacora', label: 'Bitácora' },
  ] as const;

  ngOnInit(): void {
    const now = new Date();
    const prev = new Date();
    prev.setDate(now.getDate() - 30);
    this.desde = this.toDateInput(prev);
    this.hasta = this.toDateInput(now);
    this.loadPanel();
  }

  recargarFinanzas(): void {
    this.loadFinanzas();
  }

  totalComisionSerie(): number {
    return this.serieComisiones.reduce((acc, x) => acc + this.toNumber(x.total_comision_plataforma), 0);
  }

  maxComisionSerie(): number {
    return this.serieComisiones.reduce((max, x) => {
      const value = this.toNumber(x.total_comision_plataforma);
      return value > max ? value : max;
    }, 0);
  }

  barWidthPercent(value: string): number {
    const max = this.maxComisionSerie();
    if (max <= 0) return 0;
    return Math.max(4, Math.round((this.toNumber(value) / max) * 100));
  }

  money(value: string | number | null | undefined): string {
    return new Intl.NumberFormat('es-BO', {
      style: 'currency',
      currency: 'BOB',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(this.toNumber(value));
  }

  pct(value: string | number | null | undefined): string {
    return `${this.toNumber(value).toFixed(2)}%`;
  }

  private loadPanel(): void {
    this.loading = true;
    forkJoin({
      usuarios: this.api.listUsuarios().pipe(catchError(() => of([]))),
      talleres: this.api.listTalleres().pipe(catchError(() => of([]))),
      roles: this.api.listRoles().pipe(catchError(() => of([]))),
      bitacora: this.api.listBitacora({ limit: 8, offset: 0 }).pipe(catchError(() => of([]))),
    }).subscribe({
      next: ({ usuarios, talleres, roles, bitacora }) => {
        this.totalUsuarios = usuarios.length;
        this.totalTalleres = talleres.length;
        this.totalRoles = roles.length;
        this.actividad = bitacora;
        this.loading = false;
        this.error = null;
      },
      error: () => {
        this.loading = false;
        this.error = 'No se pudieron cargar los datos del panel.';
      },
    });
    this.loadFinanzas();
  }

  private loadFinanzas(): void {
    this.loadingFinanzas = true;
    this.finanzasError = null;
    const filters = this.dateFilters();
    forkJoin({
      resumen: this.api.getFinanzasResumen(filters).pipe(catchError(() => of(null))),
      reportes: this.api.getFinanzasReportes(filters).pipe(catchError(() => of(null))),
    }).subscribe({
      next: ({ resumen, reportes }) => {
        const data = this.resolveReportData(resumen, reportes);
        this.finanzas = data?.resumen ?? resumen;
        this.topTalleres = data?.top_talleres ?? this.finanzas?.por_taller?.slice(0, 5) ?? [];
        this.serieComisiones = data?.serie_diaria ?? [];
        this.loadingFinanzas = false;
        if (!this.finanzas) {
          this.finanzasError = 'No se pudieron cargar las métricas financieras.';
        }
      },
      error: () => {
        this.loadingFinanzas = false;
        this.finanzasError = 'No se pudieron cargar las métricas financieras.';
      },
    });
  }

  private resolveReportData(
    resumen: AdminFinanzasResumen | null,
    reportes: AdminFinanzasReportes | null
  ): AdminFinanzasReportes | null {
    if (reportes?.resumen) return reportes;
    if (!resumen) return null;
    return { resumen, top_talleres: resumen.por_taller.slice(0, 5), serie_diaria: [] };
  }

  private dateFilters(): { desde?: string; hasta?: string } {
    const filters: { desde?: string; hasta?: string } = {};
    if (this.desde) filters.desde = `${this.desde}T00:00:00`;
    if (this.hasta) filters.hasta = `${this.hasta}T23:59:59`;
    return filters;
  }

  private toDateInput(date: Date): string {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
  }

  private toNumber(value: string | number | null | undefined): number {
    if (typeof value === 'number') return value;
    if (!value) return 0;
    const n = Number(value);
    return Number.isFinite(n) ? n : 0;
  }
}
