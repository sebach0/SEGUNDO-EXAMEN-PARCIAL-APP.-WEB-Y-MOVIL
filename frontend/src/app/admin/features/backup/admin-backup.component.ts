import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AdminApiService } from '../../../core/services/admin-api.service';
import type { BackupFile } from '../../../core/models/admin-api.models';

@Component({
  selector: 'app-admin-backup',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './admin-backup.component.html',
  styleUrl: './admin-backup.component.scss',
})
export class AdminBackupComponent implements OnInit {
  private readonly api = inject(AdminApiService);

  loading = false;
  error: string | null = null;
  lastDownload: string | null = null;

  history: BackupFile[] = [];
  historyLoading = false;
  downloadingFile: string | null = null;

  readonly tables = [
    'usuarios', 'roles', 'permisos', 'rol_permiso', 'usuario_rol',
    'tenants', 'talleres', 'tecnicos', 'clientes', 'vehiculos',
    'solicitudes_emergencia', 'bandeja_taller', 'cotizaciones',
    'pagos', 'notificaciones', 'bitacora',
  ];

  ngOnInit(): void {
    this.loadHistory();
  }

  loadHistory(): void {
    this.historyLoading = true;
    this.api.getBackupHistory().subscribe({
      next: (files) => {
        this.history = files;
        this.historyLoading = false;
      },
      error: () => { this.historyLoading = false; },
    });
  }

  download(): void {
    if (this.loading) return;
    this.loading = true;
    this.error = null;

    this.api.downloadBackup().subscribe({
      next: (blob) => {
        const now = new Date();
        const ts = now.toISOString().replace(/[:.]/g, '-').slice(0, 19);
        this._triggerDownload(blob, `backup_${ts}.zip`);
        this.loading = false;
        this.lastDownload = now.toLocaleString('es-BO');
      },
      error: () => {
        this.loading = false;
        this.error = 'No se pudo generar el backup. Verificá los permisos o intentá más tarde.';
      },
    });
  }

  downloadFile(file: BackupFile): void {
    if (this.downloadingFile) return;
    this.downloadingFile = file.filename;
    this.api.downloadBackupFile(file.filename).subscribe({
      next: (blob) => {
        this._triggerDownload(blob, file.filename);
        this.downloadingFile = null;
      },
      error: () => { this.downloadingFile = null; },
    });
  }

  formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  formatDate(iso: string): string {
    return new Date(iso).toLocaleString('es-BO');
  }

  private _triggerDownload(blob: Blob, filename: string): void {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }
}
