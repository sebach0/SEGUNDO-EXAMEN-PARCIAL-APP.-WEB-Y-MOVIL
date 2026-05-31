import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

/** Endpoints públicos de `/api/auth/*` (sin Bearer). */
@Injectable({ providedIn: 'root' })
export class AuthPublicApiService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/auth`;

  solicitarRecuperacionContrasena(email: string): Observable<void> {
    return this.http.post<void>(`${this.base}/solicitar-recuperacion-contrasena`, { email });
  }

  restablecerContrasena(token: string, password: string): Observable<void> {
    return this.http.post<void>(`${this.base}/restablecer-contrasena`, { token, password });
  }
}
