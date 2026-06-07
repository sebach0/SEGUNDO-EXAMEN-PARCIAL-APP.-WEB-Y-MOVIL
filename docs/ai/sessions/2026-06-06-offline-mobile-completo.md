# Sesión 2026-06-06 — Offline móvil completo (wizard + sync)

## Alcance completado

### Mobile Flutter
- Cola v2 (`emergencias_offline_queue_v2`) con borrador completo: descripción, ubicación, evidencias locales, texto adicional, `client_uuid`, anti-duplicado.
- Copia persistente de fotos/audio en `offline_emergencias/{uuid}/` (`OfflineEmergenciaStorage`).
- Wizard 6 pasos en **modo offline**: continúa sin red, chip "Offline" en AppBar, pantalla final con sync manual.
- Sync al reconectar: POST `/api/app/cliente/emergencias/sync` + subida de evidencias + patch texto (caso híbrido online→offline).
- Auto-sync: al iniciar app, al volver al foreground y cada 25 s si hay pendientes (solo cliente autenticado).
- UI: banner en Home, Mis solicitudes y botón Sync.

### Backend
- Sin cambios de schema; endpoint sync existente reutilizado.

### Angular (taller PWA)
- Ya tenía IndexedDB + `SyncService` + banner en `app.component.ts` (Ciclo 4 incidentes). No modificado en esta sesión.

## Prueba manual

1. Modo avión → reportar emergencia completa (ubicación + foto opcional).
2. Ver banner "1 reporte(s) offline pendiente(s)".
3. Desactivar modo avión → SnackBar de sincronización.
4. Ver solicitud en "Mis solicitudes".
