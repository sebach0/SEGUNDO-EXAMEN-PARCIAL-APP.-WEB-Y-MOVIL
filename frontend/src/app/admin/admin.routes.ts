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
      // ── KPIs unificados ────────────────────────────────────────────────────
      {
        path: 'kpis',
        loadComponent: () =>
          import('./features/kpis/admin-kpis-unified.component').then(
            (m) => m.AdminKpisUnifiedComponent,
          ),
      },
      // Rutas legacy — redirigen al panel unificado
      { path: 'ciclo4/kpis',    redirectTo: 'kpis', pathMatch: 'full' },
      { path: 'ciclo5/dashboard', redirectTo: 'kpis', pathMatch: 'full' },
      // ── Ciclo 4: monitor en tiempo real ───────────────────────────────────
      {
        path: 'ciclo4/realtime-monitor',
        loadComponent: () =>
          import('./features/ciclo4/realtime-monitor/admin-realtime-monitor.component').then(
            (m) => m.AdminRealtimeMonitorComponent,
          ),
      },
      // ── Ciclo 5: Tenants, Reportes, SLA ───────────────────────────────────
      {
        path: 'ciclo5/tenants',
        loadComponent: () =>
          import('./features/ciclo5/tenants/admin-tenants.component').then(
            (m) => m.AdminTenantsComponent,
          ),
      },
      {
        path: 'ciclo5/tenants/:id/asignaciones',
        loadComponent: () =>
          import('./features/ciclo5/asignaciones/admin-tenant-asignaciones.component').then(
            (m) => m.AdminTenantAsignacionesComponent,
          ),
      },
      {
        path: 'ciclo5/reports',
        loadComponent: () =>
          import('./features/ciclo5/reports/admin-reports.component').then(
            (m) => m.AdminReportsComponent,
          ),
      },
      {
        path: 'ciclo5/sla',
        loadComponent: () =>
          import('./features/ciclo5/sla/admin-sla.component').then(
            (m) => m.AdminSlaComponent,
          ),
      },
      {
        path: 'emergencias',
        loadComponent: () =>
          import('./features/emergencias/admin-emergencias.component').then(
            (m) => m.AdminEmergenciasComponent,
          ),
      },
      {
        path: 'backup',
        loadComponent: () =>
          import('./features/backup/admin-backup.component').then(
            (m) => m.AdminBackupComponent,
          ),
      },
    ],
  },
  {
    path: '',
    loadComponent: () =>
      import('./features/auth/admin-login/admin-login.component').then((m) => m.AdminLoginComponent),
  },
];
