# CURRENT_STATE.md
# =========================================================
# Estado actual del proyecto
# Última actualización: 2026-04-26 — TESTING_STRATEGY: mapeo Word (Prueba 2 `POST /servicios`) al dominio real ✅
# =========================================================

## Estado: CICLO 1 base + dominio emergencias (Ciclo 2) + módulo IA completo ✅

### Documentación de pruebas API (2026-04-26) ✅
- [x] Se agregó `docs/ai/TESTING_STRATEGY.md` con 10 casos de prueba para `GET /servicios/{id}` y `GET /servicios`, incluyendo entradas, resultados esperados y criterios de aceptación.
- [x] Se dejó explícito que actualmente no existe ruta `/servicios` en `backend/app`; el documento queda como plan reusable para mapear al endpoint real cuando se implemente.
- [x] **Prueba 2 (plantilla Word / captura):** se documenta que el contrato `POST /servicios` con `nombre` + `horario_*` **no** existe en el repo; el mapeo sugerido es `POST /api/app/cliente/emergencias` (201, alta) o `POST /api/app/taller/emergencias/bandeja/{id}/aceptar` (200, taller toma el caso), con cuerpos/roles reales.

### Panel admin — dashboard financiero (2026-04-26) ✅
- [x] **Backend:** se creó `app/modules/acceso_y_administracion/admin_finanzas/` con endpoints `GET /api/admin/finanzas/resumen` y `GET /api/admin/finanzas/reportes` (rango `desde`/`hasta`) para KPIs globales: comisión plataforma (10 %), total cobrado, ticket promedio, conversión a pago, talleres con comisión, top talleres y serie diaria.
- [x] **Frontend Angular (`admin-dashboard`):** se integró bloque KPI con filtros por fecha, tarjetas de métricas financieras, tabla de top talleres y gráfica de barras diaria de comisión plataforma, manteniendo tema visual actual.
- [x] **Fix build frontend:** ruta `/admin/panel/finanzas` referenciaba `admin-finanzas.component` inexistente; se creó componente wrapper `features/finanzas/admin-finanzas.component` para reutilizar `admin-dashboard` y restaurar compilación Docker/Angular.

### Arquitectura backend modular (2026-04-26) ✅
- [x] **Agrupación física:** `auth`, `permisos`, `roles`, `usuarios`, `bitacora` bajo `app/modules/acceso_y_administracion/` (sin `talleres`). **`talleres`**, **`taller_responsable`** y **`tecnico`** bajo `app/modules/talleres_y_tecnicos/`; imports `app.modules.talleres_y_tecnicos.<submódulo>`. Las URLs API no cambian.
- [x] **Clientes y vehículos (CU1 / CU10):** `clientes` y `vehiculos` viven bajo `app/modules/clientes_y_vehiculos/`; imports `app.modules.clientes_y_vehiculos.clientes|vehiculos`. Orden `db_metadata`: `usuarios` → `clientes` → … → `vehiculos`.
- [x] **Incidentes (CU11–CU18):** código cliente en `app/modules/incidentes/emergencias/`; imports `app.modules.incidentes.emergencias`. Prefijo API sigue `/api/app/cliente/emergencias`.
- [x] **Atención taller (CU24–CU31 en código):** `taller_emergencias` bajo `app/modules/atencion/taller_emergencias/`; imports `app.modules.atencion.taller_emergencias`. Prefijo API sigue `/api/app/taller/emergencias`.
- [x] **Comunicación y notificaciones (CU19, CU21, CU35):** `comunicaciones`, `notificaciones`, `dispositivos_push`, `mensajes_solicitud` bajo `app/modules/comunicacion_y_notificaciones/`; imports `app.modules.comunicacion_y_notificaciones.<sub>`. Prefijos API sin cambio (`/app/cliente/...`, `/app/tecnico/...`).
- [x] Sustituido el monolito `acceso/` por módulos independientes: **`auth`** (sesiones, tokens email), **`roles`**, **`permisos`**. Mismas tablas y URLs (`/api/auth/...`, `/api/roles/...`, `/api/permisos/...`). Bitácora: asignación de roles al usuario ahora se registra con `modulo="roles"`.
- [x] **Comunicaciones (orquestación):** bajo `comunicacion_y_notificaciones/`, subpaquetes `notificaciones`, `dispositivos_push`, `mensajes_solicitud` y `comunicaciones` (solo `router.py` que delega). `db_metadata` importa los tres modelos; seeds y `pagos` usan servicios con prefijo `app.modules.comunicacion_y_notificaciones.*`.
- [x] **Push bienvenida:** sigue en `dispositivos_push.service.registrar_fcm_token` (llama a `notificaciones.service.crear_notificacion_y_push`).

### Identidades seed local (2026-04-26) ✅
- [x] **`identidades_demo_sc.py`:** nombres, emails `*.sc-demo.test`, teléfonos +591 77010010–014, contraseña corta `scdemo1`, talleres **Mecánica Express Rivero** y **Auxilio Vial 4to Anillo SC** (ambos Santa Cruz). `app/core/config.py` usa estos valores como defaults de `SEED_*`; `docker-compose.yml` alineado (sin +57 ni La Paz en fallbacks).

### Seed demo Santa Cruz (2026-04-26) ✅
- [x] **`dev_demo_santa_cruz`:** 4 vehículos + 10 emergencias `[DEMO-SC]` (zonas y copy Santa Cruz), bandeja variada, asignaciones, 2 pagos BOB + comisiones para probar reportes del portal taller. `python -m app.seeds` lo ejecuta al final; `SEED_DEMO_SANTA_CRUZ_ON_START` opcional en arranque. Ciudad por defecto seed cliente/taller: Santa Cruz de la Sierra.

### Seed demo media prioridad (2026-04-26) ✅
- [x] **`dev_demo_media_prioridad`:** Tras Santa Cruz, idempotente (notificación gate `[DEMO-MEDIA] seed v1`): notificaciones in-app (tipos permitidos por enum SQL), hilo de chat cliente↔técnico en la primera solicitud `[DEMO-SC]` con `tecnico_id`, `UPDATE` de `ai_payload` con `_seed_media` + estructura alineada a mobile/backend IA, fila `taller_disponibilidad` del taller principal, usuario+taller **competidor segunda sede en Santa Cruz** (`SEED_TALLER2_*`) y **backfill** de filas `solicitud_taller_bandeja` PENDIENTE para ese taller en todas las solicitudes `[DEMO-SC]`. `SEED_DEMO_MEDIA_PRIORIDAD_ON_START` opcional en `lifespan` (requiere usuarios demo ya creados por otros flags o por `python -m app.seeds`).

### Seed stress visual — catálogos y cuentas extra (2026-04-26) ✅
- [x] **`dev_stress_visual` + `ensure_catalogos_vehiculo_stress_extra`:** más tipos/marcas/modelos de vehículo (Nissan, VW, Renault, etc.) y **8 usuarios cliente** con nombres bolivianos y emails `*.lista.sc-demo.test` (tel. +591 77021xxx); contraseña `SEED_STRESS_CLIENT_PASSWORD` (default `scdemo1` vía `identidades_demo_sc`). Idempotente por email. `python -m app.seeds` al final; `SEED_STRESS_VISUAL_ON_START` solo arranque.

### Push técnico + presupuesto BOB (2026-04-25) ✅
- [x] **Asignación técnico:** tras notificar al cliente, el backend notifica al **usuario técnico** (`notificar_tecnico_solicitud_emergencia`) con push/in-app. Si no hay tokens FCM para ese usuario, se registra log `FCM omitido: ... sin tokens`.
- [x] **Presupuesto en sitio:** migración `0014_presupuesto_bob_solicitud.sql` + columnas en modelo `SolicitudEmergencia`; `PATCH` técnico exige `presupuesto_bob` al pasar a `EN_ATENCION`; seguimiento cliente expone `presupuesto_bob` / `presupuesto_registrado_at`; móvil cliente (seguimiento) y técnico (diálogo + lista) actualizados.
- [x] **Fix pago cliente “monto no definido” (2026-04-26):** el endpoint detalle `GET /api/app/cliente/emergencias/{id}` no exponía `presupuesto_bob` porque `SolicitudEmergenciaRead` no lo incluía; se añadieron `presupuesto_bob` y `presupuesto_registrado_at` al schema base (y por herencia al detalle). En mobile `pago_resumen` se agregó `refresh` manual + pull-to-refresh para recargar el monto fijado por técnico sin reiniciar la app.
- [x] **FCM mismo token:** documentado en sesión: un solo token por fila; cambiar de rol en el mismo teléfono reasigna el token al último login que lo registre.
- [x] **Replay push pendientes al registrar token:** si el usuario registra su primer token FCM (p. ej. técnico inicia sesión después de ser asignado), backend reenvía hasta 10 notificaciones no leídas recientes para evitar “me llegó en historial pero no sonó push”.
- [x] **Hora BOT corregida en mobile:** parser unificado `core/utils/api_datetime.dart` interpreta timestamps API sin zona como UTC (`...Z`) antes de formatear con `BoliviaTime`; evita mostrar `01:38 BOT` cuando corresponde `21:38 BOT`.
- [x] **ETA operativa mínima:** al pasar a `EN_CAMINO`, si no existe `tiempo_estimado_min`, backend asigna fallback `20` min para no dejar tarjeta ETA vacía.
- [x] **Pago cliente prellenado con presupuesto técnico:** pantalla `pago_resumen` carga automáticamente `presupuesto_bob` cuando existe.
- [x] **Pago: monto = presupuesto (regla de negocio):** si existe `presupuesto_bob`, el monto se muestra **bloqueado** en el cliente; backend exige `monto == presupuesto_bob` en `POST /pagos`. **Stripe (PaymentIntent)** solo se crea para método **TARJETA**; efectivo/transferencia/QR dejan de recibir `client_secret` (evita inicializar el SDK con efectivo). Android: `MainActivity` extiende `FlutterFragmentActivity` (requisito `flutter_stripe`). **IA UI:** `damages[]` se parsea como objetos y se listan (label/severidad/motivos), no como `.toString()` del mapa.
- [x] **FCM + go_router (2026-04-26):** `FcmMessageListener` queda **por encima** de `ShadApp.router`, así que `GoRouter.of(context)` no encuentra el router. Se usa `ConsumerStatefulWidget` + `ref.read(goRouterProvider).go(...)` (y la misma instancia para leer ruta técnico/cliente).
- [x] **Pago — confirmar sin duplicar `POST /pagos` (2026-04-26):** `pago_confirmacion_screen.dart` reutiliza `draft.pagoIniciado` cuando coincide solicitud/método/monto (ε 0,02) en lugar de volver a `iniciarPago`; con Stripe, `confirmarStripe` recibe `paymentIntentId` desde `PagoRead.stripePaymentIntentId` (no solo `referencia_externa`), evitando 422 y filas PENDIENTE duplicadas.

### Pagos → comisiones taller / ganancias dashboard (2026-04-26) ✅
- [x] **Causa:** el dashboard y reportes suman `comisiones_taller`; al pasar un pago a `PAGADO` (Stripe o pasarela simulada) **no** se insertaba fila en esa tabla, así que `total_servicios` / `total_neto` seguían en 0.
- [x] **Corrección:** `pagos/repository.py` expone `registrar_comision_taller_tras_pago` (10 % plataforma, idempotente por `solicitud_id`); se invoca desde `pagos/service.py` tras pago exitoso en `_aplicar_resultado_pasarela` y en `confirmar_pago_stripe`. Pagos ya confirmados antes del fix pueden requerir backfill SQL manual si hiciera falta.

### Ajuste de UX/copy (2026-04-25) ✅
- [x] Frontend Angular (admin/taller): removidas etiquetas visibles tipo `Ciclo X`, `fase X`, `CUxx` en login, recover, dashboard, shell, permisos/roles, bandeja y detalle.
- [x] Mobile Flutter (cliente/técnico): removidas etiquetas visibles `CUxx` en wizard/seguimiento/detalle y textos de actor select; comentarios internos y descripciones también normalizados para consistencia.
- [x] **Seguimiento / análisis asistido:** el backend expone en seguimiento `tiene_ubicacion_cliente`, `tiene_evidencia_foto`, `tiene_evidencia_audio`; el móvil los usa en `SolicitudAiResumenCard` (el snapshot `ai_payload.ficha` solía quedar en “no” al crear la solicitud antes de subir medios). Detalle: chips desde `ubicaciones` / `evidencias` reales. Timeline: se eliminan sueltos `(CU##)` de observaciones antiguas.
- [x] **ETA:** al asignar técnico, el portal taller puede enviar `tiempo_estimado_min` (campo en formulario) → se guarda en la solicitud → `EtaLlegadaCard` en el móvil. Sin valor, el mensaje de “aún no hay ETA” es el comportamiento esperado.
- [x] **FCM:** registro de token existente; añadido **foreground** `onMessage` → `SnackBar` (`FcmMessageListener` en `app.dart`). `google-services.json` / `firebase_options.dart` siguen siendo locales (gitignore).
- [x] **Técnico móvil:** fechas/horas visibles normalizadas a **Bolivia Santa Cruz (BOT, UTC-4)** con util común (`core/utils/bolivia_time.dart`) en tarjetas, detalle, ubicación y burbujas de chat.
- [x] **Servicios asignados técnico:** backend `tecnico` expone `categoria_incidente` y `nivel_prioridad` (derivados de `ai_payload`) y el mobile los muestra en la lista/detalle con copy de severidad (p. ej. prioridad alta/crítica = grave).
- [x] **Push deep-link:** `FcmMessageListener` agrega `onMessageOpenedApp` + `getInitialMessage`; al tocar push navega directo a chat o detalle (cliente/técnico) usando `solicitud_id` y `tipo`.
- [x] **Push por pago confirmado:** backend `pagos/service.py` envía notificación in-app + push al cliente cuando el pago queda `PAGADO` (pasarela simulada y confirmación Stripe).
- [x] **Push de bienvenida cliente (primer token):** al registrar el primer FCM token del cliente (`dispositivos_push` vía ruta `app/cliente/dispositivos/fcm`) se crea notificación/push de cuenta activa.
- [x] **Hora Santa Cruz (BOT) unificada:** mobile reemplaza `.toLocal()` por util común `BoliviaTime` en vistas de cliente/técnico y chat/comunicaciones/pagos; Angular fija `LOCALE_ID='es-BO'` y `DATE_PIPE_DEFAULT_OPTIONS.timezone='-0400'` para que todos los `| date` muestren hora Bolivia por defecto.
- [x] **Docker timezone BOT:** `docker-compose.yml` define `TZ=America/La_Paz` en `db`, `mailhog`, `backend`, `frontend` y `ai-inference`, y `PGTZ=America/La_Paz` en `db` para logs/fechas de contenedor alineadas a Santa Cruz.

### Taller emergencias — prioridad y evidencias (2026-04-25) ✅
- [x] **API** `GET /api/app/taller/emergencias/bandeja/disponibles` y `GET .../bandeja/{id}`: campo `nivel_prioridad` (desde `ai_payload.prioridad.nivel_prioridad`); en detalle, `evidencias[]` (filas de `solicitud_evidencias` para la solicitud).
- [x] **Angular** bandeja: columna **Prioridad** con chips por nivel; detalle: galería de **fotos** y reproductor **audio** (URLs internas reescritas a ruta `/api/media/evidencias/...` bajo el mismo origen).
- [x] **Backend** `rechazar_solicitud`: corregida referencia incorrecta a variable `bandeja` al notificar al cliente.

### Docker — frontend build + `MAILHOG_WEB_URL` (2026-04-26) ✅
- [x] `docker compose build frontend` fallaba en `prebuild` (script buscaba `/.env` al no haber monorepo dentro del contexto). `sync-from-root-env.cjs` acepta **`MAILHOG_WEB_URL` por entorno**; `frontend/Dockerfile` define `ARG`/`ENV`; Compose pasa `build.args` desde el `.env` raíz. Ver `docs/ai/DOCKER_BUILD_OPTIMIZATION.md`.

### Docker — Postgres healthcheck primer `up` (2026-04-26) ✅
- [x] Servicio `db`: `healthcheck` con **`start_period: 240s`** y `retries: 12` para no marcar **unhealthy** durante initdb + scripts en `docker-entrypoint-initdb.d` y el reinicio a modo normal (evita `dependency failed to start: container emergencias_db is unhealthy` en máquinas lentas). Detalle en `docs/ai/DOCKER_BUILD_OPTIMIZATION.md`.

### Docker — builds más rápidos (2026-04-26) ✅
- [x] **`ai-inference`:** `docker-compose` usa `context: ./services/ai-inference` (antes la raíz del repo enviaba mobile/frontend/docs al daemon). Dockerfile y `.dockerignore` en ese directorio.
- [x] **Backend:** `COPY --chown=appuser:appuser` en runtime; `.dockerignore` excluye `tests/`, `uploads/`, credenciales Firebase locales.
- [x] **Frontend:** `.dockerignore` ampliado (specs, e2e, IDE).
- [x] Plan y causas: `docs/ai/DOCKER_BUILD_OPTIMIZATION.md`.

### Variables de entorno — solo raíz (2026-04-26) ✅
- [x] Eliminado `backend/.env.example`; documentación y carga de settings usan únicamente **`.env` / `.env.example` en la raíz** (`config.py` ya no lee `backend/.env`). `mobile/.env` sin cambios.
- [x] **Despliegue:** `API_PUBLIC_URL` y `APP_PUBLIC_URL` opcionales en `Settings` (prioridad sobre `EMAIL_LINK_BASE_URL` / `FRONTEND_PUBLIC_URL`); evidencias usan `EVIDENCIAS_PUBLIC_BASE_URL` o `API_PUBLIC_URL` o `Host` de la petición. Documentado en `.env.example`; `docker-compose.yml` pasa las variables al backend.
- [x] **`config.py` sin `localhost` en CORS/SMTP/enlaces:** `CORS_ORIGINS`, `SMTP_HOST`, `EMAIL_LINK_BASE_URL` y `FRONTEND_PUBLIC_URL` son obligatorias vía entorno (`.env` / Compose); valores de desarrollo viven en `.env.example` y en el `.env` del repo.
- [x] **Frontend dev sin URLs fijas en TS:** `proxy.conf.js` exige `BACKEND_URL` en `.env` raíz; MailHog sale de `MAILHOG_WEB_URL` + `npm run env:sync` / `prestart` → `mailhog-url.generated.ts`. `docker-compose` ya no usa `:-http://localhost…` para CORS ni enlaces públicos (deben venir del `.env`).
- [x] **`.env.example` infra:** incluye `TZ`, `PGTZ`, `YOLO_TASK`, `FIREBASE_CREDENTIALS_PATH` (ruta contenedor `/app/...`). En `docker-compose.yml`, esas mismas claves conservan **fallbacks seguros** (`America/La_Paz`, `db`, `/app/firebase-credentials.json`, `backend:8000`) para que un `.env` antiguo no deje cadenas vacías en TZ o en el upstream del frontend.

### Taller web — navegación post-aceptación (2026-04-26) ✅
- [x] **Historial / comisiones API:** respuestas de `GET .../historial-atenciones` y `GET .../comisiones` incluyen **`bandeja_id`** (join a `solicitud_taller_bandeja`) para poder abrir `GET .../bandeja/{id}` desde listados.
- [x] **Angular panel taller:** rutas y menú **Mis solicitudes** (activas, fuera de bandeja disponible), **Historial de atenciones** (filtros fecha/estado), **Servicios asignados** (con técnico), **Comisiones** (resumen CU31 + tabla). Servicio `TallerEmergenciasApiService` extendido. Sesión: `docs/ai/sessions/2026-04-26-taller-web-sidebar-historial-comisiones.md`.

## Lo que existe

### Backend FastAPI ✅
- [x] `core/` — config, database, security, dependencies
- [x] `modules/acceso_y_administracion/` — auth, roles, permisos, usuarios, bitácora
- [x] `modules/clientes_y_vehiculos/clientes/` — ORM `Cliente`; admin en `usuarios` router `/clientes`; app móvil `/api/app/cliente`
- [x] `modules/clientes_y_vehiculos/vehiculos/` — catálogos + CRUD vehículos `/api/vehiculos`
- [x] `modules/incidentes/emergencias/` — solicitudes, seguimiento, ubicaciones, evidencias (cliente); `/api/app/cliente/emergencias`
- [x] `modules/talleres_y_tecnicos/talleres/` — CRUD talleres, especialidades, técnicos (`/api/talleres`, `/api/especialidades`, `/api/tecnicos`)
- [x] `modules/talleres_y_tecnicos/taller_responsable/` — registro taller, mi-taller, técnicos (responsable); `/api/app/taller`
- [x] `modules/talleres_y_tecnicos/tecnico/` — app técnico emergencias; `/api/app/tecnico/emergencias`
- [x] `modules/atencion/taller_emergencias/` — bandeja PENDIENTE, detalle, aceptar/rechazar, disponibilidad, asignar técnico, historial y comisiones; prefijo `/api/app/taller/emergencias`
- [x] `modules/comunicacion_y_notificaciones/` — `comunicaciones`, `notificaciones`, `dispositivos_push`, `mensajes_solicitud`; notificaciones in-app, FCM, chat por solicitud (CU19/CU21/CU35)
- [x] `modules/ai/` — módulo completo con **6 endpoints validados** (ver tabla abajo); inferencia audio/imagen vía cliente HTTP a **`ai-inference`**, reglas híbridas, prioridad, asignación de taller; permiso `ai:inferir`; límites `AI_MAX_*` en settings
- [x] **Fase 1 incidentes compuestos (multi-foto + multi-daño)**: schemas extendidos con `transcripciones_audio[]` y `hallazgos_vision_por_imagen[]`; salida multi-label `damages[]`; nuevo endpoint `POST /api/ai/images/analyze-batch`; fusionador multimodal v1 (`evidence_fusion.py`) con pesos `imagen=0.45`, `texto=0.30`, `audio=0.25`; bandera `requires_manual_review` para conflictos
- [x] **`ai_payload` al subir medios (2026-04-27):** el enriquecimiento IA (`enrich_solicitud_ai_after_create`) se vuelve a ejecutar tras **evidencia** (FOTO/AUDIO, URL o archivo), **nueva ubicación** y **PATCH de texto** de la solicitud, no solo al crear. Lectura de binarios de evidencia para inferencia: primero archivo bajo `uploads/evidencias/` si la URL contiene `/media/evidencias/`, luego HTTP (evita depender de IP del móvil desde Docker). Sesión: `docs/ai/sessions/2026-04-27-agent-ia-payload-reenrich-evidencia.md`.
- [x] **AVIF + analyze-batch (2026-04-26):** el worker `ai-inference` añade `pillow-heif` + `libheif1` para que `PIL.Image.open` decodifique AVIF/HEIF (antes solo JPEG/PNG vía OpenCV/Pillow estándar → 400 y 502 en lote). `POST /api/ai/images/analyze-batch` ya no aborta todo el lote: cada archivo fallido devuelve un `resultado` con `hallazgos` explicando el error y `confianza=0`; las demás imágenes siguen con análisis normal. Rebuild: `docker compose ... --build ai-inference backend`.
- [x] **Mobile IA compuesto (lectura UI):** `SolicitudAiPayloadV1` ahora parsea campos nuevos (`damages`, `requires_manual_review`, `conflict_notes`, `score`, `damages_considerados`, `danos_detectados`, `hallazgos_vision_por_imagen`) y `SolicitudAiResumenCard` los muestra en detalle/seguimiento para reflejar análisis multi-daño en la app.
- [x] `main.py` — routers bajo `API_PREFIX` (p. ej. `/api`)
- [x] `migrations/init.sql` + seeds: `app/seeds/` — admin, cliente, taller, **técnico**, **demo Santa Cruz**, **demo media prioridad** (`python -m app.seeds`); vars `SEED_*` en `.env` raíz; **defaults centralizados** en `identidades_demo_sc.py` (Santa Cruz, `*.sc-demo.test`, `scdemo1`, tel. +591 77010010–014) + `docker-compose.yml` alineado.
- [x] Alembic baseline + `alembic stamp` tras init

### Frontend Angular ✅
- [x] Docker + nginx + proxy; environments; rutas lazy; landing; estilos globales oscuros
- [x] Portal **taller** — emergencias: bandeja, detalle incidente, aceptar/rechazar; **CU28** en UI: `TallerEmergenciasApiService` (`asignarTecnico`, `listarAsignacionesTecnico`) + bloque asignación en `taller-emergencias-incidente-detalle` (tras aceptar permanece en detalle y lista historial de asignaciones). Ver `frontend/src/app/core/services/taller-emergencias-api.service.ts`

### Mobile Flutter ✅
- [x] `mobile/.env` + **flutter_dotenv** (asset); `lib/core/config/app_env.dart` — `API_BASE_URL`, `APP_NAME`, timeouts opcionales
- [x] `lib/cliente/` — auth portal (login/registro/recuperar), shell, home, vehículos, perfil; Riverpod + go_router (`cliente/presentation/router/cliente_go_router.dart` registra también rutas globales)
- [x] `lib/tecnico/` — emergencias (servicios asignados, detalle, chat, etc.); splash, login, recuperar, shell; **tokens JWT en secure storage separados** (`tecnico_access_token` vía `core/network/tecnico_api_client.dart`)
- [x] Badge de estado cliente: colores distintos **Taller asignado** vs **Técnico asignado** (`estado_solicitud_badge.dart`)
- [x] `core/network/api_error.dart` compartido; `api_constants` con `portal/taller/mi-taller`, `tecnicos`, etc.

### Docker ✅
- [x] `docker-compose.yml` + override; `.env` raíz como fuente principal
- [x] **Build estable en Windows:** `backend/Dockerfile` y `frontend/Dockerfile` sin `# syntax=docker/dockerfile:1` ni `RUN --mount=type=cache` (mitiga `frontend grpc server closed unexpectedly` con BuildKit/Docker Desktop). Workarounds extra: `docker buildx prune`, reiniciar Docker, o `DOCKER_BUILDKIT=0` + `COMPOSE_DOCKER_CLI_BUILD=0`.
- [x] **Servicio `ai-inference`** (perfil Compose `ai`): imagen en `services/ai-inference/` — STT (Whisper), visión YOLO **detect** (COCO) o **classify** (modelo `.pt` propio). Sin `--profile ai` el worker **no** se levanta; el backend puede quedar con IA deshabilitada o en stub según variables.
- [x] **Modelo de clasificación propio (`incidentes_emergencias_v1.pt`):** hace falta **montar** el `.pt` en el contenedor vía **`docker-compose.ai-custom-model.yml`** (`./backend/incidentes_emergencias_v1.pt` → `/models/...`) **y** el **`.env` raíz** con `YOLO_TASK=classify`, `YOLO_MODEL=/models/incidentes_emergencias_v1.pt`, `YOLO_IMGSZ=224`. Si en `.env` quedan `YOLO_TASK=detect` y `YOLO_MODEL=yolov8n.pt`, el worker solo aplica **COCO** (persona/coche) y no las clases de Colab — suele confundirse con “el modelo dejó de reconocer”. Comando: `docker compose -f docker-compose.yml -f docker-compose.ai-custom-model.yml --profile ai up -d --build` (mismos `-f` en `down` / `exec`).
- [x] **Postgres (init):** `backend/migrations/init.sql` + `0002`–`0014` (incl. `0014_presupuesto_bob_solicitud.sql`) + **`0007_taller_operacion_permisos.sql`** (permisos `solicitudes_taller:*`, `disponibilidad:gestionar`, `tecnicos:asignar`, etc. y `rol_permiso` para `TALLER_RESPONSABLE` / `TECNICO`). Montado como `06_` en `docker-compose`. **BD ya creada:** ejecutar ese SQL a mano o `docker compose exec -i db psql ... < backend/migrations/0007_...sql`. La columna `tecnico_asignado_at` también está en `0003`. Ver `DECISIONS_LOG` **DEC-009**.

### Validación completa módulo IA — 2026-04-23 ✅

Todos los endpoints del módulo `ai/` probados en Swagger (`http://localhost:8000/docs`) con respuestas **200** correctas:

| Endpoint | Tipo | Resultado validado |
|---|---|---|
| `POST /api/ai/audio/transcribe` | Worker (`ai-inference`) | Transcripción + keywords + urgencia |
| `POST /api/ai/images/analyze` | Worker (`ai-inference`) | Hallazgos YOLO + claridad imagen |
| `POST /api/ai/incidents/classify` | Reglas backend | `categoria`, `confianza`, `fuentes` |
| `POST /api/ai/incidents/structured-summary` | Reglas backend | `resumen`, `ficha` estructurada |
| `POST /api/ai/incidents/prioritize` | Reglas backend | `nivel_prioridad`, `motivo[]` |
| `POST /api/ai/assignment/rank` | Reglas + BD | `candidatos[]`, `mejor_taller_id` |

**Ejemplo de respuesta `/incidents/prioritize` (LLANTA en autopista):**
```json
{ "nivel_prioridad": "ALTA", "motivo": ["ubicación o relato sugiere vía rápida / carretera", "lenguaje de alto riesgo"] }
```

**Ejemplo de respuesta `/assignment/rank` (La Paz, categoría LLANTA):**
```json
{ "candidatos": [{ "taller_id": 1, "nombre_comercial": "Taller Demo Emergencias", "score": 0.857, "detalle": { "proximidad": 1, "carga_bandeja": 0, "especialidad": 0.35, "prioridad_peso": 1, "distancia_km": 0 } }], "mejor_taller_id": 1 }
```

### Fase 1 incidentes compuestos — 2026-04-25 ✅

- `POST /api/ai/incidents/classify` ahora soporta evidencia compuesta:
  - `transcripciones_audio[]`
  - `hallazgos_vision_por_imagen[]`
- La clasificación devuelve además:
  - `damages[]` (multi-daño con `confidence`, `severity`, `evidence_support`, `reasons`)
  - `requires_manual_review`
  - `conflict_notes[]`
- `POST /api/ai/incidents/prioritize` ahora incluye:
  - `score` (0..1)
  - `damages_considerados[]`
- `POST /api/ai/incidents/structured-summary` ahora incluye:
  - `danos_detectados[]`
  - resumen enriquecido con daños compuestos detectados
- Nuevo endpoint: `POST /api/ai/images/analyze-batch`
  - recibe `files[]`
  - responde `imagenes[]` + `hallazgos_consolidados` + `claridad_promedio` + `confianza_promedio`

### Incidente resuelto (2026-04-23) — análisis de imagen 502/500 (worker IA) ❌→✅
- **Síntoma:** `POST /api/ai/images/analyze` devolvía **502**; logs de `ai-inference`: **500** en `/internal/vision/analyze`, `AttributeError: 'list' object has no attribute 'cpu'` en `_yolo_classify`.
- **Causa:** en Ultralytics reciente, `probs.top5` y `probs.top5conf` pueden ser **listas**, no tensores; el código llamaba `.cpu().numpy()` sin comprobar tipo.
- **Reparación:** `services/ai-inference/app/main.py` — normalización a listas de int/float. Tras cambiar el worker, **`docker compose ... --build --force-recreate ai-inference`** para que el contenedor use el código nuevo.

### Incidente operativo (2026-04-23) — backend 503 “inferencia deshabilitada”
- **Causa frecuente:** en `.env` raíz, variables `AI_ENABLED` / `AI_INFERENCE_BASE_URL` **duplicadas**; la última aparición suele ganar (`false` o URL vacía) → el backend no llama al worker.
- **Mitigación:** una sola sección `AI_*`; para Docker en la misma red: `AI_ENABLED=true`, `AI_INFERENCE_BASE_URL=http://ai-inference:8080`.

### Incidente resuelto (2026-04-25) — backend crash Pydantic en `presupuesto_bob` ❌→✅
- **Síntoma:** al arrancar backend, traceback en `ActualizarEstadoServicioIn` con `ValueError: Unknown constraint max_digits`.
- **Causa:** compatibilidad del runtime con constraints `max_digits`/`decimal_places` en `Field` sobre `Decimal`.
- **Reparación:** en `portal_tecnico_emergencias/schemas.py`, `presupuesto_bob` mantiene `gt=0` y validación de formato monetario (máx. 12 dígitos y 2 decimales) pasa a `@model_validator`. Resultado: backend inicia y `/health` responde 200.

### Incidente resuelto (2026-04-22) — registro de emergencia (móvil) ❌→✅
- **Síntoma:** al crear o listar emergencias, el backend devolvía 500: `column "tecnico_asignado_at" of relation "solicitudes_emergencia" does not exist`.
- **Causa:** el modelo SQLAlchemy (`SolicitudEmergencia` en `emergencias/models.py`) y el portal taller asignan leen/escriben `tecnico_asignado_at`, pero en las migraciones SQL de fase 2 no se había añadido esa columna (solo `taller_id`, `tecnico_id`, `tiempo_estimado_min`, `finalizada_at`).
- **Reparación en repo:** columna añadida al `ALTER` de `0003`; parche idempotente `0006_tecnico_asignado_at.sql`; volumen de compose extendido. **Bases ya creadas** (volumen `postgres_data` no re-ejecuta init): aplicar una vez `ALTER TABLE solicitudes_emergencia ADD COLUMN IF NOT EXISTS tecnico_asignado_at TIMESTAMP;` o ejecutar el contenido de `0006`.

### Docs ✅
- [x] `AGENTS.md` (raíz)
- [x] `docs/ai/*` — visión, arquitectura, estado, handoff, próximos pasos, decisiones
- [x] `mobile/README.md` — `.env`, estructura `lib/cliente` / `lib/tecnico`, usuarios demo

## Lo que falta (priorizado)

### Inmediato
- [ ] Angular: auth completo, layout admin, CRUD/features sobre el lienzo
- [ ] Flutter: tests; registro cliente / flujos edge; refresh token si aplica
- [ ] Tests backend (pytest) ampliados

### Ciclo 2 (resto)
- [x] Flujo principal emergencias (cliente → taller → técnico) — ver `PROJECT_VISION.md` y `NEXT_STEPS.md`
- [x] Módulo IA completo — 6 endpoints validados (audio, imagen, clasificar, resumen, priorizar, rankear talleres)
- [ ] Notificaciones push en tiempo real
- [ ] Geolocalización avanzada / tracking

### Actualización rápida (2026-04-25) — Push “estilo sistema” en app móvil
- [x] `mobile/lib/core/push/fcm_message_listener.dart` cambió de `SnackBar` a notificación local del sistema en foreground usando `flutter_local_notifications`.
- [x] Tap en notificación local ahora navega por deep-link (payload JSON con `target`).
- [x] Canal Android de alta prioridad: `emergencias_high_importance`.
- [x] Backend ahora deja trazas de entrega FCM (`success_count`/`failure_count`) en `backend/app/modules/comunicacion_y_notificaciones/dispositivos_push/fcm_client.py`.
- [x] Dependencia agregada en mobile: `flutter_local_notifications`.
