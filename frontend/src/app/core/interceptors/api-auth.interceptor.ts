import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AdminAuthService } from '../services/admin-auth.service';
import { TallerAuthService } from '../services/taller-auth.service';
import { environment } from '../../../environments/environment';

/** Bearer: app taller responsable (`/api/app/taller/*`) vs resto del panel admin. */
export const apiAuthInterceptor: HttpInterceptorFn = (req, next) => {
  const api = environment.apiUrl;
  const isApi = req.url.includes(`${api}/`) || req.url.endsWith(api);
  if (!isApi) {
    return next(req);
  }
  const authPublic =
    req.url.includes(`${api}/auth/login`) ||
    req.url.includes(`${api}/auth/solicitar-recuperacion-contrasena`) ||
    req.url.includes(`${api}/auth/restablecer-contrasena`) ||
    (req.url.includes(`${api}/auth/verificar-email`) && req.method === 'GET');
  if (authPublic) {
    return next(req);
  }

  // Login/hydrate/logout pasan Bearer explícito; no sustituir con otra sesión (p. ej. admin + app taller).
  if (req.headers.has('Authorization')) {
    return next(req);
  }

  const tallerAppPrefix = `${api}/app/taller`;
  const isTallerApp = req.url.includes(tallerAppPrefix);
  const isPublicRegistro =
    isTallerApp && req.url.includes('/app/taller/registro') && req.method === 'POST';

  if (isPublicRegistro) {
    return next(req);
  }

  // Endpoints compartidos fuera de /app/taller que usa el portal responsable (marketplace, KPIs).
  const isTallerSharedApi =
    req.url.includes(`${api}/cotizaciones`) || req.url.includes(`${api}/kpis/`);

  // Ciclo 4 legacy (incidents/sync/tenants) — excluir rutas /admin/ que usan token de admin.
  const isCiclo4Admin = req.url.includes(`${api}/incidents/admin`);
  const isCiclo4 =
    !isCiclo4Admin &&
    (req.url.includes(`${api}/incidents`) ||
      req.url.includes(`${api}/sync`) ||
      req.url.includes(`${api}/tenants`));

  let token: string | null;
  if (isTallerApp) {
    token = inject(TallerAuthService).getAccessToken();
  } else if (isTallerSharedApi || isCiclo4) {
    // Portal taller o admin: preferir sesión taller, luego admin.
    token =
      inject(TallerAuthService).getAccessToken() ??
      inject(AdminAuthService).getAccessToken();
  } else {
    token = inject(AdminAuthService).getAccessToken();
  }

  if (!token) return next(req);

  return next(
    req.clone({
      setHeaders: { Authorization: `Bearer ${token}` },
    }),
  );
};
