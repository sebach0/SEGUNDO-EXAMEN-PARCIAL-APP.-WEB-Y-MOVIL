# TESTING_STRATEGY.md
# =========================================================
# Estrategia de pruebas API (basada en este proyecto)
# Última actualización: 2026-04-26
# =========================================================

## Nota: plantilla `pruebas_api_servicio.docx` (Word)

- Desde el IDE **no se puede leer** el binario `.docx`; se usó además el contenido de la captura que compartiste.
- En la plantilla aparece **Prueba 2: Crear servicio** con:
  - `POST /servicios`
  - Cuerpo tipo `{ "nombre": "Spa", "horario_inicio": "08:00", "horario_final": "18:00" }`
  - Esperado **201 Created** y objeto creado con `id` generado.

**Ese contrato no existe** en nuestro backend: no hay recurso `POST /api/servicios` con esos campos.  
En **EmergenciasViales**, “servicio” se modela como **solicitud de emergencia** + flujo de **bandeja del taller** (aceptar / rechazar / asignar), no como un CRUD de “salón Spa + horario”.

## Mapeo sugerido (misma intención de prueba, dominio real)

| Idea en el Word | Endpoint real en el proyecto | Código típico | Rol / permisos |
|-----------------|-----------------------------|---------------|----------------|
| **Crear** un servicio (alta) | `POST /api/app/cliente/emergencias` | `201` | Cliente, `incidentes:crear` |
| **Aceptar** un servicio (taller toma el caso) | `POST /api/app/taller/emergencias/bandeja/{bandeja_id}/aceptar` | `200` | Taller responsable, `solicitudes_taller:aceptar` |

- Para **alta** el cuerpo real es `SolicitudEmergenciaCreateIn` (p. ej. `vehiculo_id`, `descripcion_texto`, `ubicacion_inicial` opcional), no `nombre` + horarios de apertura.
- Los horarios fijos de un negocio tipo “08:00–18:00” **no** forman parte de un `POST` actual de “crear servicio” en la API; la disponibilidad del taller se gestiona vía `GET/PUT /api/app/taller/emergencias/disponibilidad` (otro contrato: banderas, capacidad, observación — ver Swagger).

## Alcance

En este proyecto, el concepto "servicio" se corresponde con **solicitudes en bandeja del taller**.

Endpoints reales usados para estas pruebas:

- `GET /api/app/taller/emergencias/bandeja/{bandeja_id}` (detalle por ID)
- `GET /api/app/taller/emergencias/bandeja/disponibles` (lista)

Permiso requerido del rol taller responsable: `solicitudes_taller:leer`.

## Convenciones

- **Tipo de prueba:** API funcional.
- **Ambiente recomendado:** Docker local (`docker compose up -d`).
- **Autenticación:** incluir `Authorization: Bearer <token>` si la ruta lo exige.
- **Formato de respuesta:** JSON.
- **Resultados esperados:** se validan tanto código HTTP como estructura de payload.

## Casos de prueba (alineados al backend actual)

### Prueba 1 — Obtener servicio existente
- **Ruta:** `GET /api/app/taller/emergencias/bandeja/{bandeja_id}`
- **Descripción:** obtiene un servicio por ID válido.
- **Entrada:** `bandeja_id=1` (existente para el taller autenticado)
- **Esperado:** objeto `SolicitudBandejaDetalleRead`, código `200`.
- **Resultado esperado final:** se retorna correctamente el servicio.

### Prueba 2 — Obtener servicio inexistente
- **Ruta:** `GET /api/app/taller/emergencias/bandeja/{bandeja_id}`
- **Descripción:** intenta obtener un servicio no registrado.
- **Entrada:** `bandeja_id=9999`
- **Esperado:** `404`.
- **Resultado esperado final:** servicio no encontrado.

### Prueba 3 — Obtener servicio con ID inválido (no numérico)
- **Ruta:** `GET /api/app/taller/emergencias/bandeja/{bandeja_id}`
- **Descripción:** envía ID no parseable.
- **Entrada:** `bandeja_id='abc'`
- **Esperado:** error de validación (`422` en FastAPI por path param inválido).
- **Resultado esperado final:** solicitud rechazada por formato de ID.

### Prueba 4 — Obtener servicio con ID negativo
- **Ruta:** `GET /api/app/taller/emergencias/bandeja/{bandeja_id}`
- **Descripción:** consulta con ID fuera de rango.
- **Entrada:** `bandeja_id=-1`
- **Esperado:** `404` (si no existe) o validación de dominio.
- **Resultado esperado final:** no debe devolver un servicio válido.

### Prueba 5 — Obtener servicio después de eliminarlo
- **Ruta:** `GET /api/app/taller/emergencias/bandeja/{bandeja_id}`
- **Descripción:** verifica consistencia tras cambio de estado que saca la fila de "disponibles".
- **Entrada:** `bandeja_id` previamente aceptado/rechazado.
- **Esperado:** detalle consistente con nuevo estado, o `404` si ya no corresponde al taller.
- **Resultado esperado final:** no vuelve a aparecer como servicio disponible.

### Prueba 6 — Obtener servicio múltiples veces
- **Ruta:** `GET /api/app/taller/emergencias/bandeja/{bandeja_id}`
- **Descripción:** verifica consistencia en consultas repetidas.
- **Entrada:** `bandeja_id` válido.
- **Esperado:** misma data y mismo esquema en todas las llamadas.
- **Resultado esperado final:** respuesta consistente (sin variaciones).

### Prueba 7 — Obtener servicio después de actualización
- **Ruta:** `GET /api/app/taller/emergencias/bandeja/{bandeja_id}`
- **Descripción:** valida reflejo tras operaciones (`aceptar` / `rechazar` / `asignar técnico`).
- **Entrada:** `bandeja_id` actualizado por flujo previo.
- **Esperado:** estado/datos operativos reflejan cambios.
- **Resultado esperado final:** la respuesta muestra transición correcta.

### Prueba 8 — Obtener lista de servicios
- **Ruta:** `GET /api/app/taller/emergencias/bandeja/disponibles`
- **Descripción:** obtiene listado completo.
- **Entrada:** sin parámetros.
- **Esperado:** lista JSON `BandejaIncidenteBaseRead[]`, código `200`.
- **Resultado esperado final:** lista retornada correctamente.

### Prueba 9 — Obtener lista vacía
- **Ruta:** `GET /api/app/taller/emergencias/bandeja/disponibles`
- **Descripción:** consulta sin registros.
- **Entrada:** base sin servicios.
- **Esperado:** `[]`, código `200`.
- **Resultado esperado final:** lista vacía válida.

### Prueba 10 — Obtener lista con muchos registros
- **Ruta:** `GET /api/app/taller/emergencias/bandeja/disponibles`
- **Descripción:** evalúa comportamiento con volumen alto.
- **Entrada:** base con muchos registros.
- **Esperado:** respuesta correcta sin errores de estructura (ideal medir latencia y tamaño payload).
- **Resultado esperado final:** lista completa o paginada según contrato.

## Plantilla de ejecución manual (curl)

```bash
# Servicio por ID (detalle de bandeja)
curl -i -X GET "http://localhost:8000/api/app/taller/emergencias/bandeja/1" \
  -H "Authorization: Bearer <TOKEN>"

# Lista de servicios disponibles para taller
curl -i -X GET "http://localhost:8000/api/app/taller/emergencias/bandeja/disponibles" \
  -H "Authorization: Bearer <TOKEN>"
```

## Criterios de aceptación mínimos

- Códigos HTTP alineados al contrato.
- Payload estable en estructura y tipos.
- Errores controlados en entradas inválidas.
- Consistencia entre lecturas repetidas.
- Integridad de lectura tras update/delete.

---

## Prueba 2 (Word) — “Crear servicio” ≈ este proyecto

### Variante A — Crear solicitud de emergencia (alta del “servicio” en el negocio)

- **Ruta:** `POST /api/app/cliente/emergencias`
- **Tipo:** `POST`
- **Autenticación:** Bearer de usuario con rol cliente.
- **Permiso:** `incidentes:crear`
- **Cuerpo de ejemplo (esquema real):**

```json
{
  "vehiculo_id": 1,
  "descripcion_texto": "Asistencia vial — requiere grúa",
  "ubicacion_inicial": null
}
```

- **Esperado:** `201 Created`, cuerpo `SolicitudEmergenciaDetailRead` con `id` de solicitud generado.
- **Resultado:** la solicitud queda registrada y puede aparecer en bandeja de talleres.

```bash
curl -i -X POST "http://localhost:8000/api/app/cliente/emergencias" \
  -H "Authorization: Bearer <TOKEN_CLIENTE>" \
  -H "Content-Type: application/json" \
  -d "{\"vehiculo_id\":1,\"descripcion_texto\":\"Prueba API\"}"
```

### Variante B — Taller acepta el servicio (transición en bandeja)

- **Ruta:** `POST /api/app/taller/emergencias/bandeja/{bandeja_id}/aceptar`
- **Tipo:** `POST`
- **Autenticación:** Bearer de usuario **taller responsable** del taller que corresponde a la fila.
- **Permiso:** `solicitudes_taller:aceptar`
- **Esperado:** `200 OK` con `SolicitudBandejaDetalleRead` actualizado (estado distinto a pendiente según lógica).
- **Nota:** no es un `201` de “creación” del recurso raíz, sino confirmación de aceptación; el código **200** es el del router actual.

```bash
curl -i -X POST "http://localhost:8000/api/app/taller/emergencias/bandeja/1/aceptar" \
  -H "Authorization: Bearer <TOKEN_TALLER>"
```

