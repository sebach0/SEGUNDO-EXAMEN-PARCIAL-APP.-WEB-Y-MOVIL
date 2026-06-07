import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { AdminAuthService } from '../../core/services/admin-auth.service';

@Component({
  selector: 'app-admin-shell',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './admin-shell.component.html',
  styleUrl: './admin-shell.component.scss',
})
export class AdminShellComponent {
  readonly auth = inject(AdminAuthService);

  readonly nav = [
    { path: '/admin/panel', label: 'Resumen', exact: true },
    { path: '/admin/panel/finanzas', label: 'Finanzas', exact: true },
    { path: '/admin/panel/usuarios', label: 'Usuarios', exact: false },
    { path: '/admin/panel/roles', label: 'Roles', exact: false },
    { path: '/admin/panel/permisos', label: 'Permisos', exact: false },
    { path: '/admin/panel/talleres', label: 'Talleres', exact: false },
    { path: '/admin/panel/bitacora', label: 'Bitácora', exact: false },
    // Ciclo 4
    { path: '/admin/panel/ciclo4/realtime-monitor', label: 'Monitor RT', exact: false },
    { path: '/admin/panel/ciclo4/kpis', label: 'KPIs', exact: false },
  ];
}
