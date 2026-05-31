import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  AbstractControl,
  FormBuilder,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import { RouterLink } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { environment } from '../../../../../environments/environment';
import { TallerApiService } from '../../../../core/services/taller-api.service';

function passwordsMatch(c: AbstractControl): ValidationErrors | null {
  const p = c.get('password')?.value;
  const c2 = c.get('password2')?.value;
  if (!p || !c2) return null;
  return p === c2 ? null : { mismatch: true };
}

@Component({
  selector: 'app-taller-register',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './taller-register.component.html',
  styleUrl: './taller-register.component.scss',
})
export class TallerRegisterComponent {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(TallerApiService);

  readonly form = this.fb.nonNullable.group(
    {
      nombre_comercial: ['', [Validators.required, Validators.minLength(2)]],
      email: ['', [Validators.required, Validators.email]],
      telefono: ['', [Validators.required, Validators.minLength(5)]],
      direccion: ['', [Validators.required]],
      ciudad: ['', [Validators.required]],
      descripcion: [''],
      responsable_nombre_completo: ['', [Validators.required, Validators.minLength(3)]],
      password: ['', [Validators.required, Validators.minLength(4)]],
      password2: ['', [Validators.required]],
      terms: [false, Validators.requiredTrue],
    },
    { validators: passwordsMatch },
  );

  submitting = false;
  success = false;
  errorMsg: string | null = null;
  showPassword = false;
  pendienteVerificacion = false;
  readonly mailhogWebUrl = environment.mailhogWebUrl;

  submit(): void {
    this.errorMsg = null;
    this.success = false;
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const v = this.form.getRawValue();
    this.submitting = true;
    this.api
      .registro({
        nombre_comercial: v.nombre_comercial.trim(),
        email: v.email.trim(),
        telefono: v.telefono.trim(),
        direccion: v.direccion.trim(),
        ciudad: v.ciudad.trim(),
        descripcion: v.descripcion?.trim() || null,
        responsable_nombre_completo: v.responsable_nombre_completo.trim(),
        password: v.password,
      })
      .subscribe({
        next: (dto) => {
          this.submitting = false;
          this.success = true;
          this.pendienteVerificacion = dto.pendiente_verificacion_email !== false;
        },
        error: (err: unknown) => {
          this.submitting = false;
          if (err instanceof HttpErrorResponse) {
            const d = err.error?.detail;
            if (typeof d === 'string') {
              this.errorMsg = d;
              return;
            }
          }
          this.errorMsg = 'No se pudo completar el registro.';
        },
      });
  }
}
