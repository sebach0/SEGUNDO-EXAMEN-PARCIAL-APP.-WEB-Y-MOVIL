# NEXT_STEPS.md
# =========================================================
# Próximos pasos ordenados por prioridad
# Actualizado: 2026-06-07 — Ciclo 5 Etapa 1D–E completada
# =========================================================

## ALTA — Validar Ciclo 5 Etapa 1D–E (cotizaciones + pagos tenant)

1. `docker compose exec backend alembic upgrade head` (revisión `0014_ciclo5_cotiz_pagos`).
2. Cliente móvil: listar cotizaciones → rechazar una ENVIADA (`PATCH .../rechazar`).
3. Cliente: seleccionar otra cotización → crear pago con monto = `monto_total` aceptado.
4. Admin: `GET /api/admin/payments?tenant_id=1` y `PATCH .../validate-manual` en pago TRANSFERENCIA PENDIENTE.
5. Usuario tenant 2 no debe ver cotizaciones/pagos de tenant 1 (403).

## ALTA — Validar Ciclo 5 Etapa 1B (KPIs / reportes / SLA)

1. `docker compose exec backend alembic upgrade head` (revisión `0013_ciclo5_reports_sla`).
2. Login admin → `GET /api/admin/dashboard/kpis?desde=2026-01-01`.
3. `GET /api/admin/reports/incidents` y `/export/csv`.
4. `GET /api/admin/sla/workshops` y `/workshops/{id}`.
5. Usuario sin `tenants:gestionar` no debe poder filtrar otro `tenant_id`.

## ALTA — Aplicar migración Ciclo 5 Etapa 1A

1. `docker compose exec backend alembic upgrade head` (revisión `0012_ciclo5_tenants_actualizado_permisos`).
2. Probar CU43: `GET/POST/PATCH /api/admin/tenants/` con token admin.
3. Probar CU44: `POST /api/admin/tenants/1/assign-users` con `{ "ids": [N] }`.
4. Verificar bitácora tras crear/editar tenant.

## ALTA — Ciclo 5 Etapa 2 Angular (siguiente implementación)

- [ ] Pantallas admin: `/admin/dashboard`, `/admin/reports`, `/admin/sla`, `/admin/payments`.
- [ ] Etapa 3 Flutter: rechazar cotización + errores cross-tenant.

## MEDIA — Pendiente fase 2

1. Login taller demo → `/taller/panel/mi-taller` → marcar mapa → Guardar.
2. Abrir cotización de solicitud con GPS de incidente → ver distancia, ETA sugerida y mapa.
3. Enviar oferta usando «Usar ~X min» y confirmar que el cliente ve distancia en marketplace.

## ALTA — Validar audio→texto (2026-06-06)

1. Levantar stack con IA: `docker compose --profile ai up -d --build` y `AI_ENABLED=true` en `.env`.
2. Mobile: paso 1 del wizard → grabar descripción → confirmar texto transcrito en el campo.
3. Paso 4 → grabar audio → confirmar tarjeta de transcripción + evidencia en detalle solicitud.
4. Modo avión en paso 1: debe avisar que la transcripción requiere conexión (audio offline sigue en cola en paso 4).

## ALTA — Validar unificación (2026-06-06)

1. **Migración ya aplicada** en Docker: `0009_unificacion_operativa`. Si otra máquina tiene BD antigua: `docker compose exec backend alembic upgrade head`.
2. **Probar KPIs admin:** `/admin/panel/ciclo4/kpis` con solicitudes demo `[DEMO-SC]` — deben aparecer conteos > 0 tras migración.
3. **Probar offline móvil:** modo avión al crear solicitud → SnackBar “guardada localmente”; al reconectar → sync + notificación.
4. **Probar retraso:** asignar técnico con ETA corto, esperar umbral → push “Auxilio demorado” y tarjeta ETA en seguimiento cliente.

## MEDIA — Pendiente fase 2

- [ ] Reportes operacionales PDF/Excel (export KPIs / historial).
- [ ] Unificar cola offline Angular PWA con `solicitudes_emergencia` (hoy Ciclo 4 usa tabla `incidentes` en paralelo).
- [ ] Monitor realtime admin: documentar que WS usa `solicitud_id` como canal tras unificación.
- [ ] ETA dinámico recalculado por distancia GPS técnico→cliente (opcional).

## ALTA — Entorno listo en 5 min

1. Leer **`AGENTS.md`** (raíz).
2. Copiar **`.env.example` → `.env`** en la raíz del repo y ajustar `SECRET_KEY`, DB si hace falta. **IA:** definir **una sola vez** `AI_ENABLED` y `AI_INFERENCE_BASE_URL` (no duplicar bloques al pegar comentarios). Para Docker con worker en la misma red: `AI_ENABLED=true`, `AI_INFERENCE_BASE_URL=http://ai-inference:8080`.
3. **`mobile/.env`** desde `mobile/.env.example` — `API_BASE_URL` (IP/puerto del host desde el dispositivo).
4. **Docker — solo DB + backend + frontend + Mailhog:**  
   `docker compose up -d --build`  
   (timezone contenedores: `TZ=America/La_Paz`; Postgres además `PGTZ=America/La_Paz`)
   **Docker — incluir worker de inferencia (Whisper + YOLO):**  
   `docker compose --profile ai up -d --build`  
   **Docker — además modelo de clasificación propio** (archivo local `backend/incidentes_emergencias_v1.pt`):  
   `docker compose -f docker-compose.yml -f docker-compose.ai-custom-model.yml --profile ai up -d --build`  
   **Si aún falla el build** con `frontend grpc server closed unexpectedly`: el repo ya usa Dockerfiles sin `# syntax=`; en el equipo: reiniciar Docker Desktop, `docker buildx prune`, o variables de sesión `DOCKER_BUILDKIT=0` y `COMPOSE_DOCKER_CLI_BUILD=0` (builder clásico).
5. Luego **`docker compose exec backend python -m app.seeds`** (mismo proyecto; el perfil `ai` no afecta `exec`). Al final: **demo Santa Cruz**, **demo media prioridad** y **stress visual** (catálogo extra + clientes `*.lista.sc-demo.test`; credenciales base en `identidades_demo_sc.py`). Opcional en arranque: `SEED_DEMO_MEDIA_PRIORIDAD_ON_START`, `SEED_STRESS_VISUAL_ON_START`, etc.
6. Probar API: `http://localhost:8000/docs` y health `/health`. Probar IA: `POST /api/ai/images/analyze` con Bearer de un usuario con permiso `ai:inferir` (p. ej. admin tras seeds).
7. **BD ya existente (actualización 2026-04-22):** si aparece `tecnico_asignado_at` inexistente, aplicar el SQL de `backend/migrations/0006_tecnico_asignado_at.sql` (p. ej. con `psql` en el contenedor `db`). Init de Postgres no vuelve a correr en un volumen ya poblado.
8. **BD ya existente (presupuesto BOB, 2026-04-25):** aplicar `backend/migrations/0014_presupuesto_bob_solicitud.sql` con `psql` si la base se creó antes de añadir el archivo al `docker-compose` (nuevos `docker compose up` con volumen virgen montan `14_` automáticamente).
9. **Tras cambiar código de `services/ai-inference/`:** reconstruir el contenedor, p. ej.  
   `docker compose -f docker-compose.yml -f docker-compose.ai-custom-model.yml --profile ai up -d --build --force-recreate ai-inference`
10. **Si backend cae al iniciar por `Unknown constraint max_digits`:** usar la versión actual de `backend/app/modules/portal_tecnico_emergencias/schemas.py` (validación monetaria en `model_validator`) y recrear solo backend:  
   `docker compose -f docker-compose.yml -f docker-compose.ai-custom-model.yml -f docker-compose.override.yml --profile ai up -d --build backend`

## MEDIA — Producto (Ciclo 1 y transversal)

### Angular
- [ ] Auth (login/guard/interceptor) y layout admin
- [ ] Pantallas CRUD alineadas al backend (más allá del portal taller emergencias)
- [x] **Dashboard admin financiero (2026-04-26):** KPIs de comisión plataforma (10%), filtros por fecha, top talleres y serie diaria conectados a `/api/admin/finanzas/resumen|reportes`.
- [x] **Fix de compilación rutas finanzas:** creada vista `features/finanzas/admin-finanzas.component` para resolver import faltante en `admin.routes.ts`.
- [x] **Portal taller emergencias (2026-04-26):** sidebar y rutas **Mis solicitudes**, **Historial de atenciones**, **Servicios asignados**, **Comisiones** (API `historial_atenciones:leer` / `comisiones:leer`); enlaces a detalle vía `bandeja_id` devuelto por backend en historial y listado de comisiones.

### Flutter
- [ ] Tests (unit/widget), refresh token si se expone en API
- [ ] Pulir UX y mensajes de error en red

### Backend
- [ ] Endpoint refresh / recuperación de contraseña real si producto lo exige
- [ ] Paginación y tests pytest ampliados
- [ ] Definir/implementar recurso API `servicios` (rutas, contrato, permisos) para ejecutar la matriz de `docs/ai/TESTING_STRATEGY.md`.

## MEDIA — Dominio emergencias (Ciclo 2; parte ya implementada en repo)

- [x] Backend: `emergencias`, `portal_taller_emergencias` (incl. CU28 asignar técnico), `portal_tecnico_emergencias`
- [x] Flutter cliente: flujo reporte / listado / seguimiento
- [x] Portal web taller: bandeja, detalle, aceptar/rechazar, asignar técnico (CU28), disponibilidad
- [x] **Módulo IA completo** — 6 endpoints validados con respuestas 200 correctas (audio, imagen, clasificar, resumen estructurado, priorizar, rankear talleres)
- [x] **Mobile: visualización IA compuesta** — lectura/render de `damages`, `requires_manual_review`, `conflict_notes`, `score`, `damages_considerados`, `danos_detectados`, `hallazgos_vision_por_imagen`.
- [~] Notificaciones push y geolocalización en tiempo real (mejoras)
  - [x] Registro de token FCM + foreground `onMessage`.
  - [x] Deep-link por tap de notificación (`onMessageOpenedApp` + `getInitialMessage`) hacia chat/detalle.
  - [x] Foreground UX migrada a notificación del sistema (no `SnackBar`) con `flutter_local_notifications`.
  - [x] Push de pago confirmado (simulado + Stripe confirm).
  - [x] Push de bienvenida cliente al primer registro de token.
  - [x] Push al técnico cuando el taller lo asigna a una solicitud (mismo pipeline FCM; ver token único por dispositivo).
  - [x] Logging de entrega FCM en backend (`success_count`/`failure_count`).
  - [ ] Tracking continuo de técnico en mapa en tiempo real (stream) + background location robusta.
  - [ ] Auditar notificaciones “pendientes” y política de replay por ventana de tiempo (hoy: 10 últimas no leídas al primer token).
- [x] Hora de presentación unificada en BOT (Santa Cruz) para web y mobile.
  - [x] Parse UTC naive en mobile para timestamps API sin zona (`api_datetime.dart`).

## ALTA — Validación funcional post-fix (manual)

1. Crear solicitud con cliente.
2. Aceptar y asignar técnico desde taller.
3. Iniciar sesión técnico y registrar token FCM.
4. Verificar llegada de push pendiente de asignación (replay) y notificaciones de nuevos cambios.
5. Cambiar estado a `EN_CAMINO`; confirmar ETA visible (20 min fallback si no definido por taller).
6. Cliente abre seguimiento: validar hora BOT correcta y pago prellenado con presupuesto si existe.
7. Cliente abre `pago_resumen`: validar que el monto bloqueado coincida con `presupuesto_bob` del técnico; usar botón/gesto de refresco y confirmar que cambia de “no definido” a monto visible sin reiniciar app.
8. IA incidente compuesto: probar en Swagger
   - `POST /api/ai/images/analyze-batch` con 2-3 fotos distintas.
   - `POST /api/ai/incidents/classify` con `transcripciones_audio[]` y `hallazgos_vision_por_imagen[]`.
   - verificar `damages[]` y `requires_manual_review`.
9. Priorización compuesta:
   - `POST /api/ai/incidents/prioritize` y verificar `score` + `damages_considerados[]`.
10. Resumen compuesto:
   - `POST /api/ai/incidents/structured-summary` y verificar `danos_detectados[]`.

## BAJA

- [ ] CI/CD, despliegue documentado

## Obsoleto (ya hecho)

- ~~`flutter create` / `ng new`~~ — proyectos ya inicializados.
- ~~Alembic baseline~~ — configurado; usar `alembic stamp` / `upgrade` según doc del README raíz.
- ~~Remover etiquetas internas `Ciclo` / `CUxx` en frontend/mobile~~ — aplicado en vistas y copys visibles.
