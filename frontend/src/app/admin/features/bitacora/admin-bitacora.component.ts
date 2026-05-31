import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AdminApiService } from '../../../core/services/admin-api.service';
import type { AccionBitacora, BitacoraDto } from '../../../core/models/admin-api.models';

@Component({
  selector: 'app-admin-bitacora',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './admin-bitacora.component.html',
  styleUrl: './admin-bitacora.component.scss',
})
export class AdminBitacoraComponent implements OnInit {
  private readonly api = inject(AdminApiService);

  rows: BitacoraDto[] = [];
  loading = true;
  error: string | null = null;

  usuarioId = '';
  modulo = '';
  accion: AccionBitacora | '' = '';
  desde = '';
  hasta = '';

  detail: BitacoraDto | null = null;

  readonly acciones: AccionBitacora[] = [
    'CREAR',
    'ACTUALIZAR',
    'ELIMINAR',
    'INICIAR_SESION',
    'CERRAR_SESION',
    'RESTABLECER_CONTRASENA',
    'ASIGNAR_ROL',
    'ASIGNAR_PERMISO',
    'CONSULTAR',
  ];

  ngOnInit(): void {
    this.fetch();
  }

  fetch(): void {
    this.loading = true;
    this.error = null;
    const uid = this.usuarioId.trim() ? Number(this.usuarioId) : undefined;
    if (this.usuarioId.trim() && Number.isNaN(uid)) {
      this.error = 'ID de usuario inválido.';
      this.loading = false;
      return;
    }
    const desdeIso = this.desde ? new Date(this.desde).toISOString() : undefined;
    const hastaIso = this.hasta ? new Date(this.hasta).toISOString() : undefined;
    this.api
      .listBitacora({
        usuario_id: uid,
        modulo: this.modulo.trim() || undefined,
        accion: this.accion || undefined,
        desde: desdeIso,
        hasta: hastaIso,
        limit: 100,
        offset: 0,
      })
      .subscribe({
        next: (r) => {
          this.rows = r;
          this.loading = false;
        },
        error: () => {
          this.loading = false;
          this.error = 'No se pudo consultar la bitácora.';
        },
      });
  }

  openDetail(row: BitacoraDto): void {
    this.detail = row;
  }

  closeDetail(): void {
    this.detail = null;
  }
}
