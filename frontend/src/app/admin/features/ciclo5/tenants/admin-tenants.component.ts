import {
  AfterViewInit,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  NgZone,
  OnDestroy,
  OnInit,
  ViewChild,
  inject,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';
import * as L from 'leaflet';
import { AdminApiService } from '../../../../core/services/admin-api.service';
import type {
  EstadoTenant,
  TallerDto,
  TenantCreatePayload,
  TenantDto,
  TenantUpdatePayload,
} from '../../../../core/models/admin-api.models';

const TENANT_COLORS = [
  '#4361ee', '#e63946', '#2a9d8f', '#f4a261',
  '#9b5de5', '#00b4d8', '#06d6a0', '#ef476f', '#ffd166', '#a8dadc',
];
const NO_TENANT_COLOR = '#64748b';
const DEFAULT_CENTER: L.LatLngExpression = [-17.783, -63.182];
const DEFAULT_ZOOM = 11;

@Component({
  selector: 'app-admin-tenants',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './admin-tenants.component.html',
  styleUrl: './admin-tenants.component.scss',
})
export class AdminTenantsComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('tenantsMap', { static: true }) mapHost!: ElementRef<HTMLDivElement>;

  private readonly api = inject(AdminApiService);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly zone = inject(NgZone);

  tenants: TenantDto[] = [];
  talleres: TallerDto[] = [];
  loading = true;
  error: string | null = null;
  busy = false;
  successMsg: string | null = null;

  search = '';
  mapFilter: 'all' | 'none' | number = 'all';

  modalCreate = false;
  modalEdit = false;
  editTarget: TenantDto | null = null;

  createForm: TenantCreatePayload = { nombre: '', slug: '', estado: 'ACTIVO' };
  editForm: TenantUpdatePayload = {};

  readonly estados: EstadoTenant[] = ['ACTIVO', 'INACTIVO', 'SUSPENDIDO'];

  private map: L.Map | null = null;
  private markers: L.Marker[] = [];
  private tenantColorMap = new Map<number, string>();

  ngOnInit(): void {
    this.reload();
  }

  ngAfterViewInit(): void {
    this.zone.runOutsideAngular(() => {
      this.initMap();
      setTimeout(() => this.map?.invalidateSize(), 300);
    });
  }

  ngOnDestroy(): void {
    this.map?.remove();
    this.map = null;
  }

  reload(): void {
    this.loading = true;
    this.error = null;
    forkJoin({
      tenants: this.api.listTenants(),
      talleres: this.api.listTalleres(),
    }).subscribe({
      next: ({ tenants, talleres }) => {
        this.tenants = tenants;
        this.talleres = talleres;
        this.buildColorMap();
        this.loading = false;
        this.cdr.markForCheck();
        setTimeout(() => {
          this.zone.runOutsideAngular(() => this.updateMapMarkers());
        }, 150);
      },
      error: () => {
        this.loading = false;
        this.error = 'No se pudieron cargar los tenants.';
        this.cdr.markForCheck();
      },
    });
  }

  get filtered(): TenantDto[] {
    const q = this.search.trim().toLowerCase();
    if (!q) return this.tenants;
    return this.tenants.filter(
      (t) =>
        t.nombre.toLowerCase().includes(q) ||
        t.slug.toLowerCase().includes(q),
    );
  }

  get talleresConUbicacion(): number {
    return this.talleres.filter((t) => t.latitud != null && t.longitud != null).length;
  }

  private get talleresForMap(): TallerDto[] {
    if (this.mapFilter === 'all') return this.talleres;
    if (this.mapFilter === 'none') return this.talleres.filter((t) => t.tenant_id == null);
    const id = this.mapFilter as number;
    return this.talleres.filter((t) => t.tenant_id === id);
  }

  applyMapFilter(value: string): void {
    if (value === 'all') this.mapFilter = 'all';
    else if (value === 'none') this.mapFilter = 'none';
    else this.mapFilter = Number(value);
    this.zone.runOutsideAngular(() => this.updateMapMarkers());
  }

  colorForTenant(tenantId: number | null): string {
    if (tenantId == null) return NO_TENANT_COLOR;
    return this.tenantColorMap.get(tenantId) ?? NO_TENANT_COLOR;
  }

  openCreate(): void {
    this.createForm = { nombre: '', slug: '', estado: 'ACTIVO' };
    this.modalCreate = true;
    this.error = null;
    this.cdr.markForCheck();
  }

  autoSlug(): void {
    this.createForm.slug = this.createForm.nombre
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '');
    this.cdr.markForCheck();
  }

  create(): void {
    if (!this.createForm.nombre.trim() || !this.createForm.slug.trim()) {
      this.error = 'Nombre y slug son obligatorios.';
      this.cdr.markForCheck();
      return;
    }
    this.busy = true;
    this.error = null;
    this.api.createTenant(this.createForm).subscribe({
      next: (t) => {
        this.tenants = [...this.tenants, t];
        this.modalCreate = false;
        this.busy = false;
        this.successMsg = `Tenant "${t.nombre}" creado.`;
        this.buildColorMap();
        setTimeout(() => {
          this.successMsg = null;
          this.cdr.markForCheck();
        }, 3000);
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.busy = false;
        this.error = err?.error?.detail ?? 'No se pudo crear el tenant.';
        this.cdr.markForCheck();
      },
    });
  }

  openEdit(t: TenantDto): void {
    this.editTarget = t;
    this.editForm = { nombre: t.nombre, slug: t.slug, estado: t.estado };
    this.modalEdit = true;
    this.error = null;
    this.cdr.markForCheck();
  }

  saveEdit(): void {
    if (!this.editTarget) return;
    this.busy = true;
    this.error = null;
    this.api.updateTenant(this.editTarget.id, this.editForm).subscribe({
      next: (updated) => {
        this.tenants = this.tenants.map((x) => (x.id === updated.id ? updated : x));
        this.modalEdit = false;
        this.editTarget = null;
        this.busy = false;
        this.successMsg = `Tenant "${updated.nombre}" actualizado.`;
        setTimeout(() => {
          this.successMsg = null;
          this.cdr.markForCheck();
        }, 3000);
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.busy = false;
        this.error = err?.error?.detail ?? 'No se pudo actualizar el tenant.';
        this.cdr.markForCheck();
      },
    });
  }

  activate(t: TenantDto): void {
    this.busy = true;
    this.api.activateTenant(t.id).subscribe({
      next: (updated) => {
        this.tenants = this.tenants.map((x) => (x.id === updated.id ? updated : x));
        this.busy = false;
        this.cdr.markForCheck();
      },
      error: () => {
        this.busy = false;
        this.cdr.markForCheck();
      },
    });
  }

  deactivate(t: TenantDto): void {
    this.busy = true;
    this.api.deactivateTenant(t.id).subscribe({
      next: (updated) => {
        this.tenants = this.tenants.map((x) => (x.id === updated.id ? updated : x));
        this.busy = false;
        this.cdr.markForCheck();
      },
      error: () => {
        this.busy = false;
        this.cdr.markForCheck();
      },
    });
  }

  closeModals(): void {
    this.modalCreate = false;
    this.modalEdit = false;
    this.editTarget = null;
    this.error = null;
    this.cdr.markForCheck();
  }

  estadoBadgeClass(estado: EstadoTenant): string {
    return (
      {
        ACTIVO: 'badge--activo',
        INACTIVO: 'badge--inactivo',
        SUSPENDIDO: 'badge--suspendido',
      }[estado] ?? ''
    );
  }

  private buildColorMap(): void {
    this.tenantColorMap.clear();
    this.tenants.forEach((t, i) => {
      this.tenantColorMap.set(t.id, TENANT_COLORS[i % TENANT_COLORS.length]);
    });
  }

  private initMap(): void {
    if (!this.mapHost?.nativeElement) return;
    this.map = L.map(this.mapHost.nativeElement, { zoomControl: true }).setView(
      DEFAULT_CENTER,
      DEFAULT_ZOOM,
    );
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(this.map);
    // If data arrived before map was ready
    if (this.talleres.length > 0) this.updateMapMarkers();
  }

  private updateMapMarkers(): void {
    if (!this.map) return;

    this.map.invalidateSize();
    this.markers.forEach((m) => m.remove());
    this.markers = [];

    const bounds: L.LatLngExpression[] = [];

    for (const t of this.talleresForMap) {
      if (t.latitud == null || t.longitud == null) continue;

      const color = this.colorForTenant(t.tenant_id);
      const tenant = t.tenant_id != null ? this.tenants.find((tn) => tn.id === t.tenant_id) : null;
      const tenantLabel = tenant ? tenant.nombre : 'Sin tenant asignado';

      const gruaBadge = t.tiene_grua
        ? `<span style="font-size:10px;font-weight:700;padding:1px 6px;border-radius:3px;background:rgba(67,97,238,0.15);border:1px solid rgba(67,97,238,0.4);color:#818cf8;margin-left:5px">Grúa</span>`
        : '';

      const popup = `
        <div style="min-width:210px;max-width:280px;font-size:13px;line-height:1.6;font-family:system-ui,sans-serif">
          <div style="margin-bottom:3px">
            <strong style="font-size:14px">${t.nombre_comercial}</strong>${gruaBadge}
          </div>
          <div style="color:#94a3b8;font-size:12px;margin-bottom:8px">${t.ciudad} · ${t.estado}</div>
          <div style="display:flex;flex-direction:column;gap:3px;font-size:12px;margin-bottom:8px">
            <div><span style="color:#64748b;display:inline-block;width:68px">Dirección:</span><span style="color:#cbd5e1">${t.direccion}</span></div>
            <div><span style="color:#64748b;display:inline-block;width:68px">Teléfono:</span><span style="color:#cbd5e1">${t.telefono_contacto}</span></div>
            <div><span style="color:#64748b;display:inline-block;width:68px">Email:</span><span style="color:#cbd5e1;word-break:break-all">${t.email_contacto}</span></div>
          </div>
          ${t.descripcion ? `<p style="margin:0 0 8px;color:#94a3b8;font-size:12px;font-style:italic">${t.descripcion}</p>` : ''}
          <span style="display:inline-flex;align-items:center;gap:5px;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;background:${color}22;border:1px solid ${color}55;color:${color}">
            <span style="width:8px;height:8px;border-radius:50%;background:${color};display:inline-block;flex-shrink:0"></span>
            ${tenantLabel}
          </span>
        </div>`;

      const marker = L.marker([t.latitud, t.longitud], {
        icon: L.divIcon({
          className: '',
          html: `<div style="width:22px;height:22px;border-radius:50% 50% 50% 0;transform:rotate(-45deg);background:${color};border:2px solid rgba(255,255,255,0.85);box-shadow:0 2px 8px rgba(0,0,0,0.35)"></div>`,
          iconSize: [22, 22],
          iconAnchor: [11, 22],
          popupAnchor: [0, -25],
        }),
        title: t.nombre_comercial,
      })
        .bindPopup(popup, { maxWidth: 280 })
        .addTo(this.map);

      this.markers.push(marker);
      bounds.push([t.latitud, t.longitud]);
    }

    if (bounds.length === 0) {
      this.map.setView(DEFAULT_CENTER, DEFAULT_ZOOM);
    } else if (bounds.length === 1) {
      this.map.setView(bounds[0] as L.LatLngExpression, 15);
    } else {
      this.map.fitBounds(L.latLngBounds(bounds as L.LatLngExpression[]), {
        padding: [48, 48],
        maxZoom: 14,
      });
    }
    setTimeout(() => this.map?.invalidateSize(), 200);
  }
}
