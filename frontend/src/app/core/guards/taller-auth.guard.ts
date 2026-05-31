import { inject } from '@angular/core';
import { Router, type CanActivateFn } from '@angular/router';
import { map, take } from 'rxjs';
import { TallerAuthService } from '../services/taller-auth.service';

export const tallerAuthGuard: CanActivateFn = () => {
  const auth = inject(TallerAuthService);
  const router = inject(Router);

  return auth.hydrateMeIfNeeded().pipe(
    take(1),
    map((ok) => {
      if (ok) return true;
      void router.navigate(['/taller']);
      return false;
    }),
  );
};
