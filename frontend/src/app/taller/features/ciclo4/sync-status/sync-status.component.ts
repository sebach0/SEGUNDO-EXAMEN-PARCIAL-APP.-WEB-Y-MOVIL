import { Component, inject, OnInit } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { SyncService } from '../../../../core/services/sync.service';
import { OfflineQueueService } from '../../../../core/services/offline-queue.service';
import type { OfflineEvent, SyncStatusItem, SyncLocalStatus } from '../../../../core/models/ciclo4.models';
import { SYNC_STATUS_LABELS } from '../../../../core/models/ciclo4.models';

/**
 * SyncStatusComponent — Ciclo 4 (CU40 / CU42)
 *
 * Ruta: /taller/panel/ciclo4/sync/status
 *
 * Muestra:
 * - Registros locales (IndexedDB): pendiente, enviado, sincronizado, error.
 * - Registros remotos desde GET /api/sync/status.
 * - Permite reintentar manualmente los errores.
 */
@Component({
  selector: 'app-sync-status',
  standalone: true,
  imports: [CommonModule, DatePipe],
  templateUrl: './sync-status.component.html',
  styleUrl: './sync-status.component.scss',
})
export class SyncStatusComponent implements OnInit {
  private readonly syncSvc = inject(SyncService);
  private readonly queue = inject(OfflineQueueService);

  readonly statusLabels = SYNC_STATUS_LABELS;

  // ── Estado local (IndexedDB) ───────────────────────────────────────────────

  localEvents: OfflineEvent[] = [];
  loadingLocal = true;

  // ── Estado remoto (backend) ───────────────────────────────────────────────

  remoteItems: SyncStatusItem[] = [];
  loadingRemote = true;
  errorRemote: string | null = null;

  // ── Sync ──────────────────────────────────────────────────────────────────

  syncing = false;
  syncMsg: string | null = null;
  syncError: string | null = null;

  ngOnInit(): void {
    this.loadLocal();
    this.loadRemote();
  }

  loadLocal(): void {
    this.loadingLocal = true;
    this.queue.getAllEvents().then((events) => {
      this.localEvents = events.sort(
        (a, b) =>
          new Date(b.registrado_local_en).getTime() - new Date(a.registrado_local_en).getTime(),
      );
      this.loadingLocal = false;
    });
  }

  loadRemote(): void {
    this.loadingRemote = true;
    this.errorRemote = null;
    this.syncSvc.getSyncStatus().subscribe({
      next: (items) => {
        this.remoteItems = items;
        this.loadingRemote = false;
      },
      error: (err) => {
        this.loadingRemote = false;
        const detail = (err as { error?: { detail?: string } })?.error?.detail;
        this.errorRemote = detail ?? 'No se pudo cargar el estado remoto.';
      },
    });
  }

  retry(): void {
    this.syncing = true;
    this.syncMsg = null;
    this.syncError = null;

    this.syncSvc.syncPendingAutomatically().subscribe({
      next: (result) => {
        this.syncing = false;
        if (result.total === 0) {
          this.syncMsg = 'No hay eventos pendientes por sincronizar.';
        } else if (result.con_error === 0) {
          this.syncMsg = `✓ ${result.sincronizados} evento(s) sincronizado(s) correctamente.`;
        } else {
          this.syncMsg = `${result.sincronizados} sincronizado(s), ${result.con_error} con error.`;
        }
        this.loadLocal();
        this.loadRemote();
      },
      error: () => {
        this.syncing = false;
        this.syncError = 'Error al sincronizar. Verifica tu conexión.';
      },
    });
  }

  statusClass(status: SyncLocalStatus | string): string {
    const map: Record<string, string> = {
      pendiente: 'badge--warning',
      enviado: 'badge--info',
      sincronizado: 'badge--success',
      error: 'badge--danger',
    };
    return map[status] ?? 'badge--muted';
  }

  pendingCount(): number {
    return this.localEvents.filter(
      (e) => e._estado_local === 'pendiente' || e._estado_local === 'error',
    ).length;
  }
}
