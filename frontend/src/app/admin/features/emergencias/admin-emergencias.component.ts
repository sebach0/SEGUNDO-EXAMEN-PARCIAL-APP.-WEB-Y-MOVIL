import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnInit,
  inject,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AdminApiService } from '../../../core/services/admin-api.service';
import type { EmergenciaAdminDto, EstadoEmergencia } from '../../../core/models/admin-api.models';

type TabFilter = 'todas' | 'nuevas' | 'en_proceso' | 'finalizadas' | 'canceladas';

const ESTADOS_NUEVAS: EstadoEmergencia[] = ['REGISTRADA', 'EN_REVISION'];
const ESTADOS_EN_PROCESO: EstadoEmergencia[] = [
  'TALLER_ASIGNADO', 'TECNICO_ASIGNADO', 'EN_CAMINO', 'EN_ATENCION',
];

@Component({
  selector: 'app-admin-emergencias',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, FormsModule],
  templateUrl: './admin-emergencias.component.html',
  styleUrl: './admin-emergencias.component.scss',
})
export class AdminEmergenciasComponent implements OnInit {
  private readonly api = inject(AdminApiService);
  private readonly cdr = inject(ChangeDetectorRef);

  all: EmergenciaAdminDto[] = [];
  loading = true;
  error: string | null = null;

  activeTab: TabFilter = 'todas';
  search = '';

  ngOnInit(): void {
    this.reload();
  }

  reload(): void {
    this.loading = true;
    this.error = null;
    this.api.listAdminEmergencias().subscribe({
      next: (data) => {
        this.all = data;
        this.loading = false;
        this.cdr.markForCheck();
      },
      error: () => {
        this.loading = false;
        this.error = 'No se pudieron cargar las emergencias.';
        this.cdr.markForCheck();
      },
    });
  }

  setTab(tab: TabFilter): void {
    this.activeTab = tab;
    this.search = '';
    this.cdr.markForCheck();
  }

  get filtered(): EmergenciaAdminDto[] {
    let rows = this.all;

    switch (this.activeTab) {
      case 'nuevas':
        rows = rows.filter((e) => ESTADOS_NUEVAS.includes(e.estado));
        break;
      case 'en_proceso':
        rows = rows.filter((e) => ESTADOS_EN_PROCESO.includes(e.estado));
        break;
      case 'finalizadas':
        rows = rows.filter((e) => e.estado === 'FINALIZADA');
        break;
      case 'canceladas':
        rows = rows.filter((e) => e.estado === 'CANCELADA');
        break;
    }

    const q = this.search.trim().toLowerCase();
    if (q) {
      rows = rows.filter(
        (e) =>
          String(e.id).includes(q) ||
          (e.cliente_nombre ?? '').toLowerCase().includes(q) ||
          (e.taller_nombre ?? '').toLowerCase().includes(q) ||
          (e.descripcion_texto ?? '').toLowerCase().includes(q),
      );
    }
    return rows;
  }

  count(tab: TabFilter): number {
    switch (tab) {
      case 'nuevas': return this.all.filter((e) => ESTADOS_NUEVAS.includes(e.estado)).length;
      case 'en_proceso': return this.all.filter((e) => ESTADOS_EN_PROCESO.includes(e.estado)).length;
      case 'finalizadas': return this.all.filter((e) => e.estado === 'FINALIZADA').length;
      case 'canceladas': return this.all.filter((e) => e.estado === 'CANCELADA').length;
      default: return this.all.length;
    }
  }

  estadoLabel(estado: EstadoEmergencia): string {
    const MAP: Record<EstadoEmergencia, string> = {
      REGISTRADA: 'Registrada',
      EN_REVISION: 'En revisión',
      TALLER_ASIGNADO: 'Taller asignado',
      TECNICO_ASIGNADO: 'Técnico asignado',
      EN_CAMINO: 'En camino',
      EN_ATENCION: 'En atención',
      FINALIZADA: 'Finalizada',
      CANCELADA: 'Cancelada',
    };
    return MAP[estado] ?? estado;
  }

  estadoBadgeClass(estado: EstadoEmergencia): string {
    if (ESTADOS_NUEVAS.includes(estado)) return 'badge--nueva';
    if (ESTADOS_EN_PROCESO.includes(estado)) return 'badge--proceso';
    if (estado === 'FINALIZADA') return 'badge--finalizada';
    if (estado === 'CANCELADA') return 'badge--cancelada';
    return '';
  }
}
