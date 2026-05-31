import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  FormBuilder,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { AdminAuthService, AdminAuthError } from '../../../../core/services/admin-auth.service';

@Component({
  selector: 'app-admin-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './admin-login.component.html',
  styleUrl: './admin-login.component.scss',
})
export class AdminLoginComponent {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AdminAuthService);
  private readonly router = inject(Router);

  readonly form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(1)]],
    remember: [false],
  });

  showPassword = false;
  submitting = false;
  errorMsg: string | null = null;

  togglePassword(): void {
    this.showPassword = !this.showPassword;
  }

  submit(): void {
    this.errorMsg = null;
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const { email, password, remember } = this.form.getRawValue();
    this.submitting = true;
    this.auth.login(email.trim(), password, remember).subscribe({
      next: () => {
        this.submitting = false;
        void this.router.navigate(['/admin/panel']);
      },
      error: (err: unknown) => {
        this.submitting = false;
        this.errorMsg = this.formatError(err);
      },
    });
  }

  private formatError(err: unknown): string {
    if (err instanceof AdminAuthError) {
      return err.message;
    }
    if (err instanceof HttpErrorResponse) {
      const d = err.error?.detail;
      if (typeof d === 'string') return d;
      if (Array.isArray(d) && d[0]?.msg) return d.map((x: { msg: string }) => x.msg).join(' ');
    }
    return 'No se pudo iniciar sesión. Intenta de nuevo.';
  }
}
