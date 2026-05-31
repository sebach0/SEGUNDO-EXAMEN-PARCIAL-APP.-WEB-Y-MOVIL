/** Respuesta de `POST /auth/login` */
export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

/** Respuesta de `GET /auth/me` */
export interface MeResponse {
  id: number;
  nombres: string;
  apellidos: string;
  email: string;
  username: string;
  roles: string[];
  permisos: string[];
}
