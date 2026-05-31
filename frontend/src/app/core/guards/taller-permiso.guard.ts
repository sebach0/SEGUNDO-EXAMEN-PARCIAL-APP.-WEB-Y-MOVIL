import { inject } from '@angular/core';
import { Router, type CanActivateFn } from '@angular/router';
import { TallerAuthService } from '../services/taller-auth.service';

/**
 * Activa la ruta solo si `route.data['permiso']` está en `auth/me` permisos.
 * Si no hay lista de permisos (respuesta antigua), permite el acceso y la API será quien niegue.
 */
export const tallerPermisoGuard: CanActivateFn = (route) => {
  const need = route.data['permiso'] as string | undefined;
  if (!need) return true;

  const auth = inject(TallerAuthService);
  const router = inject(Router);
  const perms = auth.getMe()?.permisos;
  if (!perms?.length) return true;
  if (perms.includes(need)) return true;
  return router.parseUrl('/taller/panel?denegado=1');
};
