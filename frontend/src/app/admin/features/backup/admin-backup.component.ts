import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AdminApiService } from '../../../core/services/admin-api.service';

@Component({
  selector: 'app-admin-backup',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './admin-backup.component.html',
  styleUrl: './admin-backup.component.scss',
})
export class AdminBackupComponent {
  private readonly api = inject(AdminApiService);

  loading = false;
  error: string | null = null;
  lastDownload: string | null = null;

  readonly tables = [
    'usuarios', 'roles', 'permisos', 'rol_permiso', 'usuario_rol',
    'tenants', 'talleres', 'tecnicos', 'clientes', 'vehiculos',
    'solicitudes_emergencia', 'bandeja_taller', 'cotizaciones',
    'pagos', 'notificaciones', 'bitacora',
  ];

  download(): void {
    if (this.loading) return;
    this.loading = true;
    this.error = null;

    this.api.downloadBackup().subscribe({
      next: (blob) => {
        const now = new Date();
        const ts = now.toISOString().replace(/[:.]/g, '-').slice(0, 19);
        const filename = `backup_${ts}.zip`;
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
        this.loading = false;
        this.lastDownload = now.toLocaleString('es-BO');
      },
      error: () => {
        this.loading = false;
        this.error = 'No se pudo generar el backup. Verificá los permisos o intentá más tarde.';
      },
    });
  }
}
