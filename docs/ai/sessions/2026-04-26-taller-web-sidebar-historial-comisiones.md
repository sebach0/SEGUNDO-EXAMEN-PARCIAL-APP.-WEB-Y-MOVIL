# Sesión 2026-04-26 — Panel taller web: sidebar historial, mis solicitudes, comisiones

## Objetivo

Tras aceptar una solicitud deja de aparecer en la bandeja **Solicitudes disponibles**; el responsable necesitaba rutas para volver a ver casos y consultar finanzas.

## Cambios

### Backend (`taller_emergencias`)

- `HistorialAtencionRead` y consulta `list_historial_atenciones_taller`: se añade **`bandeja_id`** (join `solicitud_taller_bandeja` por `solicitud_id` + `taller_id` de la solicitud) para enlazar al detalle existente `GET .../bandeja/{bandeja_id}`.
- `ComisionTallerRead` y `list_comisiones_taller_con_pago`: mismo **`bandeja_id`** opcional para el enlace «Ver solicitud» desde comisiones.

### Frontend (Angular)

- Sidebar (`taller-shell.component.ts`): **Mis solicitudes**, **Historial de atenciones**, **Servicios asignados**, **Comisiones** (permisos `historial_atenciones:leer` y `comisiones:leer`).
- Rutas lazy: `emergencias/mis-solicitudes`, `emergencias/historial`, `emergencias/servicios-asignados`, `emergencias/comisiones`.
- Componente reutilizable `TallerEmergenciasHistorialListComponent` (`historialModo`: mis | historial | servicios).
- `TallerEmergenciasComisionesComponent`: resumen + tabla; `TallerEmergenciasApiService`: `listHistorialAtenciones`, `getResumenComisiones`, `listComisiones`.

## Verificación

- `npx ng build --configuration=development` (OK).

## Notas

- Si `bandeja_id` es null (datos legacy sin fila de bandeja), la UI no muestra enlace a detalle.
