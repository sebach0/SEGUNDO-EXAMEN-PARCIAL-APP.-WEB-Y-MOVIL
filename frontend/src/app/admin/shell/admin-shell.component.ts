import { Component, OnDestroy, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { AdminAuthService } from '../../core/services/admin-auth.service';
import { EmergencyNotificationService } from '../../core/services/emergency-notification.service';

@Component({
  selector: 'app-admin-shell',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './admin-shell.component.html',
  styleUrl: './admin-shell.component.scss',
})
export class AdminShellComponent implements OnInit, OnDestroy {
  readonly auth = inject(AdminAuthService);
  readonly notifSvc = inject(EmergencyNotificationService);

  bellOpen = false;

  ngOnInit(): void {
    this.notifSvc.startAdminPolling();
  }

  ngOnDestroy(): void {
    this.notifSvc.stop();
  }

  toggleBell(): void {
    this.bellOpen = !this.bellOpen;
    if (this.bellOpen) this.notifSvc.markAllRead();
  }

  clearAll(): void {
    this.notifSvc.clearAll();
    this.bellOpen = false;
  }

  readonly nav = [
    { path: '/admin/panel', label: 'Resumen', exact: true },
    { path: '/admin/panel/finanzas', label: 'Finanzas', exact: true },
    { path: '/admin/panel/usuarios', label: 'Usuarios', exact: false },
    { path: '/admin/panel/roles', label: 'Roles', exact: false },
    { path: '/admin/panel/permisos', label: 'Permisos', exact: false },
    { path: '/admin/panel/talleres', label: 'Talleres', exact: false },
    { path: '/admin/panel/bitacora', label: 'Bitácora', exact: false },
    { path: '/admin/panel/kpis', label: 'KPIs', exact: false },
{ path: '/admin/panel/ciclo5/tenants', label: 'Tenants', exact: false },
    { path: '/admin/panel/ciclo5/reports', label: 'Reportes', exact: false },
    { path: '/admin/panel/ciclo5/sla', label: 'SLA Talleres', exact: false },
    { path: '/admin/panel/emergencias', label: 'Emergencias', exact: false },
    { path: '/admin/panel/backup', label: 'Backup', exact: false },
  ];
}
