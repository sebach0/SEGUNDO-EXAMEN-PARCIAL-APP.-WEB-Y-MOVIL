import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';
import { TallerApiService } from '../../../core/services/taller-api.service';
import type { MiTallerDto, MiTallerUpdatePayload } from '../../../core/models/taller-api.models';
import type { ServicioCatalogo } from '../../../core/models/cotizacion.models';
import { OsmMapPickerComponent, type MapLocation } from '../../../shared/components/osm-map-picker/osm-map-picker.component';

@Component({
  selector: 'app-taller-mi-taller',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, OsmMapPickerComponent],
  templateUrl: './taller-mi-taller.component.html',
  styleUrl: './taller-mi-taller.component.scss',
})
export class TallerMiTallerComponent implements OnInit {
  private readonly api = inject(TallerApiService);

  m: MiTallerDto | null = null;
  servicios: ServicioCatalogo[] = [];
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
  latitud: number | null = null;
  longitud: number | null = null;

  ngOnInit(): void {
    this.reload();
  }

  reload(): void {
    this.loading = true;
    forkJoin({
      taller: this.api.getMiTaller(),
      servicios: this.api.getMisServicios(),
    }).subscribe({
      next: ({ taller, servicios }) => {
        this.m = taller;
        this.servicios = servicios;
        this.nombre_comercial = taller.nombre_comercial;
        this.telefono_contacto = taller.telefono_contacto;
        this.email_contacto = taller.email_contacto;
        this.direccion = taller.direccion;
        this.ciudad = taller.ciudad;
        this.descripcion = taller.descripcion ?? '';
        this.resp_nombres = taller.responsable_nombres;
        this.resp_apellidos = taller.responsable_apellidos;
        this.resp_telefono = taller.responsable_telefono;
        this.latitud = taller.latitud ?? null;
        this.longitud = taller.longitud ?? null;
        this.loading = false;
        this.error = null;
      },
      error: () => {
        this.loading = false;
        this.error = 'No se pudo cargar el perfil del taller.';
      },
    });
  }

  esGrua(codigo: string): boolean {
    return codigo === 'GRUA';
  }

  onMapLocation(loc: MapLocation): void {
    this.latitud = loc.lat;
    this.longitud = loc.lng;
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
      latitud: this.latitud,
      longitud: this.longitud,
      usuario: {
        nombres: this.resp_nombres,
        apellidos: this.resp_apellidos,
        telefono: this.resp_telefono,
      },
    };
    this.api.updateMiTaller(body).subscribe({
      next: (x) => {
        this.m = x;
        this.latitud = x.latitud ?? null;
        this.longitud = x.longitud ?? null;
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
