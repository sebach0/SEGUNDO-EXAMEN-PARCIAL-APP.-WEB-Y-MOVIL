# Sesión 2026-06-06 — Ciclo 4 Mobile: Cotizaciones y Cancelación

## Objetivo
Implementar las funcionalidades pendientes del Ciclo #4 en la app Flutter (cliente): comparación/selección de cotizaciones y cancelación de solicitud con motivo.

## Trabajo realizado

### 1. Estructura de carpetas creada
```
mobile/lib/cliente/cotizaciones/
  domain/     → cotizacion_models.dart
  data/       → cotizacion_repository.dart
  application/→ cotizacion_providers.dart
  presentation/screens/ → cotizaciones_list_screen.dart
```

### 2. Modelos Dart (`cotizacion_models.dart`)
- `EstadoCotizacion` enum: `ENVIADA`, `ACEPTADA`, `RECHAZADA`, `EXPIRADA` con `etiqueta` y flags `isActive`/`isSelected`.
- `CotizacionItem`: id, descripcion, cantidad, precioUnitario, subtotal.
- `Cotizacion`: completa con tallerId, tallerNombre, estado, descripcionDanio, detalleServicio, montoTotal, ETAs, incluyeGrua, garantia, comentarios, items[].

### 3. Repositorio (`cotizacion_repository.dart`)
- `listBySolicitud(solicitudId)` → `GET /cotizaciones/solicitudes/{id}`
- `seleccionar(solicitudId, cotizacionId)` → `POST /cotizaciones/solicitudes/{sid}/cotizacion/{cid}/seleccionar`
- Manejo de errores con `messageFromDio`.

### 4. Providers Riverpod (`cotizacion_providers.dart`)
- `cotizacionRepositoryProvider` (Provider simple).
- `cotizacionesBySolicitudProvider` (FutureProvider.autoDispose.family).
- `SeleccionarCotizacionNotifier` (AsyncNotifier) + `seleccionarCotizacionProvider`.

### 5. Pantalla `CotizacionesListScreen`
- Lista cotizaciones agrupadas: ACEPTADA primero, luego ENVIADAS (activas), luego resto.
- Tarjetas `_CotizacionCard` con todos los campos del modelo.
- Desglose de ítems línea a línea.
- Botón "Seleccionar" → diálogo de confirmación → POST → ShadToast → refresh.
- Banners informativos para estado "ya seleccionada" o "sin cotizaciones activas".
- Estados bloqueados (EXPIRADA/RECHAZADA) con opacidad reducida.

### 6. Cancelación de solicitud
- `EmergenciasRepository.cancelarSolicitud(id, motivo)` → `POST /app/cliente/emergencias/{id}/cancelar`.
- `CancelarSolicitudNotifier` y `cancelarSolicitudProvider` en `emergencias_providers.dart`.
- `EmergenciaDetalleScreen` reescrita como `ConsumerStatefulWidget`:
  - Botón "Ver cotizaciones de talleres" → navega a `/cotizaciones`.
  - Botón "Cancelar solicitud" (solo en estados activos: no FINALIZADA ni CANCELADA).
  - Diálogo con `TextFormField` validado (motivo obligatorio, mínimo 5 chars).
  - `ShadToast` de éxito/error, invalidación de providers al cancelar.

### 7. Routing (`cliente_go_router.dart`)
- Nueva ruta `/cliente/app/emergencias/solicitudes/:sid/cotizaciones` → `CotizacionesListScreen`.

### 8. API Constants (`api_constants.dart`)
- `appClienteEmergenciaCancelar(id)`
- `cotizacionesDeSolicitud(solicitudId)`
- `seleccionarCotizacion(solicitudId, cotizacionId)`

## Resultado
- `flutter analyze --no-pub` → **0 issues**.
- Toda la implementación respeta la arquitectura feature-first existente.
- Los nuevos archivos siguen el patrón `domain → data → application → presentation`.

## Flujo completo Ciclo 4 (mobile)
```
[Cliente abre solicitud]
        ↓
EmergenciaDetalleScreen
  ├── "Ver cotizaciones" → CotizacionesListScreen
  │       ├── Lista cotizaciones (GET /cotizaciones/solicitudes/{id})
  │       └── Seleccionar → diálogo → POST → ACEPTADA, demás EXPIRADAS
  └── "Cancelar solicitud" → diálogo (motivo) → POST /cancelar → CANCELADA
```

## Casos de uso cubiertos
- **CU nuevo**: comparar cotizaciones móvil → seleccionar taller.
- **CU cancelación**: cliente cancela desde móvil con motivo guardado en BD.
