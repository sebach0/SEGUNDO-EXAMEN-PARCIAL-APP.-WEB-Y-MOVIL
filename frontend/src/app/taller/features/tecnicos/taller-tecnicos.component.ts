import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TallerApiService } from '../../../core/services/taller-api.service';
import type {
  EstadoTecnico,
  TecnicoPortalCreatePayload,
  TecnicoPortalDto,
  TecnicoPortalUpdatePayload,
} from '../../../core/models/taller-api.models';

@Component({
  selector: 'app-taller-tecnicos',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './taller-tecnicos.component.html',
  styleUrl: './taller-tecnicos.component.scss',
})
export class TallerTecnicosComponent implements OnInit {
  private readonly api = inject(TallerApiService);

  tecnicos: TecnicoPortalDto[] = [];
  search = '';
  estado: EstadoTecnico | '' = '';
  loading = true;
  error: string | null = null;
  busy = false;

  modalCreate = false;
  modalEdit = false;
  modalDetail = false;
  selected: TecnicoPortalDto | null = null;

  createForm: TecnicoPortalCreatePayload = {
    nombre_completo: '',
    email: '',
    telefono: '',
    password: '',
    documento: '',
    disponibilidad: '',
    estado: 'ACTIVO',
  };

  editNombre = '';
  editEmail = '';
  editTelefono = '';
  editDocumento = '';
  editDisp = '';
  editEstado: EstadoTecnico = 'ACTIVO';

  readonly estados: EstadoTecnico[] = ['ACTIVO', 'INACTIVO'];

  ngOnInit(): void {
    this.reload();
  }

  reload(): void {
    this.loading = true;
    this.api.listTecnicos().subscribe({
      next: (tecnicos) => {
        this.tecnicos = tecnicos;
        this.loading = false;
        this.error = null;
      },
      error: () => {
        this.loading = false;
        this.error = 'No se pudieron cargar los técnicos.';
      },
    });
  }

  get filtered(): TecnicoPortalDto[] {
    let rows = this.tecnicos;
    if (this.estado) rows = rows.filter((t) => t.estado === this.estado);
    const q = this.search.trim().toLowerCase();
    if (q) {
      rows = rows.filter(
        (t) =>
          `${t.nombres} ${t.apellidos}`.toLowerCase().includes(q) ||
          t.email.toLowerCase().includes(q) ||
          t.telefono.includes(q),
      );
    }
    return rows;
  }

  openDetail(t: TecnicoPortalDto): void {
    this.selected = t;
    this.modalDetail = true;
  }

  openEditFromDetail(): void {
    const t = this.selected;
    if (!t) return;
    this.modalDetail = false;
    this.openEdit(t);
  }

  openCreate(): void {
    this.createForm = {
      nombre_completo: '',
      email: '',
      telefono: '',
      password: '',
      documento: '',
      disponibilidad: '',
      estado: 'ACTIVO',
    };
    this.modalCreate = true;
  }

  create(): void {
    if (!this.createForm.password || this.createForm.password.length < 4) {
      this.error = 'La contraseña del técnico debe tener al menos 4 caracteres.';
      return;
    }
    this.busy = true;
    this.api.createTecnico(this.createForm).subscribe({
      next: () => {
        this.modalCreate = false;
        this.busy = false;
        this.reload();
      },
      error: () => {
        this.busy = false;
        this.error = 'No se pudo registrar el técnico (email o teléfono duplicado).';
      },
    });
  }

  openEdit(t: TecnicoPortalDto): void {
    this.selected = t;
    this.editNombre = `${t.nombres} ${t.apellidos}`.trim();
    this.editEmail = t.email;
    this.editTelefono = t.telefono;
    this.editDocumento = t.documento ?? '';
    this.editDisp = t.disponibilidad ?? '';
    this.editEstado = t.estado;
    this.modalEdit = true;
  }

  saveEdit(): void {
    if (!this.selected) return;
    const body: TecnicoPortalUpdatePayload = {
      nombre_completo: this.editNombre,
      email: this.editEmail,
      telefono: this.editTelefono,
      documento: this.editDocumento || null,
      disponibilidad: this.editDisp || null,
      estado: this.editEstado,
    };
    this.busy = true;
    this.api.updateTecnico(this.selected.id, body).subscribe({
      next: () => {
        this.modalEdit = false;
        this.busy = false;
        this.reload();
      },
      error: () => {
        this.busy = false;
        this.error = 'No se pudo actualizar el técnico.';
      },
    });
  }

  setEstado(t: TecnicoPortalDto, e: EstadoTecnico): void {
    this.busy = true;
    this.api.updateTecnico(t.id, { estado: e }).subscribe({
      next: () => {
        this.busy = false;
        this.reload();
        this.closeModals();
      },
      error: () => {
        this.busy = false;
        this.error = 'No se pudo cambiar el estado.';
      },
    });
  }

  closeModals(): void {
    this.modalCreate = this.modalEdit = this.modalDetail = false;
    this.selected = null;
  }
}
