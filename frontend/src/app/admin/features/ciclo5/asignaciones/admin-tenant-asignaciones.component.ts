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
import { ActivatedRoute, RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';
import * as L from 'leaflet';
import { AdminApiService } from '../../../../core/services/admin-api.service';
import type {
  AssignmentResultDto,
  TenantDto,
  TenantMembersDto,
  TallerDto,
} from '../../../../core/models/admin-api.models';

const DEFAULT_CENTER: L.LatLngExpression = [-17.783, -63.182];
const DEFAULT_ZOOM = 12;

@Component({
  selector: 'app-admin-tenant-asignaciones',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './admin-tenant-asignaciones.component.html',
  styleUrl: './admin-tenant-asignaciones.component.scss',
})
export class AdminTenantAsignacionesComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('tallerMap', { static: false }) mapHost!: ElementRef<HTMLDivElement>;

  private readonly api = inject(AdminApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly zone = inject(NgZone);

  tenantId!: number;
  tenant: TenantDto | null = null;
  members: TenantMembersDto | null = null;
  allTalleres: TallerDto[] = [];

  loading = true;
  error: string | null = null;
  busy = false;
  successMsg: string | null = null;

  selectedWorkshopIds: Set<number> = new Set();

  private map: L.Map | null = null;
  private markers: L.Marker[] = [];
  private mapInitialized = false;

  ngOnInit(): void {
    this.tenantId = Number(this.route.snapshot.paramMap.get('id'));
    this.reload();
  }

  ngAfterViewInit(): void {
    // Map initializes after first data load (inside reload callback)
  }

  ngOnDestroy(): void {
    this.map?.remove();
    this.map = null;
  }

  reload(): void {
    this.loading = true;
    this.error = null;
    forkJoin({
      tenant: this.api.getTenant(this.tenantId),
      members: this.api.getTenantMembers(this.tenantId),
      talleres: this.api.listTalleres(),
    }).subscribe({
      next: ({ tenant, members, talleres }) => {
        this.tenant = tenant;
        this.members = members;
        this.allTalleres = talleres;
        this.loading = false;
        this.cdr.markForCheck();
        setTimeout(() => this.initOrUpdateMap(), 150);
      },
      error: () => {
        this.loading = false;
        this.error = 'No se pudo cargar la información del tenant.';
        this.cdr.markForCheck();
      },
    });
  }

  get memberWorkshopIds(): Set<number> {
    return new Set(this.members?.talleres.map((t) => t.id) ?? []);
  }

  get availableTalleres(): TallerDto[] {
    const assigned = this.memberWorkshopIds;
    return this.allTalleres.filter((t) => !assigned.has(t.id));
  }

  get talleresConUbicacion(): number {
    return (this.members?.talleres ?? []).filter(
      (t) => t.latitud != null && t.longitud != null,
    ).length;
  }

  toggleWorkshop(id: number): void {
    if (this.selectedWorkshopIds.has(id)) {
      this.selectedWorkshopIds.delete(id);
    } else {
      this.selectedWorkshopIds.add(id);
    }
    this.cdr.markForCheck();
  }

  assignWorkshops(): void {
    if (this.selectedWorkshopIds.size === 0) return;
    this.busy = true;
    this.error = null;
    this.api.assignWorkshopsToTenant(this.tenantId, [...this.selectedWorkshopIds]).subscribe({
      next: (r) => this._handleAssignResult(r),
      error: (err) => this._handleAssignError(err),
    });
  }

  private _handleAssignResult(r: AssignmentResultDto): void {
    this.busy = false;
    this.selectedWorkshopIds.clear();
    this.successMsg = r.message;
    setTimeout(() => {
      this.successMsg = null;
      this.cdr.markForCheck();
    }, 4000);
    this.reload();
  }

  private _handleAssignError(err: unknown): void {
    this.busy = false;
    const e = err as { error?: { detail?: string } };
    this.error = e?.error?.detail ?? 'No se pudo completar la asignación.';
    this.cdr.markForCheck();
  }

  private initOrUpdateMap(): void {
    if (!this.mapHost?.nativeElement) return;

    this.zone.runOutsideAngular(() => {
      if (!this.mapInitialized) {
        this.map = L.map(this.mapHost.nativeElement, { zoomControl: true }).setView(
          DEFAULT_CENTER,
          DEFAULT_ZOOM,
        );
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          maxZoom: 19,
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        }).addTo(this.map);
        this.mapInitialized = true;
      }
      this.updateMapMarkers();
    });
  }

  private buildPopup(memberTaller: { id: number; nombre_comercial: string; ciudad: string; estado: string }): string {
    const full = this.allTalleres.find((x) => x.id === memberTaller.id);
    const tenantNombre = this.tenant?.nombre ?? 'Este tenant';
    const color = '#4361ee';

    const gruaBadge = full?.tiene_grua
      ? `<span style="font-size:10px;font-weight:700;padding:1px 6px;border-radius:3px;background:rgba(67,97,238,0.15);border:1px solid rgba(67,97,238,0.4);color:#818cf8;margin-left:5px">Grúa</span>`
      : '';

    const detailRows = full
      ? `<div style="display:flex;flex-direction:column;gap:3px;font-size:12px;margin-bottom:8px">
           <div><span style="color:#64748b;display:inline-block;width:68px">Dirección:</span><span style="color:#cbd5e1">${full.direccion}</span></div>
           <div><span style="color:#64748b;display:inline-block;width:68px">Teléfono:</span><span style="color:#cbd5e1">${full.telefono_contacto}</span></div>
           <div><span style="color:#64748b;display:inline-block;width:68px">Email:</span><span style="color:#cbd5e1;word-break:break-all">${full.email_contacto}</span></div>
         </div>
         ${full.descripcion ? `<p style="margin:0 0 8px;color:#94a3b8;font-size:12px;font-style:italic">${full.descripcion}</p>` : ''}`
      : '';

    return `
      <div style="min-width:210px;max-width:280px;font-size:13px;line-height:1.6;font-family:system-ui,sans-serif">
        <div style="margin-bottom:3px">
          <strong style="font-size:14px">${memberTaller.nombre_comercial}</strong>${gruaBadge}
        </div>
        <div style="color:#94a3b8;font-size:12px;margin-bottom:8px">${memberTaller.ciudad} · ${memberTaller.estado}</div>
        ${detailRows}
        <span style="display:inline-flex;align-items:center;gap:5px;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;background:${color}22;border:1px solid ${color}55;color:${color}">
          <span style="width:8px;height:8px;border-radius:50%;background:${color};display:inline-block;flex-shrink:0"></span>
          ${tenantNombre}
        </span>
      </div>`;
  }

  private updateMapMarkers(): void {
    if (!this.map) return;

    this.markers.forEach((m) => m.remove());
    this.markers = [];

    const talleres = this.members?.talleres ?? [];
    const bounds: L.LatLngExpression[] = [];

    for (const t of talleres) {
      if (t.latitud == null || t.longitud == null) continue;
      const pos: L.LatLngExpression = [t.latitud, t.longitud];
      bounds.push(pos);
      const marker = L.marker(pos, {
        icon: L.divIcon({
          className: '',
          html: `<div style="width:20px;height:20px;border-radius:50% 50% 50% 0;transform:rotate(-45deg);background:#4361ee;border:2px solid rgba(255,255,255,0.85);box-shadow:0 2px 8px rgba(0,0,0,0.35)"></div>`,
          iconSize: [20, 20],
          iconAnchor: [10, 20],
          popupAnchor: [0, -22],
        }),
        title: t.nombre_comercial,
      })
        .bindPopup(this.buildPopup(t), { maxWidth: 300 })
        .addTo(this.map);
      this.markers.push(marker);
    }

    if (bounds.length === 1) {
      this.map.setView(bounds[0], 15);
    } else if (bounds.length > 1) {
      this.map.fitBounds(L.latLngBounds(bounds), { padding: [48, 48], maxZoom: 15 });
    } else {
      this.map.setView(DEFAULT_CENTER, DEFAULT_ZOOM);
    }
    setTimeout(() => this.map?.invalidateSize(), 200);
  }
}
