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

  const token = isTallerApp
    ? inject(TallerAuthService).getAccessToken()
    : inject(AdminAuthService).getAccessToken();

  if (!token) {
    return next(req);
  }
  return next(
    req.clone({
      setHeaders: { Authorization: `Bearer ${token}` },
    }),
  );
};
