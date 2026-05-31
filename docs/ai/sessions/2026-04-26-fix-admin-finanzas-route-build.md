# 2026-04-26 — Fix build frontend: ruta finanzas admin

## Problema

`docker compose up --build` fallaba en frontend con:

- `Could not resolve "./features/finanzas/admin-finanzas.component"`
- `TS2307: Cannot find module './features/finanzas/admin-finanzas.component'`

La ruta `/admin/panel/finanzas` existía en `admin.routes.ts`, pero el componente no.

## Solución

- Se creó `frontend/src/app/admin/features/finanzas/admin-finanzas.component.ts` (standalone).
- Se añadió template wrapper que reutiliza el dashboard financiero: `<app-admin-dashboard />`.
- Se agregaron archivos `html` y `scss` del componente.

## Resultado esperado

La compilación Angular en Docker deja de fallar por import faltante y se conserva navegación a `/admin/panel/finanzas`.

