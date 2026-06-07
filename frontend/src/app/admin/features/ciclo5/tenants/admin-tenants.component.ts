import { Component, inject, OnInit, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { AdminApiService } from '../../../../core/services/admin-api.service';
import type {
  EstadoTenant,
  TenantCreatePayload,
  TenantDto,
  TenantUpdatePayload,
} from '../../../../core/models/admin-api.models';

@Component({
  selector: 'app-admin-tenants',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './admin-tenants.component.html',
  styleUrl: './admin-tenants.component.scss',
})
export class AdminTenantsComponent implements OnInit {
  private readonly api = inject(AdminApiService);
  private readonly cdr = inject(ChangeDetectorRef);

  tenants: TenantDto[] = [];
  loading = true;
  error: string | null = null;
  busy = false;
  successMsg: string | null = null;

  search = '';

  modalCreate = false;
  modalEdit = false;
  editTarget: TenantDto | null = null;

  createForm: TenantCreatePayload = { nombre: '', slug: '', estado: 'ACTIVO' };
  editForm: TenantUpdatePayload = {};

  readonly estados: EstadoTenant[] = ['ACTIVO', 'INACTIVO', 'SUSPENDIDO'];

  ngOnInit(): void {
    this.reload();
  }

  reload(): void {
    this.loading = true;
    this.error = null;
    this.api.listTenants().subscribe({
      next: (data) => {
        this.tenants = data;
        this.loading = false;
        this.cdr.markForCheck();
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
        setTimeout(() => { this.successMsg = null; this.cdr.markForCheck(); }, 3000);
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
        setTimeout(() => { this.successMsg = null; this.cdr.markForCheck(); }, 3000);
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
      error: () => { this.busy = false; this.cdr.markForCheck(); },
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
      error: () => { this.busy = false; this.cdr.markForCheck(); },
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
    return {
      ACTIVO: 'badge--activo',
      INACTIVO: 'badge--inactivo',
      SUSPENDIDO: 'badge--suspendido',
    }[estado] ?? '';
  }
}
