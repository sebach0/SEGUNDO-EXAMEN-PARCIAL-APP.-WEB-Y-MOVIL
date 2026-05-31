import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { AdminApiService } from '../../../core/services/admin-api.service';
import type { PermisoDto, RolDto } from '../../../core/models/admin-api.models';

@Component({
  selector: 'app-admin-roles',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './admin-roles.component.html',
  styleUrl: './admin-roles.component.scss',
})
export class AdminRolesComponent implements OnInit {
  private readonly api = inject(AdminApiService);

  roles: RolDto[] = [];
  permisos: PermisoDto[] = [];
  search = '';
  loading = true;
  error: string | null = null;
  busy = false;

  modalCreate = false;
  modalPerm = false;
  modalView = false;
  selectedRol: RolDto | null = null;
  permIds = new Set<number>();

  newNombre = '';
  newDesc = '';

  ngOnInit(): void {
    this.reload();
  }

  reload(): void {
    this.loading = true;
    this.error = null;
    forkJoin({
      roles: this.api.listRoles(),
      permisos: this.api.listPermisos(),
    }).subscribe({
      next: ({ roles, permisos }) => {
        this.roles = roles;
        this.permisos = permisos;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
        this.error = 'No se pudieron cargar los roles.';
      },
    });
  }

  get filtered(): RolDto[] {
    const q = this.search.trim().toLowerCase();
    if (!q) return this.roles;
    return this.roles.filter(
      (r) =>
        r.nombre.toLowerCase().includes(q) ||
        (r.descripcion && r.descripcion.toLowerCase().includes(q)),
    );
  }

  permisosByModulo(): Record<string, PermisoDto[]> {
    const m: Record<string, PermisoDto[]> = {};
    for (const p of this.permisos) {
      m[p.modulo] = m[p.modulo] || [];
      m[p.modulo].push(p);
    }
    return m;
  }

  openView(r: RolDto): void {
    this.selectedRol = r;
    this.modalView = true;
  }

  openPerm(r: RolDto): void {
    this.selectedRol = r;
    this.busy = true;
    this.api.getRolPermisoIds(r.id).subscribe({
      next: (res) => {
        this.permIds = new Set(res.permiso_ids);
        this.modalPerm = true;
        this.busy = false;
      },
      error: () => {
        this.busy = false;
        this.error = 'No se pudieron cargar los permisos del rol.';
      },
    });
  }

  togglePerm(id: number): void {
    if (this.permIds.has(id)) this.permIds.delete(id);
    else this.permIds.add(id);
  }

  savePermisos(): void {
    if (!this.selectedRol) return;
    this.busy = true;
    this.api.setRolPermisos(this.selectedRol.id, [...this.permIds]).subscribe({
      next: () => {
        this.modalPerm = false;
        this.busy = false;
      },
      error: () => {
        this.busy = false;
        this.error = 'No se pudo guardar la asignación.';
      },
    });
  }

  createRol(): void {
    if (!this.newNombre.trim()) return;
    this.busy = true;
    this.api.createRol(this.newNombre.trim(), this.newDesc.trim() || null).subscribe({
      next: (r) => {
        this.roles = [...this.roles, r].sort((a, b) => a.nombre.localeCompare(b.nombre));
        this.modalCreate = false;
        this.newNombre = '';
        this.newDesc = '';
        this.busy = false;
      },
      error: () => {
        this.busy = false;
        this.error = 'No se pudo crear el rol.';
      },
    });
  }

  closeModals(): void {
    this.modalCreate = this.modalPerm = this.modalView = false;
    this.selectedRol = null;
    this.permIds = new Set();
  }
}
