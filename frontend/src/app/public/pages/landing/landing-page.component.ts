import { Component, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

export interface LandingModuleCard {
  title: string;
  desc: string;
  badge: string;
  accent: 'cyan' | 'blue' | 'indigo' | 'violet' | 'red' | 'emerald' | 'yellow' | 'orange' | 'teal';
}

@Component({
  selector: 'app-landing-page',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './landing-page.component.html',
  styleUrl: './landing-page.component.scss',
})
export class LandingPageComponent {
  navScrolled = false;
  menuOpen = false;

  readonly heroImage =
    'https://images.unsplash.com/photo-1660184687164-757e98363338?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxjYXIlMjBlbWVyZ2VuY3klMjByb2Fkc2lkZSUyMGFzc2lzdGFuY2UlMjBuaWdodHxlbnwxfHx8fDE3NzY1MTkzNTZ8MA&ixlib=rb-4.1.0&q=80&w=1080';

  readonly navLinks: { label: string; href: string }[] = [
    { label: 'Inicio', href: '#inicio' },
    { label: 'Características', href: '#caracteristicas' },
    { label: 'Accesos', href: '#portales' },
    { label: 'Cómo funciona', href: '#como-funciona' },
    { label: 'Módulos', href: '#modulos' },
    { label: 'Beneficios', href: '#beneficios' },
    { label: 'Stack', href: '#tecnologias' },
    { label: 'Proyecto', href: '#contacto' },
  ];

  readonly stats = [
    { val: '4', label: 'Roles integrados' },
    { val: '9+', label: 'Módulos activos' },
    { val: '100%', label: 'Trazabilidad' },
  ];

  readonly techPills = ['Angular', 'FastAPI', 'Flutter', 'Azure'];

  /** Orden visual: arriba-izq, arriba-der, abajo-izq (mapa sigue abajo-centro) */
  readonly floatingCards = [
    {
      title: 'Emergencia Reportada',
      sub: 'Av. Los Libertadores, Km 12',
      accent: 'cyan' as const,
    },
    {
      title: 'Caso #0821 Resuelto',
      sub: 'Valoración pos-atención: excelente',
      accent: 'blue' as const,
    },
    {
      title: 'Técnico Asignado',
      sub: 'ETA: 12 minutos',
      accent: 'emerald' as const,
    },
  ];

  readonly modules: LandingModuleCard[] = [
    {
      title: 'Acceso y Seguridad',
      desc: 'Autenticación robusta, control de sesiones, recuperación de contraseñas y permisos granulares por rol.',
      badge: 'Core',
      accent: 'cyan',
    },
    {
      title: 'Usuarios y Roles',
      desc: 'Gestión completa de perfiles: clientes, mecánicos, responsables de taller y administradores del sistema.',
      badge: 'IAM',
      accent: 'blue',
    },
    {
      title: 'Talleres y Técnicos',
      desc: 'Alta y configuración de talleres, gestión de técnicos asignados, horarios y zonas de cobertura.',
      badge: 'Ops',
      accent: 'indigo',
    },
    {
      title: 'Vehículos',
      desc: 'Registro de vehículos por cliente con ficha técnica, historial de atenciones y documentos asociados.',
      badge: 'Registro',
      accent: 'violet',
    },
    {
      title: 'Incidentes',
      desc: 'Creación, clasificación y gestión completa de reportes de emergencia con prioridad y seguimiento de estado.',
      badge: 'Core',
      accent: 'red',
    },
    {
      title: 'Atención al Servicio',
      desc: 'Flujo completo de atención: asignación, desplazamiento, diagnóstico, reparación y cierre documentado.',
      badge: 'Workflow',
      accent: 'emerald',
    },
    {
      title: 'Notificaciones',
      desc: 'Sistema de alertas push, email y en-app para mantener informados a todos los actores en tiempo real.',
      badge: 'Realtime',
      accent: 'yellow',
    },
    {
      title: 'Finanzas',
      desc: 'Registro de costos de servicio, generación de facturas, reportes financieros y análisis de ingresos.',
      badge: 'Finance',
      accent: 'orange',
    },
    {
      title: 'Historial y Trazabilidad',
      desc: 'Auditoría completa de cada acción, logs del sistema, historial por cliente/vehículo y reportes analíticos.',
      badge: 'Audit',
      accent: 'teal',
    },
  ];

  readonly footerSections: { title: string; links: { label: string; href: string }[] }[] = [
    {
      title: 'Plataforma',
      links: [
        { label: 'Características', href: '#caracteristicas' },
        { label: 'Cómo funciona', href: '#como-funciona' },
        { label: 'Módulos', href: '#modulos' },
        { label: 'Beneficios', href: '#beneficios' },
      ],
    },
    {
      title: 'Tecnología',
      links: [
        { label: 'Angular', href: '#tecnologias' },
        { label: 'FastAPI', href: '#tecnologias' },
        { label: 'Flutter', href: '#tecnologias' },
        { label: 'Azure', href: '#tecnologias' },
      ],
    },
    {
      title: 'Empresa',
      links: [
        { label: 'Sobre el proyecto', href: '#inicio' },
        { label: 'Accesos (taller / admin)', href: '#portales' },
        { label: 'Proyecto académico', href: '#contacto' },
      ],
    },
  ];

  @HostListener('window:scroll')
  onScroll(): void {
    this.navScrolled = window.scrollY > 20;
  }

  scrollTo(selector: string): void {
    const el = document.querySelector(selector);
    el?.scrollIntoView({ behavior: 'smooth' });
    this.menuOpen = false;
  }

  toggleMenu(): void {
    this.menuOpen = !this.menuOpen;
  }

  closeMenu(): void {
    this.menuOpen = false;
  }
}
