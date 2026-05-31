import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  AbstractControl,
  FormBuilder,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { AuthPublicApiService } from '../../../../core/services/auth-public-api.service';

function passwordsMatch(c: AbstractControl): ValidationErrors | null {
  const p = c.get('password')?.value;
  const c2 = c.get('password2')?.value;
  if (!p || !c2) return null;
  return p === c2 ? null : { mismatch: true };
}

@Component({
  selector: 'app-taller-reset-password',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './taller-reset-password.component.html',
  styleUrl: './taller-reset-password.component.scss',
})
export class TallerResetPasswordComponent {
  private readonly fb = inject(FormBuilder);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly authPublic = inject(AuthPublicApiService);

  readonly token = this.route.snapshot.queryParamMap.get('token') ?? '';

  readonly form = this.fb.nonNullable.group(
    {
      password: ['', [Validators.required, Validators.minLength(6)]],
      password2: ['', [Validators.required]],
    },
    { validators: passwordsMatch },
  );

  submitting = false;
  success = false;
  errorMsg: string | null = null;
  missingToken = !this.token;

  submit(): void {
    this.errorMsg = null;
    if (this.missingToken) {
      this.errorMsg = 'Enlace incompleto. Abre el enlace que recibiste por correo.';
      return;
    }
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const { password } = this.form.getRawValue();
    this.submitting = true;
    this.authPublic.restablecerContrasena(this.token, password).subscribe({
      next: () => {
        this.submitting = false;
        this.success = true;
        setTimeout(() => void this.router.navigate(['/taller']), 2500);
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
        this.errorMsg = 'No se pudo actualizar la contraseña.';
      },
    });
  }
}
