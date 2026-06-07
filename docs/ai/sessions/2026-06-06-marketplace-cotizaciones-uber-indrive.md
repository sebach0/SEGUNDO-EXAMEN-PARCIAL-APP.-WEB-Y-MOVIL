# Sesión 2026-06-06 — Marketplace emergencias (modelo Uber/InDrive)

## Objetivo
Cliente crea emergencia → talleres compiten con cotización (precio, servicios, distancia) → cliente elige la mejor opción.

## Cambios

### Backend
- Migración `0018_marketplace_cotizaciones.sql` / Alembic `0010_marketplace_cotizaciones`: columnas `distancia_km`, `servicios_ofrecidos` en `cotizaciones`.
- `app/core/geo.py`: Haversine compartido.
- `cotizaciones/service.py`:
  - Calcula distancia taller↔ubicación del incidente al proponer.
  - Snapshot de servicios del taller (`taller_servicios`).
  - Notifica al cliente al recibir cotización.
  - Al seleccionar cotización: asigna taller, expira competencia, actualiza bandeja y ETA.
  - Lista ordenada por distancia y precio.
- `GET /cotizaciones/solicitudes/{id}/contexto-oferta` para el taller (distancia + servicios).
- `aceptar_solicitud` en bandeja → **409** (ya no aceptación directa).

### Frontend Angular (taller)
- Bandeja y detalle: botón **Cotizar** / **Enviar cotización** (reemplaza «Aceptar asistencia»).
- Pantalla cotizaciones: banner distancia + chips de servicios + formulario oferta.

### Mobile (cliente)
- Cards de cotización muestran **distancia km** y **chips de servicios**.
- Wizard y detalle: CTA «Comparar ofertas de talleres».

## Flujo
```
Cliente → POST emergencia → bandeja a talleres
Taller → POST /cotizaciones/solicitudes/{id} (precio, ETA, servicios, distancia auto)
Cliente → GET cotizaciones → POST .../seleccionar
  → taller asignado, bandeja ganadora, demás EXPIRADA
```

## Requisitos operativos
- Talleres con `latitud`/`longitud` y servicios en «Mis servicios» para distancia y chips completos.
- Migración: `docker compose exec backend alembic upgrade head`
