# Sesión 2026-06-07 — Mapa ubicación taller + oferta minimalista

## Objetivo

1. Permitir marcar la ubicación del taller en mapa (Mi taller), similar al registro de incidente.
2. Usar esas coordenadas para calcular distancia y ETA al armar la oferta al cliente.
3. Rediseñar la UI de cotizaciones con layout más minimalista y ordenado.

## Backend

- `MiTallerUpdate` / `MiTallerRead`: campos `latitud`, `longitud`.
- `build_mi_taller_read()` expone coords del taller.
- `CotizacionContextoRead`: `taller_tiene_ubicacion`, `taller_lat/lng`, `incidente_lat/lng`, `eta_sugerida_min`.
- `contexto_oferta_taller()`: ETA sugerida ≈ distancia / 35 km/h urbano (mín. 5 min).

## Frontend

- Dependencia `leaflet` + `@types/leaflet`; CSS en `angular.json`.
- Nuevo `OsmMapPickerComponent` (`shared/components/osm-map-picker/`):
  - Click para marcar, botón «Usar mi ubicación», marcadores primario/secundario, línea punteada.
- `taller-mi-taller`: sección mapa + guardado lat/lng en `PATCH /mi-taller`.
- `taller-cotizaciones`: UI minimalista, resumen distancia/ETA, mapa taller↔incidente, auto-fill ETA sugerida.

## Flujo de prueba

1. Login taller: `luis.rivera@sc-demo.test` / `scdemo1`.
2. `/taller/panel/mi-taller` → marcar ubicación → Guardar.
3. Ir a cotización de una solicitud activa → ver distancia, ETA y mapa.
4. Enviar oferta con botón «Usar ~X min» para ETA.

## Archivos clave

- `frontend/src/app/shared/components/osm-map-picker/*`
- `frontend/src/app/taller/features/mi-taller/*`
- `frontend/src/app/taller/features/cotizaciones/*`
- `backend/app/modules/talleres_y_tecnicos/taller_responsable/schemas.py`
- `backend/app/modules/cotizaciones/schemas.py` + `service.py`

## Fix mapa fragmentado + selección de ubicación (2026-06-07)

**Síntoma:** mapa Leaflet se mostraba partido/disperso en varios bloques y el clic
no marcaba bien la ubicación.

**Causa raíz:** el CSS de Leaflet NO se incrustaba en el bundle.
- `@import 'leaflet/dist/leaflet.css'` en `styles.scss` → Sass lo deja como import nativo, no inlinea.
- `@import 'leaflet/dist/leaflet'` (sin extensión) → tampoco resuelve desde `node_modules`.
- Entrada en `angular.json > styles` con `node_modules/leaflet/dist/leaflet.css` → en este
  Angular 17 + esbuild **no terminaba bundleando** el archivo (styles.css no crecía).

**Solución definitiva (a prueba de balas):**
- Copiado `leaflet.css` + `images/` a `frontend/src/assets/leaflet/`.
- `<link rel="stylesheet" href="assets/leaflet/leaflet.css">` en `src/index.html`.
- Revertidas las entradas de `angular.json` (quedó solo `src/styles.scss`).

**Mejoras componente `OsmMapPickerComponent`:**
- Doble `requestAnimationFrame` antes de inicializar el mapa (layout listo).
- `ResizeObserver` → `invalidateSize()` automático.
- Eventos Leaflet (`click`, `dragend`) envueltos en `NgZone.run()` + `markForCheck()` (OnPush).
- Marcador arrastrable para ajuste fino.
- Feedback "✓ Ubicación seleccionada" con coords.

**Nota:** si Leaflet se actualiza de versión, re-copiar `node_modules/leaflet/dist/leaflet.css`
a `src/assets/leaflet/`.
