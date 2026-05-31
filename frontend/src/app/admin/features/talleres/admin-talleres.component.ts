import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { AdminApiService } from '../../../core/services/admin-api.service';
import type {
  EstadoTaller,
  TallerCreatePayload,
  TallerDto,
  TallerUpdatePayload,
  UsuarioListDto,
} from '../../../core/models/admin-api.models';

@Component({
  selector: 'app-admin-talleres',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './admin-talleres.component.html',
  styleUrl: './admin-talleres.component.scss',
})
export class AdminTalleresComponent implements OnInit {
  private readonly api = inject(AdminApiService);

  talleres: TallerDto[] = [];
  usuarios: UsuarioListDto[] = [];
  search = '';
  estado: EstadoTaller | '' = '';
  loading = true;
  error: string | null = null;
  busy = false;

  detail: TallerDto | null = null;
  modalEdit = false;
  modalCreate = false;
  editId: number | null = null;
  editForm: TallerUpdatePayload = {};
  createForm: TallerCreatePayload = {
    usuario_responsable_id: 0,
    nombre_comercial: '',
    telefono_contacto: '',
    email_contacto: '',
    direccion: '',
    ciudad: '',
    descripcion: '',
    estado: 'PENDIENTE',
  };

  readonly estados: EstadoTaller[] = ['PENDIENTE', 'ACTIVO', 'SUSPENDIDO', 'INACTIVO'];

  /** Usuarios con rol taller (responsable); el desplegable de nuevo taller solo los lista. */
  get responsablesTaller(): UsuarioListDto[] {
    return this.usuarios.filter((u) => (u.roles || []).includes('TALLER_RESPONSABLE'));
  }

  ngOnInit(): void {
    this.reload();
  }

  reload(): void {
    this.loading = true;
    forkJoin({ talleres: this.api.listTalleres(), usuarios: this.api.listUsuarios() }).subscribe({
      next: ({ talleres, usuarios }) => {
        this.talleres = talleres;
        this.usuarios = usuarios;
        const firstResp = this.responsablesTaller[0];
        if (firstResp) {
          this.createForm.usuario_responsable_id = firstResp.id;
        } else {
          this.createForm.usuario_responsable_id = 0;
        }
        this.loading = false;
        this.error = null;
      },
      error: () => {
        this.loading = false;
        this.error = 'No se pudieron cargar los talleres.';
      },
    });
  }

  get filtered(): TallerDto[] {
    let rows = this.talleres;
    if (this.estado) rows = rows.filter((t) => t.estado === this.estado);
    const q = this.search.trim().toLowerCase();
    if (q) {
      rows = rows.filter(
        (t) =>
          t.nombre_comercial.toLowerCase().includes(q) ||
          t.ciudad.toLowerCase().includes(q) ||
          t.email_contacto.toLowerCase().includes(q),
      );
    }
    return rows;
  }

  openDetail(t: TallerDto): void {
    this.detail = t;
  }

  openCreateModal(): void {
    const first = this.responsablesTaller[0];
    this.createForm.usuario_responsable_id = first?.id ?? 0;
    this.modalCreate = true;
  }

  openEdit(t: TallerDto): void {
    this.editId = t.id;
    this.editForm = {
      nombre_comercial: t.nombre_comercial,
      telefono_contacto: t.telefono_contacto,
      email_contacto: t.email_contacto,
      direccion: t.direccion,
      ciudad: t.ciudad,
      descripcion: t.descripcion ?? '',
      estado: t.estado,
    };
    this.modalEdit = true;
  }

  saveEdit(): void {
    if (this.editId == null) return;
    this.busy = true;
    this.api.updateTaller(this.editId, this.editForm).subscribe({
      next: (t) => {
        this.talleres = this.talleres.map((x) => (x.id === t.id ? t : x));
        this.modalEdit = false;
        this.busy = false;
        this.detail = null;
      },
      error: () => {
        this.busy = false;
        this.error = 'No se pudo actualizar el taller.';
      },
    });
  }

  create(): void {
    if (!this.createForm.usuario_responsable_id) {
      this.error = 'Elige un usuario responsable con rol TALLER_RESPONSABLE.';
      return;
    }
    this.busy = true;
    this.api.createTaller(this.createForm).subscribe({
      next: (t) => {
        this.talleres = [...this.talleres, t];
        this.modalCreate = false;
        this.busy = false;
        this.createForm = {
          usuario_responsable_id: this.responsablesTaller[0]?.id ?? 0,
          nombre_comercial: '',
          telefono_contacto: '',
          email_contacto: '',
          direccion: '',
          ciudad: '',
          descripcion: '',
          estado: 'PENDIENTE',
        };
      },
      error: () => {
        this.busy = false;
        this.error = 'No se pudo crear el taller (revisa usuario responsable y datos).';
      },
    });
  }

  setEstado(t: TallerDto, estado: EstadoTaller): void {
    this.busy = true;
    this.api.updateTaller(t.id, { estado }).subscribe({
      next: (u) => {
        this.talleres = this.talleres.map((x) => (x.id === u.id ? u : x));
        this.busy = false;
        if (this.detail?.id === u.id) this.detail = u;
      },
      error: () => {
        this.busy = false;
        this.error = 'No se pudo cambiar el estado.';
      },
    });
  }

  closeModals(): void {
    this.detail = null;
    this.modalEdit = false;
    this.modalCreate = false;
    this.editId = null;
  }
}
