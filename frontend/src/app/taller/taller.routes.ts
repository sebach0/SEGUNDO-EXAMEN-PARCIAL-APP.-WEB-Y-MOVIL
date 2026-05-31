import { Routes } from '@angular/router';
import { tallerAuthGuard } from '../core/guards/taller-auth.guard';
import { tallerPermisoGuard } from '../core/guards/taller-permiso.guard';

/** Rutas bajo `/taller` (login, recuperar, registro, panel). */
export const TALLER_ROUTES: Routes = [
  {
    path: 'recuperar',
    loadComponent: () =>
      import('./features/auth/taller-recover/taller-recover.component').then(
        (m) => m.TallerRecoverComponent,
      ),
  },
  {
    path: 'restablecer-contrasena',
    loadComponent: () =>
      import('./features/auth/taller-reset-password/taller-reset-password.component').then(
        (m) => m.TallerResetPasswordComponent,
      ),
  },
  {
    path: 'registro',
    loadComponent: () =>
      import('./features/auth/taller-register/taller-register.component').then(
        (m) => m.TallerRegisterComponent,
      ),
  },
  {
    path: 'panel',
    loadComponent: () => import('./shell/taller-shell.component').then((m) => m.TallerShellComponent),
    canActivate: [tallerAuthGuard],
    children: [
      {
        path: '',
        pathMatch: 'full',
        loadComponent: () =>
          import('./features/dashboard/taller-dashboard.component').then((m) => m.TallerDashboardComponent),
      },
      {
        path: 'mi-taller',
        loadComponent: () =>
          import('./features/mi-taller/taller-mi-taller.component').then((m) => m.TallerMiTallerComponent),
      },
      {
        path: 'tecnicos',
        loadComponent: () =>
          import('./features/tecnicos/taller-tecnicos.component').then((m) => m.TallerTecnicosComponent),
      },
      {
        path: 'emergencias/solicitudes',
        canActivate: [tallerPermisoGuard],
        data: { permiso: 'solicitudes_taller:leer' },
        loadComponent: () =>
          import('./features/emergencias/bandeja/taller-emergencias-bandeja.component').then(
            (m) => m.TallerEmergenciasBandejaComponent,
          ),
      },
      {
        path: 'emergencias/solicitudes/:bandejaId',
        canActivate: [tallerPermisoGuard],
        data: { permiso: 'solicitudes_taller:leer' },
        loadComponent: () =>
          import('./features/emergencias/incidente-detalle/taller-emergencias-incidente-detalle.component').then(
            (m) => m.TallerEmergenciasIncidenteDetalleComponent,
          ),
      },
      {
        path: 'emergencias/mis-solicitudes',
        canActivate: [tallerPermisoGuard],
        data: { permiso: 'historial_atenciones:leer', historialModo: 'mis' },
        loadComponent: () =>
          import('./features/emergencias/historial-list/taller-emergencias-historial-list.component').then(
            (m) => m.TallerEmergenciasHistorialListComponent,
          ),
      },
      {
        path: 'emergencias/historial',
        canActivate: [tallerPermisoGuard],
        data: { permiso: 'historial_atenciones:leer', historialModo: 'historial' },
        loadComponent: () =>
          import('./features/emergencias/historial-list/taller-emergencias-historial-list.component').then(
            (m) => m.TallerEmergenciasHistorialListComponent,
          ),
      },
      {
        path: 'emergencias/servicios-asignados',
        canActivate: [tallerPermisoGuard],
        data: { permiso: 'historial_atenciones:leer', historialModo: 'servicios' },
        loadComponent: () =>
          import('./features/emergencias/historial-list/taller-emergencias-historial-list.component').then(
            (m) => m.TallerEmergenciasHistorialListComponent,
          ),
      },
      {
        path: 'emergencias/comisiones',
        canActivate: [tallerPermisoGuard],
        data: { permiso: 'comisiones:leer' },
        loadComponent: () =>
          import('./features/emergencias/comisiones/taller-emergencias-comisiones.component').then(
            (m) => m.TallerEmergenciasComisionesComponent,
          ),
      },
      {
        path: 'emergencias/disponibilidad',
        canActivate: [tallerPermisoGuard],
        data: { permiso: 'disponibilidad:gestionar' },
        loadComponent: () =>
          import('./features/emergencias/disponibilidad/taller-emergencias-disponibilidad.component').then(
            (m) => m.TallerEmergenciasDisponibilidadComponent,
          ),
      },
    ],
  },
  {
    path: '',
    loadComponent: () =>
      import('./features/auth/taller-login/taller-login.component').then((m) => m.TallerLoginComponent),
  },
];
