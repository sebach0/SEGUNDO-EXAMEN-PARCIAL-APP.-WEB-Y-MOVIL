# Sesión 2026-04-25 — Limpieza de copy (Ciclo/CU)

## Objetivo
Eliminar textos visibles no profesionales en frontend y mobile que exponían etiquetas internas de planificación (`Ciclo X`, `fase X`, `CUxx`).

## Cambios aplicados
- Frontend Angular (`frontend/src/app/...`):
  - Login/recover/register admin y taller.
  - Shell admin/taller.
  - Dashboard, usuarios, talleres, bitácora, permisos, roles.
  - Bandeja/disponibilidad/detalle de emergencias del taller.
  - Comentario de servicio `taller-emergencias-api.service.ts`.
- Mobile Flutter (`mobile/lib/...`):
  - Wizard, seguimiento y detalle de emergencias cliente.
  - Selector de actor.
  - Constantes API y varios comentarios descriptivos en cliente/técnico.
  - Comentario en `mobile/pubspec.yaml`.

## Verificación
- Búsqueda global sin resultados para patrones `Ciclo\\d`, `ciclo\\d`, `CU\\d` en:
  - `frontend/src`
  - `mobile/lib`
  - `mobile/pubspec.yaml`

## Resultado
Copy más limpio y profesional, sin exponer nomenclatura interna de análisis/planificación al usuario final.
