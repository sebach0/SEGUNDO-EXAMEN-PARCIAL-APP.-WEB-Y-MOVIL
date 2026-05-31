import { Routes } from '@angular/router';

/** Rutas raíz: landing pública + árboles lazy `admin` y `taller`. */
export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    loadComponent: () =>
      import('./public/pages/landing/landing-page.component').then((m) => m.LandingPageComponent),
  },
  {
    path: 'admin',
    loadChildren: () => import('./admin/admin.routes').then((m) => m.ADMIN_ROUTES),
  },
  {
    path: 'taller',
    loadChildren: () => import('./taller/taller.routes').then((m) => m.TALLER_ROUTES),
  },
  { path: '**', redirectTo: '' },
];
