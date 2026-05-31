import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AdminApiService } from '../../../core/services/admin-api.service';
import type { PermisoDto } from '../../../core/models/admin-api.models';

@Component({
  selector: 'app-admin-permisos',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './admin-permisos.component.html',
  styleUrl: './admin-permisos.component.scss',
})
export class AdminPermisosComponent implements OnInit {
  private readonly api = inject(AdminApiService);

  permisos: PermisoDto[] = [];
  modulo = '';
  search = '';
  loading = true;
  error: string | null = null;

  ngOnInit(): void {
    this.api.listPermisos().subscribe({
      next: (p) => {
        this.permisos = p;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
        this.error = 'No se pudieron cargar los permisos.';
      },
    });
  }

  get modulos(): string[] {
    return [...new Set(this.permisos.map((x) => x.modulo))].sort();
  }

  get filtered(): PermisoDto[] {
    let rows = this.permisos;
    if (this.modulo) rows = rows.filter((p) => p.modulo === this.modulo);
    const q = this.search.trim().toLowerCase();
    if (q) {
      rows = rows.filter(
        (p) =>
          p.codigo.toLowerCase().includes(q) ||
          p.nombre.toLowerCase().includes(q) ||
          (p.descripcion && p.descripcion.toLowerCase().includes(q)),
      );
    }
    return rows;
  }
}
