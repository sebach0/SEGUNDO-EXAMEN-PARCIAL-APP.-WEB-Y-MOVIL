# Sesión 2026-06-07 — Cotización automática traslado del técnico

## Objetivo

Al enviar una cotización desde el portal taller, agregar automáticamente el costo de traslado del técnico al lugar de la emergencia: **5 Bs por km** (configurable).

## Implementación

### Backend

- `COTIZACION_TARIFA_TRASLADO_BS_KM` en `app/core/config.py` (default `5.0`).
- `CotizacionContextoRead`: `tarifa_traslado_bs_km`, `costo_traslado_estimado`.
- `proponer_cotizacion`: calcula distancia (Haversine taller ↔ incidente), agrega ítem
  `Traslado del técnico al lugar de la emergencia` (cantidad = km, P.U. = tarifa),
  `monto_total` = monto servicio + traslado.

### Frontend taller

- Resumen con traslado estimado y total al cliente (servicio + traslado).
- Historial muestra desglose de ítems.

### Mobile cliente

- Tarjeta de cotización: filas Traslado / Servicio / Total.
- Desglose resalta línea de traslado.

## Configuración

```env
COTIZACION_TARIFA_TRASLADO_BS_KM=5
```

Requiere ubicación del taller (`Mi taller`) y GPS del incidente para calcular distancia.
