import { inject } from '@angular/core';
import { Router, type CanActivateFn } from '@angular/router';
import { map, take } from 'rxjs';
import { AdminAuthService } from '../services/admin-auth.service';

export const adminAuthGuard: CanActivateFn = () => {
  const auth = inject(AdminAuthService);
  const router = inject(Router);

  if (auth.isAdminSession()) {
    return true;
  }

  return auth.hydrateMeIfNeeded().pipe(
    take(1),
    map((ok) => {
      if (ok) return true;
      void router.navigate(['/admin']);
      return false;
    }),
  );
};
