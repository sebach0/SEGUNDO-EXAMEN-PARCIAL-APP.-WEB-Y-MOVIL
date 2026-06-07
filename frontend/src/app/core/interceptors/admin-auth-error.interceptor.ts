import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AdminAuthService } from '../services/admin-auth.service';
import { environment } from '../../../environments/environment';

/** Rutas del panel admin que requieren sesión ADMIN (Bearer ev_admin_access). */
function isAdminPanelApi(url: string, api: string): boolean {
  const prefixes = [
    `${api}/usuarios`,
    `${api}/roles`,
    `${api}/permisos`,
    `${api}/bitacora`,
    `${api}/talleres`,
    `${api}/admin/`,
    `${api}/incidents/admin/`,
    `${api}/kpis/`,
  ];
  return prefixes.some((p) => url.includes(p));
}

function isAuthFailure(err: HttpErrorResponse): boolean {
  if (err.status === 401) return true;
  if (err.status !== 403) return false;
  const detail = err.error?.detail;
  if (detail === 'Not authenticated') return true;
  if (typeof detail === 'string' && detail.toLowerCase().includes('token')) return true;
  return false;
}

/**
 * Si una API del panel admin responde sin autenticación válida,
 * limpia la sesión admin y redirige al login.
 */
export const adminAuthErrorInterceptor: HttpInterceptorFn = (req, next) => {
  const api = environment.apiUrl;
  if (!isAdminPanelApi(req.url, api)) {
    return next(req);
  }

  return next(req).pipe(
    catchError((err: unknown) => {
      if (err instanceof HttpErrorResponse && isAuthFailure(err)) {
        const auth = inject(AdminAuthService);
        const router = inject(Router);
        auth.clearSession();
        void router.navigate(['/admin'], {
          queryParams: { reason: 'session_expired' },
        });
      }
      return throwError(() => err);
    }),
  );
};
