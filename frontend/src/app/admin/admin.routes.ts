import { Routes } from '@angular/router';
import { adminAuthGuard } from '../core/guards/admin-auth.guard';

/** Rutas bajo `/admin` (login, recuperar, panel). */
export const ADMIN_ROUTES: Routes = [
  {
    path: 'recuperar',
    loadComponent: () =>
      import('./features/auth/admin-recover/admin-recover.component').then(
        (m) => m.AdminRecoverComponent,
      ),
  },
  {
    path: 'panel',
    loadComponent: () => import('./shell/admin-shell.component').then((m) => m.AdminShellComponent),
    canActivate: [adminAuthGuard],
    children: [
      {
        path: '',
        pathMatch: 'full',
        loadComponent: () =>
          import('./features/dashboard/admin-dashboard.component').then((m) => m.AdminDashboardComponent),
      },
      {
        path: 'usuarios',
        loadComponent: () =>
          import('./features/usuarios/admin-usuarios.component').then((m) => m.AdminUsuariosComponent),
      },
      {
        path: 'roles',
        loadComponent: () =>
          import('./features/roles/admin-roles.component').then((m) => m.AdminRolesComponent),
      },
      {
        path: 'permisos',
        loadComponent: () =>
          import('./features/permisos/admin-permisos.component').then((m) => m.AdminPermisosComponent),
      },
      {
        path: 'talleres',
        loadComponent: () =>
          import('./features/talleres/admin-talleres.component').then((m) => m.AdminTalleresComponent),
      },
      {
        path: 'bitacora',
        loadComponent: () =>
          import('./features/bitacora/admin-bitacora.component').then((m) => m.AdminBitacoraComponent),
      },
      {
        path: 'finanzas',
        loadComponent: () =>
          import('./features/finanzas/admin-finanzas.component').then((m) => m.AdminFinanzasComponent),
      },
    ],
  },
  {
    path: '',
    loadComponent: () =>
      import('./features/auth/admin-login/admin-login.component').then((m) => m.AdminLoginComponent),
  },
];
