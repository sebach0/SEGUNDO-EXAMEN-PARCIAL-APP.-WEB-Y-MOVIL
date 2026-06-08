import { Component, OnDestroy, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { take } from 'rxjs';
import { TallerAuthService } from '../../core/services/taller-auth.service';
import { EmergencyNotificationService } from '../../core/services/emergency-notification.service';

type NavItem = { path: string; label: string; exact: boolean; permiso?: string };

@Component({
  selector: 'app-taller-shell',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './taller-shell.component.html',
  styleUrl: './taller-shell.component.scss',
})
export class TallerShellComponent implements OnInit, OnDestroy {
  readonly auth = inject(TallerAuthService);
  readonly notifSvc = inject(EmergencyNotificationService);

  bellOpen = false;

  ngOnInit(): void {
    this.auth.refreshMeSiHaySesion().pipe(take(1)).subscribe();
    this.notifSvc.startTallerPolling();
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

  private readonly navAll: NavItem[] = [
    { path: '/taller/panel', label: 'Resumen', exact: true },
    {
      path: '/taller/panel/emergencias/solicitudes',
      label: 'Solicitudes',
      exact: false,
      permiso: 'solicitudes_taller:leer',
    },
    {
      path: '/taller/panel/emergencias/mis-solicitudes',
      label: 'Mis solicitudes',
      exact: true,
      permiso: 'historial_atenciones:leer',
    },
    {
      path: '/taller/panel/emergencias/historial',
      label: 'Historial de atenciones',
      exact: true,
      permiso: 'historial_atenciones:leer',
    },
    {
      path: '/taller/panel/emergencias/servicios-asignados',
      label: 'Servicios asignados',
      exact: true,
      permiso: 'historial_atenciones:leer',
    },
    {
      path: '/taller/panel/emergencias/comisiones',
      label: 'Comisiones',
      exact: true,
      permiso: 'comisiones:leer',
    },
    {
      path: '/taller/panel/emergencias/disponibilidad',
      label: 'Disponibilidad',
      exact: true,
      permiso: 'disponibilidad:gestionar',
    },
    { path: '/taller/panel/mi-taller', label: 'Mi taller', exact: false },
    { path: '/taller/panel/tecnicos', label: 'Técnicos', exact: false },
    // Ciclo 4
    { path: '/taller/panel/ciclo4/offline-incidents', label: 'Incidentes offline', exact: false },
    { path: '/taller/panel/ciclo4/sync/status', label: 'Estado de sync', exact: false },
    // Ciclo 4 Segunda Fase
    { path: '/taller/panel/servicios', label: 'Mis servicios', exact: false },
  ];

  /** Oculta entradas de emergencias si el JWT no trae el permiso (backend FastAPI). */
  get nav(): NavItem[] {
    const permisos = this.auth.getMe()?.permisos;
    if (!permisos?.length) return [...this.navAll];
    return this.navAll.filter((item) => !item.permiso || permisos.includes(item.permiso));
  }
}
