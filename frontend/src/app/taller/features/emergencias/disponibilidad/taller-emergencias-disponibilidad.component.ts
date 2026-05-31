import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TallerEmergenciasApiService } from '../../../../core/services/taller-emergencias-api.service';
import type { TallerDisponibilidadDto } from '../../../../core/models/taller-emergencias.models';

@Component({
  selector: 'app-taller-emergencias-disponibilidad',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './taller-emergencias-disponibilidad.component.html',
  styleUrl: './taller-emergencias-disponibilidad.component.scss',
})
export class TallerEmergenciasDisponibilidadComponent implements OnInit {
  private readonly api = inject(TallerEmergenciasApiService);

  data: TallerDisponibilidadDto | null = null;
  acepta = true;
  capacidad = 10;
  observacion = '';
  loading = true;
  saving = false;
  error: string | null = null;
  success: string | null = null;

  ngOnInit(): void {
    this.reload();
  }

  reload(): void {
    this.loading = true;
    this.error = null;
    this.success = null;
    this.api.getDisponibilidad().subscribe({
      next: (d) => {
        this.data = d;
        this.acepta = d.acepta_nuevas_solicitudes;
        this.capacidad = d.capacidad_maxima_diaria;
        this.observacion = d.observacion ?? '';
        this.loading = false;
      },
      error: (err) => {
        this.loading = false;
        this.data = null;
        this.error = this.msg(err, 'No se pudo cargar la disponibilidad del taller.');
      },
    });
  }

  guardar(): void {
    if (this.capacidad < 1 || this.capacidad > 500) {
      this.error = 'La capacidad máxima diaria debe estar entre 1 y 500.';
      return;
    }
    this.saving = true;
    this.error = null;
    this.success = null;
    this.api
      .putDisponibilidad({
        acepta_nuevas_solicitudes: this.acepta,
        capacidad_maxima_diaria: this.capacidad,
        observacion: this.observacion.trim() || null,
      })
      .subscribe({
        next: (d) => {
          this.data = d;
          this.saving = false;
          this.success = 'Cambios guardados correctamente.';
        },
        error: (err) => {
          this.saving = false;
          this.error = this.msg(err, 'No se pudo guardar la disponibilidad.');
        },
      });
  }

  private msg(err: { error?: { detail?: unknown } }, fallback: string): string {
    const d = err?.error?.detail;
    if (typeof d === 'string') return d;
    if (Array.isArray(d) && d.length && typeof d[0] === 'object' && d[0] !== null && 'msg' in d[0]) {
      return String((d[0] as { msg: string }).msg);
    }
    return fallback;
  }
}
