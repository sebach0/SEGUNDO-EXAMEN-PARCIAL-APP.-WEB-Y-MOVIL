import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router';
import { Subscription } from 'rxjs';
import { NetworkService } from './core/services/network.service';
import { SyncService } from './core/services/sync.service';

type BannerState =
  | 'offline'
  | 'reconnecting'
  | 'syncing'
  | 'sync_ok'
  | 'sync_partial'
  | null;

/**
 * AppComponent — Ciclo 4
 *
 * Envuelve la aplicación completa y añade el banner global de
 * estado de conexión y sincronización offline.
 *
 * Detecta `window.online` / `window.offline` a través del NetworkService.
 * Al reconectar, dispara automáticamente SyncService.syncPendingAutomatically().
 */
@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
})
export class AppComponent implements OnInit, OnDestroy {
  title = 'emergencias-frontend';

  bannerState: BannerState = null;
  bannerMsg = '';
  private bannerTimer: ReturnType<typeof setTimeout> | null = null;

  private sub?: Subscription;

  constructor(
    private readonly network: NetworkService,
    private readonly syncSvc: SyncService,
  ) {}

  ngOnInit(): void {
    this.sub = this.network.isOnline$().subscribe((online) => {
      if (!online) {
        this._showBanner('offline', 'Sin conexión: los cambios se guardarán localmente.');
      } else {
        this._showBanner('reconnecting', 'Conexión restablecida: sincronizando registros pendientes…');
        this._autoSync();
      }
    });
  }

  ngOnDestroy(): void {
    this.sub?.unsubscribe();
    if (this.bannerTimer) clearTimeout(this.bannerTimer);
  }

  dismissBanner(): void {
    this.bannerState = null;
  }

  private _autoSync(): void {
    this.syncSvc.syncPendingAutomatically().subscribe({
      next: (result) => {
        if (result.total === 0) {
          // No había nada pendiente — no mostrar nada
          this.bannerState = null;
          return;
        }
        if (result.con_error === 0) {
          this._showBanner('sync_ok', `Sincronización completada: ${result.sincronizados} registro(s) enviado(s).`, 5000);
        } else {
          this._showBanner(
            'sync_partial',
            `Algunos registros no pudieron sincronizarse (${result.con_error} con error).`,
            8000,
          );
        }
      },
      error: () => {
        this._showBanner('sync_partial', 'Algunos registros no pudieron sincronizarse.', 8000);
      },
    });
  }

  private _showBanner(state: BannerState, msg: string, autoDismissMs?: number): void {
    if (this.bannerTimer) clearTimeout(this.bannerTimer);
    this.bannerState = state;
    this.bannerMsg = msg;
    if (autoDismissMs) {
      this.bannerTimer = setTimeout(() => {
        this.bannerState = null;
      }, autoDismissMs);
    }
  }

  get bannerClass(): string {
    const map: Record<NonNullable<BannerState>, string> = {
      offline: 'banner--offline',
      reconnecting: 'banner--info',
      syncing: 'banner--info',
      sync_ok: 'banner--success',
      sync_partial: 'banner--warning',
    };
    return this.bannerState ? (map[this.bannerState] ?? '') : '';
  }
}
