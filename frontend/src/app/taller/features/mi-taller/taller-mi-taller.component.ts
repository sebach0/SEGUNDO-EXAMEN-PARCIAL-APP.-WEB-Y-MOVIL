import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TallerApiService } from '../../../core/services/taller-api.service';
import type { MiTallerDto, MiTallerUpdatePayload } from '../../../core/models/taller-api.models';

@Component({
  selector: 'app-taller-mi-taller',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './taller-mi-taller.component.html',
  styleUrl: './taller-mi-taller.component.scss',
})
export class TallerMiTallerComponent implements OnInit {
  private readonly api = inject(TallerApiService);

  m: MiTallerDto | null = null;
  loading = true;
  error: string | null = null;
  busy = false;

  nombre_comercial = '';
  telefono_contacto = '';
  email_contacto = '';
  direccion = '';
  ciudad = '';
  descripcion = '';
  resp_nombres = '';
  resp_apellidos = '';
  resp_telefono = '';

  ngOnInit(): void {
    this.reload();
  }

  reload(): void {
    this.loading = true;
    this.api.getMiTaller().subscribe({
      next: (x) => {
        this.m = x;
        this.nombre_comercial = x.nombre_comercial;
        this.telefono_contacto = x.telefono_contacto;
        this.email_contacto = x.email_contacto;
        this.direccion = x.direccion;
        this.ciudad = x.ciudad;
        this.descripcion = x.descripcion ?? '';
        this.resp_nombres = x.responsable_nombres;
        this.resp_apellidos = x.responsable_apellidos;
        this.resp_telefono = x.responsable_telefono;
        this.loading = false;
        this.error = null;
      },
      error: () => {
        this.loading = false;
        this.error = 'No se pudo cargar el perfil del taller.';
      },
    });
  }

  save(): void {
    if (!this.m) return;
    this.busy = true;
    const body: MiTallerUpdatePayload = {
      nombre_comercial: this.nombre_comercial,
      telefono_contacto: this.telefono_contacto,
      email_contacto: this.email_contacto,
      direccion: this.direccion,
      ciudad: this.ciudad,
      descripcion: this.descripcion || null,
      usuario: {
        nombres: this.resp_nombres,
        apellidos: this.resp_apellidos,
        telefono: this.resp_telefono,
      },
    };
    this.api.updateMiTaller(body).subscribe({
      next: (x) => {
        this.m = x;
        this.busy = false;
        this.error = null;
      },
      error: () => {
        this.busy = false;
        this.error = 'No se pudieron guardar los cambios.';
      },
    });
  }
}
