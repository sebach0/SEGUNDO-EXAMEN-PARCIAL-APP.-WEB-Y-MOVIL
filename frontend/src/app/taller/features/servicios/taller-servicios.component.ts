import {
  Component,
  inject,
  OnInit,
  signal,
  computed,
  ChangeDetectionStrategy,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CotizacionService } from '../../../core/services/cotizacion.service';
import { TallerApiService } from '../../../core/services/taller-api.service';
import type { ServicioCatalogo } from '../../../core/models/cotizacion.models';

const ICONOS_SERVICIO: Record<string, string> = {
  CHAPERIA: 'CH',
  LLANTERIA: 'LL',
  ELECTRICIDAD: 'EL',
  ELECTRONICA: 'EC',
  MECANICA_GENERAL: 'MG',
  GRUA: 'GR',
  BATERIA: 'BT',
  MOTOR: 'MO',
  AUXILIO_CARRETERA: 'AC',
  OTROS: 'OT',
};

@Component({
  selector: 'app-taller-servicios',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, FormsModule],
  templateUrl: './taller-servicios.component.html',
  styleUrl: './taller-servicios.component.scss',
})
export class TallerServiciosComponent implements OnInit {
  private readonly cotSvc = inject(CotizacionService);
  private readonly tallerApi = inject(TallerApiService);

  tallerId       = signal(0);
  tallerNombre   = signal('');
  catalogo       = signal<ServicioCatalogo[]>([]);
  seleccion      = signal<Set<number>>(new Set());
  tieneGrua      = signal(false);
  loading        = signal(true);
  saving         = signal(false);
  busqueda       = signal('');
  msg            = signal<{ tipo: 'ok' | 'error'; texto: string } | null>(null);

  totalCatalogo = computed(() => this.catalogo().length);
  totalActivos  = computed(() => this.seleccion().size);
  catalogoFiltrado = computed(() => {
    const q = this.busqueda().trim().toLowerCase();
    const items = this.catalogo();
    if (!q) return items;
    return items.filter(
      (s) =>
        s.nombre.toLowerCase().includes(q) ||
        (s.descripcion?.toLowerCase().includes(q) ?? false) ||
        s.codigo.toLowerCase().includes(q),
    );
  });

  ngOnInit(): void {
    this.tallerApi.getMiTaller().subscribe({
      next: (taller) => {
        this.tallerId.set(taller.id);
        this.tallerNombre.set(taller.nombre_comercial);
        this.cargarCatalogo();
      },
      error: () => {
        this.loading.set(false);
        this.msg.set({ tipo: 'error', texto: 'No se pudo cargar el perfil del taller.' });
      },
    });
  }

  private cargarCatalogo(): void {
    this.cotSvc.getCatalogo().subscribe({
      next: (cat) => {
        this.catalogo.set(cat);
        this.cargarServiciosTaller();
      },
      error: () => {
        this.loading.set(false);
        this.msg.set({ tipo: 'error', texto: 'No se pudo cargar el catálogo de servicios.' });
      },
    });
  }

  private cargarServiciosTaller(): void {
    this.tallerApi.getMisServicios().subscribe({
      next: (servicios) => {
        this.seleccion.set(new Set(servicios.map((s) => s.id)));
        const grua = this.catalogo().find((s) => s.codigo === 'GRUA');
        this.tieneGrua.set(grua ? this.seleccion().has(grua.id) : false);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  toggleServicio(id: number): void {
    const s = new Set(this.seleccion());
    s.has(id) ? s.delete(id) : s.add(id);
    this.seleccion.set(s);

    const grua = this.catalogo().find((c) => c.codigo === 'GRUA');
    if (grua) this.tieneGrua.set(s.has(grua.id));
  }

  isSelected(id: number): boolean {
    return this.seleccion().has(id);
  }

  icono(codigo: string): string {
    return ICONOS_SERVICIO[codigo] ?? codigo.slice(0, 2);
  }

  esGrua(codigo: string): boolean {
    return codigo === 'GRUA';
  }

  seleccionarTodos(): void {
    const ids = this.catalogo().map((s) => s.id);
    this.seleccion.set(new Set(ids));
    const grua = this.catalogo().find((c) => c.codigo === 'GRUA');
    if (grua) this.tieneGrua.set(true);
  }

  limpiarTodos(): void {
    this.seleccion.set(new Set());
    this.tieneGrua.set(false);
  }

  guardar(): void {
    if (this.saving()) return;
    if (!this.tallerId()) return;
    this.saving.set(true);
    this.msg.set(null);

    const ids = Array.from(this.seleccion());
    this.tallerApi.actualizarMisServicios(ids).subscribe({
      next: () => {
        this.tallerApi.actualizarMiGrua(this.tieneGrua()).subscribe({
          next: () => {
            this.saving.set(false);
            this.msg.set({ tipo: 'ok', texto: 'Servicios actualizados correctamente.' });
          },
          error: () => {
            this.saving.set(false);
            this.msg.set({ tipo: 'ok', texto: 'Servicios guardados; grúa no pudo actualizarse.' });
          },
        });
      },
      error: () => {
        this.saving.set(false);
        this.msg.set({ tipo: 'error', texto: 'Error al guardar los servicios.' });
      },
    });
  }
}
