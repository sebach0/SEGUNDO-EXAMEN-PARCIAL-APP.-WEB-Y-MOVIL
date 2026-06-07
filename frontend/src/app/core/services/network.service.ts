import { Injectable, NgZone } from '@angular/core';
import { Observable, BehaviorSubject, fromEvent, merge } from 'rxjs';
import { map, startWith } from 'rxjs/operators';

/**
 * NetworkService — Ciclo 4
 * Detecta eventos online/offline del navegador y expone el estado como Observable.
 * Escucha `window.online` y `window.offline` de forma reactiva con RxJS.
 */
@Injectable({ providedIn: 'root' })
export class NetworkService {
  private readonly _online$ = new BehaviorSubject<boolean>(navigator.onLine);

  constructor(private readonly zone: NgZone) {
    // fromEvent necesita correr dentro de la zona Angular para que el CD funcione
    this.zone.runOutsideAngular(() => {
      merge(
        fromEvent(window, 'online').pipe(map(() => true)),
        fromEvent(window, 'offline').pipe(map(() => false)),
      ).subscribe((online) => {
        this.zone.run(() => this._online$.next(online));
      });
    });
  }

  /** Observable que emite true/false cuando cambia la conectividad. */
  isOnline$(): Observable<boolean> {
    return this._online$.asObservable();
  }

  /** Valor síncrono del estado actual. */
  getCurrentStatus(): boolean {
    return this._online$.value;
  }
}
