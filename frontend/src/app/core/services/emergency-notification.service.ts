import { Injectable, NgZone, OnDestroy, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Subscription, timer } from 'rxjs';
import { catchError, switchMap } from 'rxjs/operators';
import { of } from 'rxjs';
import { environment } from '../../../environments/environment';
import type { EmergenciaAdminDto } from '../models/admin-api.models';
import type { BandejaIncidenteBaseDto } from '../models/taller-emergencias.models';

export interface EmergencyNotification {
  id: number;
  titulo: string;
  mensaje: string;
}

@Injectable({ providedIn: 'root' })
export class EmergencyNotificationService implements OnDestroy {
  private readonly http = inject(HttpClient);
  private readonly zone = inject(NgZone);

  private sub: Subscription | null = null;
  private knownIds = new Set<number>();
  private firstPoll = true;

  notifications: EmergencyNotification[] = [];
  unreadCount = 0;

  requestPermission(): void {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }

  startAdminPolling(): void {
    this.stop();
    this.requestPermission();
    this.firstPoll = true;

    this.sub = timer(0, 30_000)
      .pipe(
        switchMap(() =>
          this.http
            .get<EmergenciaAdminDto[]>(`${environment.apiUrl}/incidents/admin/emergencias`)
            .pipe(catchError(() => of([] as EmergenciaAdminDto[])))
        )
      )
      .subscribe(lista => {
        if (this.firstPoll) {
          lista.forEach(e => this.knownIds.add(e.id));
          this.firstPoll = false;
          return;
        }
        lista
          .filter(e => !this.knownIds.has(e.id))
          .forEach(e => {
            this.knownIds.add(e.id);
            const cliente = e.cliente_nombre ?? 'Cliente';
            const desc = e.descripcion_texto ?? 'Sin descripción';
            this.notify('🚨 Nueva emergencia', `#${e.id} — ${cliente}: ${desc}`);
          });
      });
  }

  startTallerPolling(): void {
    this.stop();
    this.requestPermission();
    this.firstPoll = true;

    this.sub = timer(0, 30_000)
      .pipe(
        switchMap(() =>
          this.http
            .get<BandejaIncidenteBaseDto[]>(
              `${environment.apiUrl}/app/taller/emergencias/bandeja/disponibles`
            )
            .pipe(catchError(() => of([] as BandejaIncidenteBaseDto[])))
        )
      )
      .subscribe(lista => {
        if (this.firstPoll) {
          lista.forEach(e => this.knownIds.add(e.solicitud_id));
          this.firstPoll = false;
          return;
        }
        lista
          .filter(e => !this.knownIds.has(e.solicitud_id))
          .forEach(e => {
            this.knownIds.add(e.solicitud_id);
            const vehiculo = [e.marca, e.modelo, e.placa].filter(Boolean).join(' ');
            this.notify(
              '🚨 Nueva solicitud',
              `Solicitud #${e.solicitud_id} — ${vehiculo || 'Vehículo sin datos'}`
            );
          });
      });
  }

  dismiss(id: number): void {
    this.notifications = this.notifications.filter(n => n.id !== id);
  }

  markAllRead(): void {
    this.unreadCount = 0;
  }

  clearAll(): void {
    this.notifications = [];
    this.unreadCount = 0;
  }

  stop(): void {
    this.sub?.unsubscribe();
    this.sub = null;
    this.knownIds.clear();
    this.firstPoll = true;
    this.notifications = [];
    this.unreadCount = 0;
  }

  private notify(titulo: string, mensaje: string): void {
    this.zone.run(() => {
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(titulo, { body: mensaje, icon: '/favicon.ico' });
      }
      const n: EmergencyNotification = { id: Date.now(), titulo, mensaje };
      this.notifications = [n, ...this.notifications].slice(0, 20);
      this.unreadCount++;
    });
  }

  ngOnDestroy(): void {
    this.stop();
  }
}
