# Sesión 2026-06-07 — Asignación automática de técnico disponible

## Objetivo

Cuando el taller gana una emergencia (cliente elige cotización), asignar automáticamente al **primer técnico disponible** del taller y marcarlo **OCUPADO**. La siguiente emergencia toma el siguiente técnico libre.

## Backend

- `elegir_tecnico_disponible`: ACTIVO + disponibilidad ≠ OCUPADO + sin solicitudes activas (FIFO por `id`).
- `asignar_tecnico_automatico`: wrapper sobre `asignar_tecnico_a_solicitud`.
- Al asignar: `disponibilidad = OCUPADO`.
- Al finalizar servicio o cancelar solicitud: `liberar_tecnico_si_sin_servicios` → `DISPONIBLE`.
- Hook en `seleccionar_cotizacion` tras `TALLER_ASIGNADO`.
- Endpoint: `POST .../asignar-tecnico-automatico`.

## Frontend taller

- Detalle incidente: retry auto si quedó `TALLER_ASIGNADO` sin técnico.
- Select muestra Disponible/Ocupado; botón "Asignar automáticamente".
