# HANDOFF_LATEST.md
# =========================================================
# Handoff para el próximo agente/sesión
# Fecha: 2026-04-26

## Cambios recientes (2026-04-26) — Word `pruebas_api_servicio` + Prueba 2 mapeo ✅

- `docs/ai/TESTING_STRATEGY.md` incorpora: nota sobre el `.docx` (no leíble como texto en el IDE), explicación de que **no** hay `POST /servicios` con Spa/horarios, tabla y sección con **Prueba 2** equivalente a `POST /api/app/cliente/emergencias` (201) o `.../bandeja/{id}/aceptar` (200) + `curl` de ejemplo.
- Sesión: `docs/ai/sessions/2026-04-26-pruebas-api-servicio-docx-prueba-2.md`.

## Cambios recientes (2026-04-26) — Documentación pruebas API recurso `servicios` ✅

- Se creó `docs/ai/TESTING_STRATEGY.md` con 10 pruebas funcionales para `GET /servicios/{id}` y `GET /servicios` (existente, inexistente, ID inválido, ID negativo, post-delete, consistencia, post-update, lista completa, lista vacía y alto volumen).
- Se incluyó plantilla `curl`, criterios de aceptación y nota de mapeo: en el backend actual no hay ruta `/servicios` aún.
- Sesión: `docs/ai/sessions/2026-04-26-testing-strategy-servicios-api.md`.

## Cambios recientes (2026-04-26) — Dashboard admin financiero (KPIs comisiones/reportes) ✅

- Se implementó módulo backend `admin_finanzas` (`schemas.py`, `service.py`, `router.py`) para exponer métricas financieras globales desde `comisiones_taller`, `pagos` y `solicitudes_emergencia`: comisión total plataforma (10 %), pagos confirmados, ticket promedio, conversión de finalizadas→pagadas, top talleres y serie diaria.
- Se actualizó `frontend/src/app/admin/features/dashboard/` para mostrar filtros de fecha, tarjetas KPI, top talleres y barras diarias de comisión dentro del panel administrador.
- Fix posterior: `admin.routes.ts` apuntaba a `./features/finanzas/admin-finanzas.component` inexistente y rompía `ng build`; se creó ese componente (wrapper standalone que renderiza `admin-dashboard`) para que compile y mantenga ruta `/admin/panel/finanzas`.
- Sesión: `docs/ai/sessions/2026-04-26-admin-dashboard-finanzas-kpis.md`.

## Cambios recientes (2026-04-26) — Pagos: registrar `comisiones_taller` al confirmar (ganancias dashboard) ✅

- Tras `PAGADO` (Stripe o simulado) ahora se crea fila en `comisiones_taller` (10 % comisión, neto al taller), alineado a `dev_demo_santa_cruz`. Sin esto, el landing/reportes del taller seguían con sumas en 0. Código: `backend/app/modules/pagos_y_comisiones/pagos/repository.py` + `service.py`. Sesión: `docs/ai/sessions/2026-04-26-pagos-comisiones-taller-dashboard.md`.

## Cambios recientes (2026-04-27) — `ai_payload` fijo en “Otros” tras subir foto (re-enriquecer IA) ✅

- Tras **crear** la solicitud el flujo móvil suele añadir **foto/ubicación después**; el `enrich` solo corría al `POST` inicial, así que `fuentes` quedaba `["texto"]` y `OTROS`. Ahora: `enrich` también tras **evidencias**, **ubicación** y **actualizar texto**; lectura local de `uploads/evidencias` para análisis de imagen. Sesión: `docs/ai/sessions/2026-04-27-agent-ia-payload-reenrich-evidencia.md`.

## Cambios recientes (2026-04-26) — YOLO: modelo Colab dejó de “reconocer” (en realidad usaba COCO) ✅

- **Causa:** `.env` tenía `YOLO_MODEL=yolov8n.pt` y por defecto `YOLO_TASK=detect`; el contenedor nunca usaba el clasificador en `backend/incidentes_emergencias_v1.pt` salvo que se uniera `docker-compose.ai-custom-model.yml` y se forzara classify.
- **Ajuste:** `.env` con `YOLO_TASK=classify`, `YOLO_MODEL=/models/incidentes_emergencias_v1.pt`, `YOLO_IMGSZ=224` **y** levantar con **`docker compose -f docker-compose.yml -f docker-compose.ai-custom-model.yml --profile ai up -d --build --force-recreate ai-inference`** (el segundo archivo monta el `.pt` en `/models/...`). Sesión: `docs/ai/sessions/2026-04-26-yolo-custom-model-compose-env.md`.

## Cambios recientes (2026-04-26) — Docker: Postgres `db` healthcheck + primer `up` ✅

- `docker-compose.yml` (`db`): `healthcheck.start_period: 240s`, `retries: 12` — init largo + reinicio post-init ya no debería marcar `unhealthy` por carrera con `pg_isready`. Ver `docs/ai/DOCKER_BUILD_OPTIMIZATION.md`.

## Cambios recientes (2026-04-26) — Docker: contexto `ai-inference` acotado + builds más livianos ✅

- `docker-compose.yml`: build de `ai-inference` con `context: ./services/ai-inference` (no toda la repo). Backend: `COPY --chown` (sin `chown -R`). `.dockerignore` backend/frontend/ai-inference ampliados. Detalle: `docs/ai/DOCKER_BUILD_OPTIMIZATION.md`.

## Cambios recientes (2026-04-26) — `.env` solo en la raíz del repo ✅

- Eliminado `backend/.env.example`; `config.py` solo carga `<repo>/.env`. Plantilla única: `.env.example` raíz. `mobile/.env` intacto. Sesión: `docs/ai/sessions/2026-04-26-env-solo-raiz.md`.
- Compose: `.env.example` documenta `TZ`/`PGTZ`/`YOLO_TASK`/Firebase; YAML mantiene fallbacks seguros para TZ, host Postgres, credenciales Firebase y `BACKEND_UPSTREAM` (evita warnings y valores vacíos con `.env` viejos). Sesión: `docs/ai/sessions/2026-04-26-compose-env-estricto.md`.

## Cambios recientes (2026-04-26) — Panel taller Angular: historial, mis solicitudes, comisiones ✅

- Sidebar y rutas bajo `/taller/panel/emergencias/`: **Mis solicitudes**, **Historial de atenciones**, **Servicios asignados**, **Comisiones**; consumen APIs existentes (`historial-atenciones`, `comisiones`, `comisiones/resumen`). Backend: `bandeja_id` opcional en `HistorialAtencionRead` y `ComisionTallerRead` para enlazar al detalle de bandeja. Sesión: `docs/ai/sessions/2026-04-26-taller-web-sidebar-historial-comisiones.md`.

## Cambios recientes (2026-04-26) — Paquete `comunicacion_y_notificaciones` (4 módulos) ✅

- Movidos `comunicaciones`, `dispositivos_push`, `mensajes_solicitud`, `notificaciones` → `modules/comunicacion_y_notificaciones/`; imports `app.modules.comunicacion_y_notificaciones.*`. `main`, `db_metadata`, `pagos`, `tecnico`, `atencion/taller_emergencias`, seeds. Sesión: `docs/ai/sessions/2026-04-26-backend-comunicacion-y-notificaciones.md`.

## Cambios recientes (2026-04-26) — Paquete `atencion` (`taller_emergencias`) ✅

- `modules/taller_emergencias` → `modules/atencion/taller_emergencias/`; imports `app.modules.atencion.taller_emergencias.*`. `main`, seeds, `incidentes` (solicitudes), `ai/repository`, tests. Sesión: `docs/ai/sessions/2026-04-26-backend-atencion-taller-emergencias.md`.

## Cambios recientes (2026-04-26) — Paquete `talleres_y_tecnicos` (`talleres`, `taller_responsable`, `tecnico`) ✅

- Movidos desde raíz de `modules/`: `acceso_y_administracion/talleres` → `talleres_y_tecnicos/talleres`, `taller_responsable`, `tecnico`. Imports `app.modules.talleres_y_tecnicos.*`; `acceso_y_administracion/__init__.py` actualizado. Sesión: `docs/ai/sessions/2026-04-26-backend-talleres-y-tecnicos-paquete.md`.

## Cambios recientes (2026-04-26) — Paquete `incidentes` (`emergencias` bajo `incidentes/emergencias`) ✅

- Movido `modules/emergencias` → `modules/incidentes/emergencias/`; imports `app.modules.incidentes.emergencias.*`; `main`, `db_metadata`, taller/tecnico/pagos/mensajes/notificaciones/ai/seeds/tests actualizados. URLs sin cambio. Sesión: `docs/ai/sessions/2026-04-26-backend-incidentes-emergencias-paquete.md`.

## Cambios recientes (2026-04-26) — Paquete `clientes_y_vehiculos` (clientes + vehiculos) ✅

- Carpetas movidas a `backend/app/modules/clientes_y_vehiculos/{clientes,vehiculos}/`; imports globales actualizados (regex evita doble `clientes_y_vehiculos`). `main.py`, `db_metadata`, emergencias, pagos, técnico, seeds, etc. Sesión: `docs/ai/sessions/2026-04-26-backend-clientes-y-vehiculos-paquete.md`.

## Cambios recientes (2026-04-26) — Carpeta `acceso_y_administracion` (auth, permisos, roles, usuarios, bitácora, talleres) ✅

- Se movieron esos seis paquetes a `backend/app/modules/acceso_y_administracion/`; se añadió `__init__.py` del padre; `main.py`, `db_metadata.py`, `dependencies.py`, el resto de módulos, seeds y tests quedaron con imports `app.modules.acceso_y_administracion.*`. Verificar en Docker/venv: `python -c "from app.main import app"`. Sesión: `docs/ai/sessions/2026-04-26-backend-acceso-y-administracion-paquete.md`.

## Cambios recientes (2026-04-26) — Módulos backend: auth / roles / permisos + notificaciones / push / mensajes ✅

- El monolito `backend/app/modules/acceso/` se reemplazó por **`auth`**, **`roles`**, **`permisos`** (mismas tablas y prefijos API).
- `comunicaciones` ya no concentra modelos ni un solo `service.py` grande: **`notificaciones`**, **`dispositivos_push`**, **`mensajes_solicitud`**; `comunicaciones/router.py` solo ensambla rutas.
- Imports afectados: seeds, `dependencies.py`, `pagos`, `portal_*`, `db_metadata`. Ver `docs/ai/sessions/2026-04-26-backend-modulos-acceso-comunicaciones.md` y `ARCHITECTURE.md`.

## Cambios recientes (2026-04-26) — Identidades seed (Santa Cruz, cuentas naturales) ✅

- **`identidades_demo_sc.py`:** emails `*.sc-demo.test`, pass `scdemo1`, tel. +591 77010010–014, nombres y talleres con razón social SC; `config.py` importa estos defaults; `docker-compose.yml` deja de usar +57/La Paz en fallbacks.
- Sesión: `docs/ai/sessions/2026-04-26-seed-identidades-santa-cruz.md`.

## Cambios recientes (2026-04-26) — Seed stress visual (catálogo + clientes extra) ✅

- **`dev_stress_visual`:** clientes extra `*.lista.sc-demo.test` + nombres SC; **`identidades_demo_sc.py`** centraliza emails/tel/pass de admin/cliente/taller/técnico/taller2; **`ensure_catalogos_vehiculo_stress_extra`** sin cambios de lógica. `docker-compose.yml` defaults Bolivia (+591, Santa Cruz).

## Cambios recientes (2026-04-26) — AVIF + analyze-batch resiliente ✅

- **`ai-inference`:** `pillow-heif` + `libheif1` en Docker; `register_heif_opener()` en `main.py` para decodificar AVIF/HEIF.
- **`backend` `router.py`:** `POST /api/ai/images/analyze-batch` no hace 502 si una foto falla: esa entrada lleva `resultado` con `hallazgos` de error y `confianza=0`; el resto sigue normal. `POST /api/ai/images/analyze` (una imagen) mantiene 502 ante fallo de inferencia.
- **Docs:** `DECISIONS_LOG` DEC-016; sesión `docs/ai/sessions/2026-04-26-agent-avif-analyze-batch-resilience.md`.

## Cambios recientes (2026-04-26) — Seed demo media prioridad (comunicaciones, IA, multi-taller) ✅

- **`backend/app/seeds/dev_demo_media_prioridad.py`:** notificaciones, chat, `ai_payload` demo, disponibilidad taller SC, segundo taller La Paz + bandeja retroactiva en `[DEMO-SC]`. Se encadena después de `ensure_demo_santa_cruz_datos` en `python -m app.seeds` y en `lifespan` si `SEED_DEMO_MEDIA_PRIORIDAD_ON_START=true`. Variables `SEED_TALLER2_*` documentadas en `.env.example` (raíz del repo).

## Cambios recientes (2026-04-26) — Seed demo Santa Cruz (emergencias + pagos) ✅

- **`backend/app/seeds/dev_demo_santa_cruz.py`:** vehículos y 10 solicitudes demo con contexto Santa Cruz de la Sierra; `python -m app.seeds` las ejecuta al final. Variable opcional `SEED_DEMO_SANTA_CRUZ_ON_START` para lifespan. Defaults `SEED_*_CIUDAD` Santa Cruz en `config` / `.env.example`.

## Cambios recientes (2026-04-26) — Confirmación pago: reusa intent iniciado, PI id correcto

- **Mobile** `pago_confirmacion_screen.dart`: si el paso método ya devolvió `PagoRead` coherente, no se vuelve a `POST /pagos`; `confirmarStripe` usa `stripePaymentIntentId` del modelo.

## Cambios recientes (2026-04-26) — Pago resumen muestra presupuesto técnico real ✅

- **Backend** `emergencias/schemas.py`: `SolicitudEmergenciaRead` ahora incluye `presupuesto_bob` y `presupuesto_registrado_at`; `SolicitudEmergenciaDetailRead` los hereda y `GET /portal/cliente/emergencias/{id}` los devuelve al mobile.
- **Mobile** `pago_resumen_screen.dart`: se mantiene la regla “cliente no escribe monto”, y se agrega refresco explícito (botón en app bar + pull-to-refresh) para sincronizar de inmediato cuando el técnico registra presupuesto.
- **Causa raíz del bug reportado:** la pantalla de pago leía `emergenciaDetailProvider` (endpoint detalle), pero `presupuesto_bob` solo estaba en seguimiento; por eso podía mostrar “no definido” aunque backend ya tuviera monto.

## Cambios recientes (2026-04-26) — Daños IA en UI, pago = presupuesto, Stripe solo tarjeta, Android `FlutterFragmentActivity` ✅

- **IA (mobile):** `damages` del `ai_payload` son objetos `DamagePrediction` → se parsean como `DanoIaV1` y se muestran en lista legible (no dump del Map).
- **Pagos:** con `presupuesto_bob` el cliente no edita monto; backend valida igualdad. `crear_pago` solo crea PaymentIntent Stripe si `metodo == TARJETA`. `PagoRead.requiereStripePaymentSheet(metodo)` exige tarjeta.
- **Android:** `MainActivity` → `FlutterFragmentActivity` para `flutter_stripe`.
- **FCM / go_router:** `FcmMessageListener` ya no usa `GoRouter.of(context)` (el listener está **encima** del router). Es `ConsumerStatefulWidget` y usa `ref.read(goRouterProvider)` para `go` y ruta actual; evita `No GoRouter found in context` y excepciones al recibir notificación en primer plano.

**Seguridad:** no pegar claves `sk_` en chats; rotar en Stripe si se expusieron.

## Cambios recientes (2026-04-25) — Fase 1 IA incidentes compuestos ✅

- **Objetivo cubierto:** soportar casos reales donde un incidente trae múltiples daños simultáneos (ej. choque + vidrios + llanta) y múltiples fotos.
- **Schemas IA extendidos** (`backend/app/modules/ai/schemas.py`):
  - Inputs multi-evidencia: `transcripciones_audio[]`, `hallazgos_vision_por_imagen[]`.
  - Output multi-daño: `damages[]`, `requires_manual_review`, `conflict_notes`.
- **Fusionador multimodal v1** (`backend/app/modules/ai/services/evidence_fusion.py`):
  - pesos: imagen 0.45, texto 0.30, audio 0.25.
  - agregación por evidencia y detección de conflictos.
  - mapeo a categoría principal (`pick_primary_category`).
- **Router IA**:
  - endpoint nuevo `POST /api/ai/images/analyze-batch` para `files[]` (varias fotos).
  - endpoint existente `POST /api/ai/images/analyze` se mantiene compatible.
- **Prioridad y resumen**:
  - `prioritize` ahora considera daños compuestos (`damages_considerados`, `score`).
  - `structured-summary` ahora devuelve `danos_detectados` y agrega síntesis de daños en `resumen`.
- **Tests backend actualizados** (`backend/tests/test_ai_engines.py`):
  - caso compuesto multi-daño,
  - prioridad con daños múltiples,
  - resumen estructurado con daños compuestos.
- **Mobile (cliente) alineado con payload compuesto**:
  - `mobile/lib/cliente/emergencias/domain/solicitud_ai_payload.dart` parsea nuevos campos del backend IA compuesto.
  - `mobile/lib/cliente/emergencias/presentation/widgets/ai/solicitud_ai_resumen_card.dart` renderiza daños detectados, score, conflictos y revisión manual.

## Cambios recientes (2026-04-25) — Fixes críticos reportados por pruebas reales ✅

- **Push técnico no recibido (aunque aparece en historial):** causa frecuente detectada en pruebas: el técnico registra token FCM *después* del evento (asignación/estado), por lo que no había token en el momento del envío.
  - Fix: `dispositivos_push/service.py` (paquete `comunicacion_y_notificaciones`) en `registrar_fcm_token` reenvía notificaciones no leídas recientes (hasta 10) cuando es el primer token del usuario.
- **Hora BOT incorrecta en mobile (01:38 vs 21:38):**
  - Causa: timestamps API sin zona (`timestamp without time zone`) eran parseados como hora local en Dart.
  - Fix: `mobile/lib/core/utils/api_datetime.dart` + adopción en modelos cliente/técnico/pagos/comunicación para tratar naive timestamps como UTC y luego convertir a BOT en UI.
- **ETA “vacía” en seguimiento:**
  - Fix de fallback en backend (`portal_tecnico_emergencias/service.py`): al pasar a `EN_CAMINO`, si `tiempo_estimado_min` es `NULL`, se setea `20` min.
- **Pago “de adorno” respecto al presupuesto técnico:**
  - Fix UX en mobile (`pago_resumen_screen.dart`): monto se prellena con `presupuesto_bob` y se informa explícitamente al cliente.

# =========================================================

## Normativa

**`AGENTS.md`** (raíz del repo): contrato de agente, PUDS, UI/UX, seguridad y **obligación de mantener `docs/ai/`** tras cambios relevantes.

## Qué es el proyecto

Plataforma de **emergencias vehiculares**: clientes, talleres, técnicos, auditoría. Stack: **FastAPI + PostgreSQL + Angular 17 + Flutter + Docker**.

## Cambios recientes (2026-04-25) — Push técnico + presupuesto BOB ✅

- **Push al asignar técnico:** `comunicaciones/service.py` → `notificar_tecnico_solicitud_emergencia`; invocado desde `portal_taller_emergencias/service.py` en `asignar_tecnico_a_solicitud` después del aviso al cliente.
- **FCM sin tokens:** `_notificar_push` escribe log `INFO` cuando el usuario destino no tiene filas en `usuario_fcm_tokens`.
- **Presupuesto BOB:** migración `backend/migrations/0014_presupuesto_bob_solicitud.sql` + `docker-compose` init `14_...`; `ActualizarEstadoServicioIn` exige `presupuesto_bob` si `nuevo_estado == EN_ATENCION`; seguimiento cliente y PATCH técnico devuelven los campos; Flutter: diálogo de monto (técnico) y tarjeta en seguimiento (cliente).
- **BD existente:** si el volumen de Postgres ya fue inicializado antes, aplicar `0014` a mano con `psql` (el init de Docker no se re-ejecuta).

### Docker build “frontend grpc server closed” (2026-04-25) ✅

- **Síntoma:** al hacer `docker compose ... up -d --build`, falla `target backend: failed to solve: frontend grpc server closed unexpectedly` (a veces con puntero a `Dockerfile:1` con `# syntax=docker/dockerfile:1`).
- **Causa típica:** inestabilidad de BuildKit / Docker Desktop (comunicación gRPC con el “Dockerfile front” externo o con daemon), no un error lógico del código de la app.
- **Ajuste en repo:** se quitaron `# syntax=docker/dockerfile:1` y `RUN --mount=type=cache` en `backend/Dockerfile` y `frontend/Dockerfile` (instalación pip/npm sin mount de caché; builds un poco más lentos, más estables en Windows). Si aún falla: reiniciar Docker Desktop, `docker buildx prune`, o `set DOCKER_BUILDKIT=0` + `set COMPOSE_DOCKER_CLI_BUILD=0` para forzar el builder clásico.

### Backend startup “Unknown constraint max_digits” (2026-04-25) ✅

- **Síntoma:** backend reiniciando con traceback en import de `portal_tecnico_emergencias/schemas.py`: `ValueError: Unknown constraint max_digits`.
- **Causa:** en este runtime (Pydantic v2 del contenedor), la metadata `max_digits`/`decimal_places` en `Field(...)` para `Decimal` no fue aceptada al construir el schema.
- **Ajuste en repo:** `ActualizarEstadoServicioIn.presupuesto_bob` mantiene `gt=0` y mueve el control de formato monetario (máx. 12 dígitos y 2 decimales) a `@model_validator`, evitando el crash de arranque.

## Cambios recientes (2026-04-23) — Validación completa módulo IA ✅

## Cambios recientes (2026-04-25) — Limpieza de textos UI ✅

- **Frontend Angular:** se removieron referencias internas de planificación en textos visibles (`Ciclo`, `fase`, `CUxx`) en módulos admin/taller para una UX más profesional.
- **Mobile Flutter:** se removieron etiquetas `CUxx` y `ciclo` en textos de pantallas cliente/técnico (wizard, seguimiento, detalle y selector de actor), más normalización de comentarios descriptivos.
- **Verificación:** búsqueda global sin coincidencias de `Ciclo\\d`/`CU\\d` en `frontend/src` y `mobile/lib`.

### Seguimiento móvil, ETA, chips IA, FCM (2026-04-25) ✅

- **Chips "Ubicación / Audio / Imagen":** se alinean a datos reales: detalle móvil cuenta `ubicaciones`/`evidencias`; seguimiento usa flags del API (`tiene_ubicacion_cliente`, etc.). **ETA:** formulario en **portal taller** al asignar técnico (`tiempo_estimado_min` opcional) rellena `solicitud.tiempo_estimado_min` que ya consume el seguimiento móvil.
- **Historial:** `SeguimientoTimeline` elimina `(CU##)` de observaciones heredadas.
- **FCM:** `FirebaseMessaging.onMessage` con app abierta → `SnackBar` (`FcmMessageListener`). Token + backend sin cambio; credenciales Firebase siguen solo en máquina local.
- **Docs:** `CURRENT_STATE` actualizado; sesión en `docs/ai/sessions/2026-04-25-mobile-seguimiento-eta-fcm.md`.

### Técnico móvil: hora BOT + tipo accidente + push routing (2026-04-25) ✅

- **Hora Bolivia (Santa Cruz):** util `mobile/lib/core/utils/bolivia_time.dart` (UTC-4) aplicada en `tecnico_servicio_card`, `tecnico_servicio_detalle_screen`, `tecnico_servicio_ubicacion_screen` y `chat_bubble`.
- **Servicios asignados técnico:** backend `portal_tecnico_emergencias` incluye `categoria_incidente` y `nivel_prioridad` desde `ai_payload`; mobile técnico lo presenta como chips “Tipo” y “Prioridad” en lista y bloque “Incidente” en detalle.
- **Push técnico/cliente:** `FcmMessageListener` añade manejo de tap (`onMessageOpenedApp` + `getInitialMessage`) con deep-link por `solicitud_id`; si `tipo=MENSAJE_NUEVO` abre chat, en otro caso abre detalle/seguimiento.
- **Validación:** `flutter analyze` (mobile) ✅ y `python -m py_compile` para schemas/repository técnico ✅.

### Hora Santa Cruz unificada en sistema (2026-04-25) ✅

- **Angular web:** `app.config.ts` fija `LOCALE_ID='es-BO'` + `DATE_PIPE_DEFAULT_OPTIONS.timezone='-0400'`; `main.ts` registra locale `es-BO`. Resultado: los templates con `| date` muestran BOT.
- **Mobile Flutter:** `BoliviaTime` se usa en timeline/ETA/ubicación técnico/notificaciones/comprobante/listado solicitudes (además de técnico ya implementado) y se elimina dependencia de `.toLocal()`.
- **Convención:** backend mantiene persistencia en UTC/servidor; la capa de presentación fuerza BOT para experiencia consistente.
- **Docker:** `docker-compose.yml` ahora inyecta `TZ=America/La_Paz` en `db/mailhog/backend/frontend/ai-inference` y `PGTZ=America/La_Paz` en `db`.
- **Chequeo:** `docker compose config` válido ✅.

### Push registro + pagos (2026-04-25) ✅

- **Cliente (registro/token):** en `comunicaciones.service.registrar_fcm_token`, si es el primer token del cliente se envía push/notificación de bienvenida.
- **Pago confirmado:** en `pagos.service` se dispara push/notificación cuando `estado -> PAGADO`:
  - flujo simulado/autocomplete (`_aplicar_resultado_pasarela`)
  - confirmación Stripe (`confirmar_pago_stripe`)
- **Stripe env vars:** backend usa `STRIPE_SECRET_KEY` para PaymentIntent/retrieve y expone `STRIPE_PUBLISHABLE_KEY` al mobile en `PagoIniciadoRead`.

Todos los endpoints del módulo `ai/` fueron probados en Swagger con respuestas **200** correctas:

| Endpoint | Tipo | Estado |
|---|---|---|
| `POST /api/ai/audio/transcribe` | Worker `ai-inference` | ✅ |
| `POST /api/ai/images/analyze` | Worker `ai-inference` (YOLO detect/classify) | ✅ |
| `POST /api/ai/incidents/classify` | Reglas backend | ✅ |
| `POST /api/ai/incidents/structured-summary` | Reglas backend | ✅ |
| `POST /api/ai/incidents/prioritize` | Reglas backend | ✅ |
| `POST /api/ai/assignment/rank` | Reglas + consulta BD | ✅ |

- `/incidents/prioritize` detectó correctamente "vía rápida / carretera" y "lenguaje de alto riesgo" para prioridad `ALTA`.
- `/assignment/rank` retornó el taller seed (`Taller Demo Emergencias`, id=1) con score `0.857`.
- El stack completo levantado con: `docker compose --profile ai up -d --build`.
- Con modelo Colab propio: `docker compose -f docker-compose.yml -f docker-compose.ai-custom-model.yml --profile ai up -d --build`.

## Cambios recientes (2026-04-23) — IA modular + Docker

- **Backend:** módulo `backend/app/modules/ai/` — rutas bajo `{API_PREFIX}/ai/...` (p. ej. análisis de imagen/audio), cliente HTTP a servicio interno, reglas y prioridad; requiere permiso **`ai:inferir`** para endpoints de inferencia. Variables `AI_ENABLED`, `AI_INFERENCE_BASE_URL`, `AI_INFERENCE_STUB`, timeouts y límites de upload en `.env` raíz (ver `.env.example`).
- **Worker `ai-inference`:** contenedor en `services/ai-inference/` (FastAPI + Uvicorn :8080). Rutas internas p. ej. `POST /internal/vision/analyze`. **Perfil Compose `ai`:** sin `docker compose --profile ai` el servicio no arranca.
- **Modelo custom (Colab → YOLOv8-cls):** archivo local `backend/incidentes_emergencias_v1.pt` (no versionado). Override `docker-compose.ai-custom-model.yml` monta el `.pt` y fija `YOLO_TASK=classify`, `YOLO_IMGSZ=224`.
- **Comando stack completo con IA + modelo propio:**  
  `docker compose -f docker-compose.yml -f docker-compose.ai-custom-model.yml --profile ai up -d --build`  
  Tras `down -v --rmi all`, el primer arranque puede tardar varios minutos (build, Postgres healthy, descarga de pesos al volumen de caché del worker).
- **`.env`:** no duplicar `AI_ENABLED` / `AI_INFERENCE_BASE_URL`; la última línea suele prevalecer y deja IA “apagada” → **503** en el backend aunque el worker exista.
- **Bug corregido:** Ultralytics puede exponer `probs.top5` como **lista**; el worker hacía `.cpu()` sobre eso → **500** y **502** aguas arriba. Parche en `services/ai-inference/app/main.py` (`_yolo_classify`). Tras tocar el worker: `--build --force-recreate ai-inference`.
- **Sesión detallada:** `docs/ai/sessions/2026-04-23-agent-ia-docker-worker-env-ultralytics.md`.

## Cambios recientes (2026-04-22) — plan emergencia → taller → técnico

- **Angular — CU28 en portal taller:** `TallerEmergenciasApiService` expone `POST .../solicitudes/{id}/asignar-tecnico` y `GET .../asignaciones`. Pantalla detalle de incidente (`taller-emergencias-incidente-detalle`): tras **aceptar** la solicitud ya no redirige a la bandeja; recarga el detalle y muestra historial de asignaciones + selector de técnico activo (lista desde `TallerApiService.listTecnicos()`). Permiso `tecnicos:asignar`.
- **Docs:** `PROJECT_VISION.md` — Ciclo 2 emergencias como en producto; nota sobre nomenclatura «ciclo 3 fase n» en código. `NEXT_STEPS.md` — checklist emergencias.
- **Flutter cliente:** `EstadoSolicitudBadge` diferencia color **TALLER_ASIGNADO** vs **TECNICO_ASIGNADO**.
- **Postgres (verificación):** columna `tecnico_asignado_at` presente en entornos con init/migraciones al día.

## Cambios recientes (2026-04-22)

- **Base de datos — `tecnico_asignado_at`:** Alineada con el modelo `SolicitudEmergencia` y el asigna-técnico en portal taller. En **migraciones repo:** `0003` incluye `ADD COLUMN ... tecnico_asignado_at`, `0006` es parche idempotente, `docker-compose` monta `0006` como `05_tecnico_asignado_at.sql`. **Volúmenes ya inicializados:** no re-ejecutan init; correr en Postgres: `backend/migrations/0006_tecnico_asignado_at.sql` o el `ALTER` equivalente. Detalle: `DECISIONS_LOG` **DEC-009** y `CURRENT_STATE` (incidente móvil 500 al registrar emergencia).
- **Nota con scripts manuales:** Puede existir `scripts/007_fase2_asignacion_tecnico.sql` u otros SQL fuera de `docker-entrypoint-initdb.d`; la fuente de verdad para Docker local sigue siendo `backend/migrations/*` mapeada en `docker-compose.yml`.

## Cambios recientes (2026-04-21)

- **Backend ciclo 3 fase 1 (taller):** módulo `backend/app/modules/portal_taller_emergencias/` — bandeja, detalle incidente, aceptar/rechazar, disponibilidad. Router bajo `{API_PREFIX}/portal/taller/emergencias`. Requiere tablas/permisos de `scripts/006_fase1_taller_bandeja_disponibilidad.sql`. Seed `ensure_baseline_rol_permisos` asigna a `TALLER_RESPONSABLE` los códigos `solicitudes_taller:*`, `disponibilidad:gestionar` y `tecnicos:asignar` si existen en `permisos`.
- **Backend ciclo 3 fase 2 (taller, CU28):** `POST .../solicitudes/{id}/asignar-tecnico`, `GET .../solicitudes/{id}/asignaciones`. Requiere `scripts/007_fase2_asignacion_tecnico.sql` y columna `tecnico_asignado_at` en `solicitudes_emergencia`.
- **Backend ciclo 3 fase 3 (técnico):** módulo `portal_tecnico_emergencias` — `GET /servicios-asignados`, `GET /solicitudes/{id}/ubicacion`, `PATCH /solicitudes/{id}/estado`, mensajes en `/{id}/mensajes` (misma URL que antes). Permisos script 008 + `servicios_tecnico:leer` (007). Mensajes técnico migrados desde `comunicaciones.router`. Seed `ensure_baseline_rol_permisos` amplía rol `TECNICO`.
- **Backend ciclo 3 fase 4 (taller):** en `portal_taller_emergencias`: `GET /historial-atenciones`, `GET /comisiones`, `GET /comisiones/resumen`. Requiere `scripts/009_fase4_historial_comisiones.sql`. Modelo `ComisionTaller`.

## Cambios recientes (2026-04-19)

- **Mobile:** módulos renombrados a `lib/cliente/` y `lib/tecnico/` (sin `_ciclo1`). Config por **`mobile/.env`** (`flutter_dotenv`). Flujo técnico: login con validación de roles `TECNICO` / `TALLER_RESPONSABLE`, perfil vía `/auth/me` + portal taller o listado técnicos según rol; sesión técnica con tokens **independientes** del cliente.
- **Backend seeds:** defaults en `identidades_demo_sc.py` + `config.py` (p. ej. `carlos.vega@sc-demo.test` / `scdemo1`); `docker-compose.override.yml` activa `SEED_TECNICO_ON_START` en dev.
- **Docs / README:** `mobile/README.md` y sección móvil del `README.md` raíz actualizados.

## Rutas y archivos clave

| Área | Dónde mirar |
|------|-------------|
| API móvil cliente | `backend/app/modules/portal_cliente/` |
| API portal taller | `backend/app/modules/portal_taller/` |
| API taller emergencias (bandeja / CU25–29) | `backend/app/modules/portal_taller_emergencias/` |
| API técnico emergencias (CU32–35) | `backend/app/modules/portal_tecnico_emergencias/` |
| IA (inferencia + reglas) | `backend/app/modules/ai/`; worker `services/ai-inference/app/main.py` |
| Router Flutter | `mobile/lib/cliente/presentation/router/cliente_go_router.dart` |
| Env móvil | `mobile/.env` + `lib/core/config/app_env.dart` |
| Seeds | `backend/app/seeds/__main__.py`, `dev_*.py` |

## Próximo paso sugerido

1. **Módulo IA ya validado** — no requiere cambios. El stack funciona con `docker compose --profile ai up -d --build`.
2. Continuar con **Angular:** auth completo (guard/interceptor), layout admin, pantallas CRUD.
3. Continuar con **Flutter:** tests unitarios/widget, pulir UX, refresh token.
4. Ampliar **tests pytest** en backend (cobertura endpoints IA + emergencias).
5. Tras un `git pull`, si el backend falla con columna `tecnico_asignado_at` inexistente, aplicar `0006` a la BD.
6. `docker compose exec backend python -m app.seeds` si la BD no tiene usuarios demo.
7. `mobile/.env` con `API_BASE_URL` alcanzable desde el dispositivo → `flutter run` en `mobile/`.

## Docker / .env raíz

Compose carga `.env` del repo; `DATABASE_URL`, `SECRET_KEY`, `SEED_*`, **`AI_*`**. Ver `.env.example` raíz. **No duplicar claves** de IA en el mismo archivo.

## Handoff puntual (2026-04-25) — UX de push móvil

- Problema reportado: “la notificación se ve como mensaje interno” (SnackBar en foreground).
- Solución aplicada: en `mobile/lib/core/push/fcm_message_listener.dart` se reemplaza el aviso visual por notificación del sistema vía `flutter_local_notifications`.
- Se mantiene deep-link: al tocar la notificación local, la app navega al chat/detalle según `tipo` y `solicitud_id`.
- Backend con mejor observabilidad FCM: `comunicacion_y_notificaciones/dispositivos_push/fcm_client.py` loguea `FCM multicast enviado: success/failure/tokens` y detalle de fallos.
- Verificación mínima completada:
  - `FCM_ENABLED=True` en runtime.
  - `POST /api/portal/cliente/dispositivos/fcm 204` en logs.
  - Inserciones en `notificaciones` para eventos (`TALLER_ASIGNADO`, `TECNICO_ASIGNADO`, etc.).
