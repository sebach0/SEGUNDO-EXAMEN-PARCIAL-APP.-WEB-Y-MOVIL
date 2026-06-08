// src/environments/environment.production.ts
// =========================================================
// Entorno de PRODUCCIÓN
// La URL del backend viene de una variable de entorno del build
// En Azure VM: nginx hace proxy /api/ → backend:8000
// =========================================================
export const environment = {
  production: true,
  apiUrl: 'https://segundo-examen-backend.onrender.com/api',
  appName: 'Plataforma Emergencias Vehiculares',
  mailhogWebUrl: '',
};
