// src/environments/environment.production.ts
// =========================================================
// Entorno de PRODUCCIÓN
// La URL del backend viene de una variable de entorno del build
// En Azure VM: nginx hace proxy /api/ → backend:8000
// =========================================================
export const environment = {
  production: true,
  apiUrl: '/api',   // Relativo — nginx hace proxy al backend
  appName: 'Plataforma Emergencias Vehiculares',
  mailhogWebUrl: '',
};
