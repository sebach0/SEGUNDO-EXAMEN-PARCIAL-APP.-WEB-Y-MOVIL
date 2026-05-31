# 2026-04-26 — Dashboard admin financiero (comisiones + reportes)

## Objetivo

Mostrar en el panel administrador KPIs financieros reales de plataforma basados en `comisiones_taller` (10 %) y datos de pago, con filtros por rango de fechas.

## Implementación

- **Backend**
  - Nuevo módulo: `backend/app/modules/acceso_y_administracion/admin_finanzas/`
  - Endpoints:
    - `GET /api/admin/finanzas/resumen`
    - `GET /api/admin/finanzas/reportes`
  - Métricas: comisión total plataforma, total cobrado, ticket promedio, tasa de conversión pago, talleres con comisión, top talleres y serie diaria.

- **Frontend Angular**
  - Archivo: `frontend/src/app/admin/features/dashboard/admin-dashboard.*`
  - Secciones nuevas:
    - Filtro `desde`/`hasta` + botón actualizar.
    - Tarjetas KPI financieras.
    - Tabla top talleres por comisión.
    - Barras diarias de comisión plataforma.

## Nota operativa

Si hay pagos históricos confirmados antes del fix de generación de comisión, esos pagos no aparecerán en KPI de comisión hasta realizar backfill en `comisiones_taller`.

