// src/environments/environment.ts
// =========================================================
// Entorno de DESARROLLO
// Los valores de producción van en environment.production.ts
// Angular sustituye automáticamente el archivo al compilar con --configuration production
// =========================================================
import { mailhogWebUrl as mailhogWebUrlFromEnv } from './mailhog-url.generated';

export const environment = {
  production: false,
  /** Dev: mismo origen vía proxy.conf.js → BACKEND_URL en .env raíz */
  apiUrl: '/api',
  appName: 'Plataforma Emergencias Vehiculares',
  /** UI MailHog: definir MAILHOG_WEB_URL en `.env` raíz y ejecutar `npm run env:sync` (o `npm start`). */
  mailhogWebUrl: mailhogWebUrlFromEnv,
};
