import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import {
  Observable,
  catchError,
  map,
  mergeMap,
  of,
  switchMap,
  tap,
  throwError,
} from 'rxjs';
import { environment } from '../../../environments/environment';
import type { MeResponse, TokenResponse } from '../models/auth.models';

const ACCESS = 'ev_taller_access';
const REFRESH = 'ev_taller_refresh';
const ME = 'ev_taller_me';

@Injectable({ providedIn: 'root' })
export class TallerAuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);

  private storage(sessionOnly: boolean): Storage {
    return sessionOnly ? sessionStorage : localStorage;
  }

  private activeStorage(): Storage | null {
    if (localStorage.getItem(ACCESS)) return localStorage;
    if (sessionStorage.getItem(ACCESS)) return sessionStorage;
    return null;
  }

  getAccessToken(): string | null {
    return localStorage.getItem(ACCESS) ?? sessionStorage.getItem(ACCESS);
  }

  getMe(): MeResponse | null {
    const raw = localStorage.getItem(ME) ?? sessionStorage.getItem(ME);
    if (!raw) return null;
    try {
      return JSON.parse(raw) as MeResponse;
    } catch {
      return null;
    }
  }

  isTallerSession(): boolean {
    const me = this.getMe();
    const token = this.getAccessToken();
    return !!(token && me?.roles?.includes('TALLER_RESPONSABLE'));
  }

  clearSession(): void {
    for (const s of [localStorage, sessionStorage]) {
      s.removeItem(ACCESS);
      s.removeItem(REFRESH);
      s.removeItem(ME);
    }
  }

  logout(): void {
    const token = this.getAccessToken();
    if (!token) {
      this.clearSession();
      void this.router.navigate(['/taller']);
      return;
    }
    this.http
      .post(`${environment.apiUrl}/auth/logout`, {}, { headers: { Authorization: `Bearer ${token}` } })
      .subscribe({
        next: () => {
          this.clearSession();
          void this.router.navigate(['/taller']);
        },
        error: () => {
          this.clearSession();
          void this.router.navigate(['/taller']);
        },
      });
  }

  login(email: string, password: string, remember: boolean): Observable<void> {
    const url = `${environment.apiUrl}/auth/login`;
    return this.http.post<TokenResponse>(url, { email, password }).pipe(
      switchMap((tokens) =>
        this.fetchMe(tokens.access_token).pipe(
          mergeMap((me) => {
            if (!me.roles?.includes('TALLER_RESPONSABLE')) {
              return throwError(
                () =>
                  new TallerAuthError(
                    'FORBIDDEN_ROLE',
                    'Tu cuenta no es responsable de taller. Usa el acceso de administración si eres admin.',
                  ),
              );
            }
            this.persist(tokens, me, remember);
            return of(undefined);
          }),
        ),
      ),
      catchError((err) => {
        this.clearSession();
        return throwError(() => err);
      }),
    );
  }

  private fetchMe(accessToken: string): Observable<MeResponse> {
    return this.http.get<MeResponse>(`${environment.apiUrl}/auth/me`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
  }

  private persist(tokens: TokenResponse, me: MeResponse, remember: boolean): void {
    this.clearSession();
    const s = this.storage(!remember);
    s.setItem(ACCESS, tokens.access_token);
    s.setItem(REFRESH, tokens.refresh_token);
    s.setItem(ME, JSON.stringify(me));
  }

  hydrateMeIfNeeded(): Observable<boolean> {
    const token = this.getAccessToken();
    if (!token) return of(false);
    if (this.getMe()) return of(this.isTallerSession());
    return this.fetchMe(token).pipe(
      tap((me) => {
        const s = this.activeStorage();
        if (s) s.setItem(ME, JSON.stringify(me));
      }),
      map((me) => me.roles?.includes('TALLER_RESPONSABLE') ?? false),
      catchError(() => {
        this.clearSession();
        return of(false);
      }),
    );
  }

  /**
   * Vuelve a pedir /auth/me y actualiza localStorage/sessionStorage.
   * Útil tras migraciones que añaden permisos al rol (sin cerrar sesión).
   */
  refreshMeSiHaySesion(): Observable<boolean> {
    const token = this.getAccessToken();
    if (!token) return of(false);
    return this.fetchMe(token).pipe(
      tap((me) => {
        const s = this.activeStorage();
        if (s) s.setItem(ME, JSON.stringify(me));
      }),
      map(() => true),
      catchError(() => of(false)),
    );
  }
}

export class TallerAuthError extends Error {
  constructor(
    readonly code: string,
    override readonly message: string,
  ) {
    super(message);
    this.name = 'TallerAuthError';
  }
}
