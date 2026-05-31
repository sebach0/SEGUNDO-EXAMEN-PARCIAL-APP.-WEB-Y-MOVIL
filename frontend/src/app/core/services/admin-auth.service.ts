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

const ACCESS = 'ev_admin_access';
const REFRESH = 'ev_admin_refresh';
const ME = 'ev_admin_me';

@Injectable({ providedIn: 'root' })
export class AdminAuthService {
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

  isAdminSession(): boolean {
    const me = this.getMe();
    const token = this.getAccessToken();
    return !!(token && me?.roles?.includes('ADMIN'));
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
      void this.router.navigate(['/admin']);
      return;
    }
    this.http
      .post(`${environment.apiUrl}/auth/logout`, {}, { headers: { Authorization: `Bearer ${token}` } })
      .subscribe({
        next: () => {
          this.clearSession();
          void this.router.navigate(['/admin']);
        },
        error: () => {
          this.clearSession();
          void this.router.navigate(['/admin']);
        },
      });
  }

  /**
   * Login + verificación rol ADMIN vía `/auth/me`.
   */
  login(email: string, password: string, remember: boolean): Observable<void> {
    const url = `${environment.apiUrl}/auth/login`;
    return this.http.post<TokenResponse>(url, { email, password }).pipe(
      switchMap((tokens) =>
        this.fetchMe(tokens.access_token).pipe(
          mergeMap((me) => {
            if (!me.roles?.includes('ADMIN')) {
              return throwError(
                () =>
                  new AdminAuthError(
                    'FORBIDDEN_ROLE',
                    'Tu cuenta no tiene rol de administrador.',
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

  /** Si hay token pero no `me` en storage, rehidrata (p. ej. pestaña nueva). */
  hydrateMeIfNeeded(): Observable<boolean> {
    const token = this.getAccessToken();
    if (!token) {
      return of(false);
    }
    if (this.getMe()) {
      return of(this.isAdminSession());
    }
    return this.fetchMe(token).pipe(
      tap((me) => {
        const s = this.activeStorage();
        if (s) s.setItem(ME, JSON.stringify(me));
      }),
      map((me) => me.roles?.includes('ADMIN') ?? false),
      catchError(() => {
        this.clearSession();
        return of(false);
      }),
    );
  }
}

export class AdminAuthError extends Error {
  constructor(
    readonly code: string,
    override readonly message: string,
  ) {
    super(message);
    this.name = 'AdminAuthError';
  }
}
