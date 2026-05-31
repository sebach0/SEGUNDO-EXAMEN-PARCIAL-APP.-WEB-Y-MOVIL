import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  FormBuilder,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { RouterLink } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { AuthPublicApiService } from '../../../../core/services/auth-public-api.service';

@Component({
  selector: 'app-taller-recover',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './taller-recover.component.html',
  styleUrl: './taller-recover.component.scss',
})
export class TallerRecoverComponent {
  private readonly fb = inject(FormBuilder);
  private readonly authPublic = inject(AuthPublicApiService);

  readonly form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
  });

  submitting = false;
  success = false;
  errorMsg: string | null = null;

  submit(): void {
    this.errorMsg = null;
    this.success = false;
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.submitting = true;
    const email = this.form.getRawValue().email.trim();
    this.authPublic.solicitarRecuperacionContrasena(email).subscribe({
      next: () => {
        this.submitting = false;
        this.success = true;
      },
      error: (err: unknown) => {
        this.submitting = false;
        if (err instanceof HttpErrorResponse && err.status === 0) {
          this.errorMsg = 'No hay conexión con la API.';
          return;
        }
        this.errorMsg = 'No se pudo enviar la solicitud. Intenta más tarde.';
      },
    });
  }
}
