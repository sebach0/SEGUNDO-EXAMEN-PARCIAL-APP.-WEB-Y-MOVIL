# Plataforma Inteligente de Atención de Emergencias Vehiculares 🚗🚨

Sistema digital completo, modular y escalable para coordinar y auditar la atención de emergencias vehiculares. Conecta clientes y sus vehículos con talleres, técnicos asignados y un panel administrativo de auditoría, manteniendo trazabilidad completa.

---

## 📋 Requisitos Previos

Asegúrate de contar con lo siguiente instalado en tu entorno local antes de iniciar:

- **Docker** y **Docker Compose**
- **Node.js** (v18+) y **npm**
- **Angular CLI** (v17+) `npm install -g @angular/cli@17`
- **Flutter SDK** (v3.3+)
- (Opcional) Cliente de visualización de base de datos tipo DBeaver o PgAdmin.

---

## 🐳 Gestión de Contenedores y Entorno con Docker

La arquitectura local está enteramente dockerizada. Es vital contar con el `.env` creado usando tu archivo `.env.example` como base.

### Flujo habitual de comandos (orden sugerido)

Orden recomendado según el stack (**sin IA**, **con IA** o **con IA + modelo custom**). El paso 1 es opcional (reset agresivo).

| Paso                                                                   | Sin worker IA                                     | Con worker IA (`--profile ai`)                  | Con IA + modelo custom (`.pt` en `backend/`)                                                                  |
| ---------------------------------------------------------------------- | ------------------------------------------------- | ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| **1 (opc.)** Reset fuerte: borra volúmenes **e imágenes** del proyecto | `docker compose down -v --rmi all`                | `docker compose --profile ai down -v --rmi all` | `docker compose -f docker-compose.yml -f docker-compose.ai-custom-model.yml --profile ai down -v --rmi all`   |
| **2** Construir y levantar                                             | `docker compose up -d --build`                    | `docker compose --profile ai up -d --build`     | `docker compose -f docker-compose.yml -f docker-compose.ai-custom-model.yml --profile ai up -d --build`       |
| **3** Ver revisión Alembic                                             | `docker compose exec backend alembic current`     | Igual                                           | `docker compose -f docker-compose.yml -f docker-compose.ai-custom-model.yml exec backend alembic current`     |
| **4** Seeds (usuarios demo, catálogos, etc.)                           | `docker compose exec backend python -m app.seeds` | Igual                                           | `docker compose -f docker-compose.yml -f docker-compose.ai-custom-model.yml exec backend python -m app.seeds` |

> Si levantaste con `-f docker-compose.ai-custom-model.yml`, usá **los mismos** `-f` y `--profile ai` en `down` y `exec` para que Compose apunte al mismo proyecto.

### Arranque del entorno

| Acción                                                                                                                                  | Comando                                                                                                 |
| --------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| **Levantar e inicializar todo** (Recomendado primera vez)                                                                               | `docker compose up -d --build`                                                                          |
| **Incluir worker de IA** (Whisper + YOLO; servicio `ai-inference`)                                                                      | `docker compose --profile ai up -d --build`                                                             |
| **IA + modelo de clasificación propio** (peso local + `.env` con `YOLO_TASK=classify`; el override **monta** el `.pt` en el contenedor) | `docker compose -f docker-compose.yml -f docker-compose.ai-custom-model.yml --profile ai up -d --build` |
| Levantar servicios creados                                                                                                              | `docker compose up -d`                                                                                  |
| Detener los contenedores                                                                                                                | `docker compose down`                                                                                   |
| **Peligro:** Detener y borrar volúmenes (⚠️ Borra toda la base de datos)                                                                | `docker compose down -v`                                                                                |
| **Peligro:** Igual que arriba **y** borrar imágenes construidas del proyecto                                                            | `docker compose down -v --rmi all`                                                                      |

El primer arranque tras `docker compose down -v --rmi all` puede tardar varios minutos (build de imágenes, Postgres hasta _healthy_, descarga de modelos en el volumen de caché del worker).

### Logs y Troubleshooting

| Acción                                                                   | Comando                               |
| ------------------------------------------------------------------------ | ------------------------------------- |
| Ver logs en vivo de todos los servicios                                  | `docker compose logs -f`              |
| Ver logs exclusivos del backend                                          | `docker compose logs -f backend`      |
| Ver logs del frontend                                                    | `docker compose logs -f frontend`     |
| Ver logs de la base de datos                                             | `docker compose logs -f db`           |
| Ver logs del worker de inferencia (si está levantado con `--profile ai`) | `docker compose logs -f ai-inference` |
| Reiniciar únicamente el backend                                          | `docker compose restart backend`      |

### IA modular (opcional)

El backend expone rutas bajo `/api/ai/...` y puede delegar audio e imagen a un contenedor **`ai-inference`** en la misma red Docker. Contexto técnico, incidentes resueltos y variables: **[docs/ai/HANDOFF_LATEST.md](docs/ai/HANDOFF_LATEST.md)** y **[docs/ai/CURRENT_STATE.md](docs/ai/CURRENT_STATE.md)**.

- **`.env` en la raíz del repo:** para usar el worker, `AI_ENABLED=true` y `AI_INFERENCE_BASE_URL=http://ai-inference:8080`. No dupliques esas claves en el mismo archivo (la última línea suele ganar y el backend responde 503 como si la IA estuviera apagada). Detalle en `.env.example`.
- **Permiso:** los endpoints de inferencia requieren **`ai:inferir`** (p. ej. usuario admin tras seeds).
- **Tras cambiar código en `services/ai-inference/`:** reconstruir solo ese servicio, por ejemplo:  
  `docker compose -f docker-compose.yml -f docker-compose.ai-custom-model.yml --profile ai up -d --build --force-recreate ai-inference`  
  (si no usás modelo custom, alcanza `docker compose --profile ai ...` sin el segundo `-f`).
- **Incidentes compuestos (Fase 1):**
  - `POST /api/ai/images/analyze-batch` acepta `files[]` y devuelve `hallazgos_consolidados`.
  - `POST /api/ai/incidents/classify` soporta `transcripciones_audio[]` y `hallazgos_vision_por_imagen[]`.
  - la clasificación ahora devuelve `damages[]` (multi-daño) + `requires_manual_review`.
  - `POST /api/ai/incidents/prioritize` devuelve además `score` y `damages_considerados[]`.

**Payload ejemplo (incidente compuesto):**

```json
{
  "texto_cliente": "sufri un choque, tengo vidrios rotos y llanta pinchada",
  "transcripcion_audio": "estoy en la autopista, no puedo mover el auto",
  "transcripciones_audio": ["tambien hay vidrio por todo lado"],
  "hallazgos_vision_por_imagen": [
    ["choque frontal", "vidrio roto"],
    ["llanta pinchada delantera"]
  ]
}
```

---

## 🐍 Backend (FastAPI + SQLAlchemy + Alembic)

A diferencia de Django, FastAPI no cuenta con un motor ORM o de migraciones nativo. Utilizamos **SQLAlchemy** para mapear los objetos y **Alembic** para el control de versiones (migraciones).

| Acción                                              | Django ORM                                  | Equivalente en FastAPI (Alembic)                                                    |
| --------------------------------------------------- | ------------------------------------------- | ----------------------------------------------------------------------------------- |
| **Preparar migración** detectando los cambios       | `python manage.py makemigrations`           | `docker compose exec backend alembic revision --autogenerate -m "Agregado campo X"` |
| **Ejecutar / Aplicar** migración a la base de datos | `python manage.py migrate`                  | `docker compose exec backend alembic upgrade head`                                  |
| **Deshacer (Rollback)** la última migración         | `python manage.py migrate <app> <anterior>` | `docker compose exec backend alembic downgrade -1`                                  |

### Alembic en este repositorio

- **Qué es:** versiona el esquema de PostgreSQL (cambios incrementales en archivos Python bajo `backend/alembic/versions/`), parecido a las carpetas `migrations/` de Django.
- **No sustituye el backend:** FastAPI, routers y modelos siguen igual; solo se añade la herramienta de migración.
- **Convivencia con `init.sql`:** la primera migración (`0001_baseline`) está vacía: el esquema inicial lo sigue creando Docker con `backend/migrations/init.sql` la primera vez que levantas Postgres. En ese mismo arranque se aplican `0002_ciclo2_fase1_emergencias.sql` (CU11–CU15), `0003_ciclo2_fase2_seguimiento.sql` (CU16–CU18) y `0004_ciclo2_fase3_comunicaciones.sql` (CU19–CU21: notificaciones, mensajes, FCM).
- **Bases ya creadas** (volumen Postgres antiguo): `docker compose exec backend alembic upgrade head` o ejecutar el SQL con `psql` contra tu instancia.
- **Una vez por base de datos** creada con ese flujo, marca la línea base para Alembic (sin ejecutar SQL otra vez). Primero levantá el stack (con o sin perfil `ai`; Alembic corre en `backend`):

```bash
cd d:\Examen-1-SI2
docker compose up -d --build
docker compose exec backend alembic stamp 0001_baseline
docker compose exec backend alembic stamp 0002_ciclo2_fase1_emergencias
```

(El segundo `stamp` refleja el SQL de emergencias ya aplicado por `02_ciclo2_fase1_emergencias.sql` en bases nuevas con Docker. Si usás compose con `-f docker-compose.ai-custom-model.yml`, los mismos `exec` aplican una vez que `backend` esté arriba.)

A partir de ahí, cuando **realmente cambies** modelos SQLAlchemy: `revision --autogenerate -m "mensaje útil"` → **revisar a mano** el `.py` generado (autogenerate se equivoca con IDENTITY, índices y nombres de FK) → `upgrade head`.

**Importante:** no ejecutes `--autogenerate` “de prueba” sin cambios en código: suele generar un diff enorme contra la BD creada por `init.sql` y `upgrade head` puede fallar (p. ej. `ALTER COLUMN id` en columnas IDENTITY). Si ya generaste un archivo malo en `alembic/versions/`, bórralo; si `upgrade` falló, la versión en BD suele seguir en `0001_baseline` (transacción revertida).

- **Poblar datos demo (seeds):** `docker compose exec backend python -m app.seeds` — admin, cliente, taller, técnico según `SEED_*` (defaults en `backend/app/seeds/identidades_demo_sc.py`: nombres bolivianos, Santa Cruz, teléfonos +591 7701 00xx, dominio `*.sc-demo.test`, contraseña corta `scdemo1`). Catálogos de vehículo si faltan. Luego **demo Santa Cruz** (`[DEMO-SC]`), **demo media prioridad** (notificaciones, chat, `ai_payload`, disponibilidad, **segundo taller en Santa Cruz** con bandeja retroactiva) y **stress visual** (más marcas/modelos y 8 clientes `*.lista.sc-demo.test`). Variables opcionales: `SEED_*` en `.env` raíz (ver `.env.example`).

**Nota:** Alembic usa el driver síncrono **psycopg** (`postgresql+psycopg://…`); la API sigue usando **asyncpg** (`postgresql+asyncpg://…`). La conversión la hace `backend/alembic/env.py`.

---

## 🗄️ Base de Datos e Inicialización

Al crear el contenedor PostgreSQL con volumen vacío, se montan los `*.sql` numerados en `docker-entrypoint-initdb.d/` (`01_` … `04_`). Alembic gestiona **cambios posteriores** al esquema (p. ej. `alembic upgrade head` tras un merge de revisiones).

| Acción                               | Comando                                                                                                        |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------------- |
| **Inicializar BD automáticamente**   | Ejecutando _docker compose up_, postgres detecta `init.sql` e inicializa si está vacío el volumen.             |
| **Destruir BD y recrear desde cero** | `docker compose down -v && docker compose up -d db`                                                            |
| **Forzar ejecución del archivo SQL** | `docker compose exec db psql -U emergencias_user -d emergencias_db -f /docker-entrypoint-initdb.d/01_init.sql` |
| Entrar a la consola de la BD         | `docker compose exec db psql -U emergencias_user -d emergencias_db`                                            |

---

## 🌐 Frontend (Angular Web)

El frontend web expone los paneles de administración y consumo de datos consumiendo los recursos bajo Nginx al compilarse en servidor para producción y en node para desarrollo de forma local.

_(Asegúrate de estar en el directorio root `/frontend`)_

| Acción                                             | Comando Ejecutivo                     |
| -------------------------------------------------- | ------------------------------------- |
| Descargar e instalar dependencias del proyecto     | `npm install`                         |
| Servir ambiente y desarrollar local (Hot Reload)   | `ng serve`                            |
| Ejecutar lints de análisis estático                | `ng lint`                             |
| Construir / Compilar aplicación final (Producción) | `ng build --configuration production` |

---

## 📱 Móvil (Flutter)

App para **cliente** (registro, vehículos, perfil) y **técnico / responsable de taller** (login, home, perfil, placeholders de servicios). Configuración por `mobile/.env` (`API_BASE_URL`, `APP_NAME`). Detalle: **[mobile/README.md](mobile/README.md)**.

_(Directorio del proyecto: `mobile/`)_

| Acción                             | Comando             |
| ---------------------------------- | ------------------- |
| Dependencias                       | `flutter pub get`   |
| Ejecutar en emulador o dispositivo | `flutter run`       |
| Análisis estático                  | `dart analyze`      |
| Limpiar build local                | `flutter clean`     |
| APK Android                        | `flutter build apk` |

Usuarios demo del backend (tras seeds): ver `identidades_demo_sc.py` — por ejemplo **cliente** `carlos.vega@sc-demo.test` / `scdemo1`, **taller** `luis.rivera@sc-demo.test` / `scdemo1`, **técnico** `marco.salas@sc-demo.test` / `scdemo1`, **admin** `patricio.mendez@sc-demo.test` / `scdemo1` (todo sobreescribible con `SEED_*` en `.env`).

---

## 🔐 Notas Adicionales y Buenas Prácticas

1. **La carpeta [`docs/ai/`](docs/ai/) es vital.** Contexto del software: [`HANDOFF_LATEST.md`](docs/ai/HANDOFF_LATEST.md) (último handoff), [`CURRENT_STATE.md`](docs/ai/CURRENT_STATE.md), [`ARCHITECTURE.md`](docs/ai/ARCHITECTURE.md), [`DECISIONS_LOG.md`](docs/ai/DECISIONS_LOG.md), [`NEXT_STEPS.md`](docs/ai/NEXT_STEPS.md). Revísala al incorporarte o tras cambios grandes (emergencias, IA, Docker).
2. Si por algún motivo tienes errores de _caché de Docker_, fuerza el build con la bandera limpia: `docker compose build --no-cache`.
3. Nunca adjuntar datos de variables de entorno (como `SECRET_KEY` o contraseñas) dentro de archivos de repositorio. Manipula esto con los `.env`.

---

## 📌 Referencia Rápida de Comandos

### Docker — Levantar el stack

```bash
# Solo DB + Backend + Frontend + Mailhog
docker compose up -d --build

# Incluir worker de IA (Whisper + YOLO genérico)
docker compose --profile ai up -d --build

# IA + modelo de clasificación propio (backend/incidentes_emergencias_v1.pt)
docker compose -f docker-compose.yml -f docker-compose.ai-custom-model.yml --profile ai up -d --build
```

### Docker — Reconstruir un solo servicio

```bash
# Reconstruir solo el backend (sin tocar otros contenedores)
docker compose up -d --build --force-recreate backend

# Reconstruir solo el worker de IA (sin modelo custom)
docker compose --profile ai up -d --build --force-recreate ai-inference

# Reconstruir solo el worker de IA (con modelo custom)
docker compose -f docker-compose.yml -f docker-compose.ai-custom-model.yml --profile ai up -d --build --force-recreate ai-inference

# Reconstruir solo el frontend
docker compose up -d --build --force-recreate frontend
```

### Docker — Bajar el stack

```bash
# Detener contenedores (mantiene volúmenes e imágenes)
docker compose down

# Detener + borrar volúmenes ⚠️ borra la BD
docker compose down -v

# Detener + borrar volúmenes e imágenes ⚠️ reset completo
docker compose down -v --rmi all

# Lo mismo incluyendo el perfil ai (baja también ai-inference)
docker compose --profile ai down -v --rmi all

# Lo mismo con el override del modelo custom
docker compose -f docker-compose.yml -f docker-compose.ai-custom-model.yml --profile ai down -v --rmi all
```

### Migraciones (Alembic)

```bash
# Ver revisión actual de la BD
docker compose exec backend alembic current

# Ver historial de migraciones
docker compose exec backend alembic history

# Aplicar todas las migraciones pendientes
docker compose exec backend alembic upgrade head

# Deshacer la última migración
docker compose exec backend alembic downgrade -1

# Crear nueva migración (auto-detecta cambios en modelos)
docker compose exec backend alembic revision --autogenerate -m "descripcion del cambio"

# Marcar línea base (primera vez, sin re-ejecutar SQL)
docker compose exec backend alembic stamp 0001_baseline
```

### Seeds (datos demo)

```bash
# Crear todos los usuarios demo (admin, cliente, taller, técnico)
docker compose exec backend python -m app.seeds

# Si levantaste con el perfil ai o el override, el exec es igual:
docker compose --profile ai exec backend python -m app.seeds
docker compose -f docker-compose.yml -f docker-compose.ai-custom-model.yml --profile ai exec backend python -m app.seeds
```

Usuarios creados por los seeds (configurables en `.env` con `SEED_*`):

| Rol     | Email                          | Contraseña |
| ------- | ------------------------------ | ---------- |
| Admin   | `patricio.mendez@sc-demo.test` | `scdemo1`  |
| Cliente | `carlos.vega@sc-demo.test`     | `scdemo1`  |
| Taller  | `luis.rivera@sc-demo.test`     | `scdemo1`  |
| Técnico | `marco.salas@sc-demo.test`     | `scdemo1`  |

### Base de datos — Acceso directo

```bash
# Entrar a la consola psql
docker compose exec db psql -U emergencias_user -d emergencias_db

# Ejecutar un archivo SQL contra la BD (ej. parche idempotente)
docker compose exec -i db psql -U emergencias_user -d emergencias_db < backend/migrations/0006_tecnico_asignado_at.sql

# Destruir BD y recrear desde cero
docker compose down -v && docker compose up -d --build
```

### Logs

```bash
# Todos los servicios en vivo
docker compose logs -f

# Solo un servicio
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
docker compose logs -f ai-inference

# Últimas 100 líneas de un servicio
docker compose logs --tail=100 backend
```

### Flujo completo desde cero (primera vez)

```bash
# 1. Copiar variables de entorno
cp .env.example .env          # editar SECRET_KEY, CORS_ORIGINS, EMAIL_*, FRONTEND_*, BACKEND_URL, MAILHOG_WEB_URL, SMTP_*…
cp mobile/.env.example mobile/.env   # editar API_BASE_URL
# Frontend local (`cd frontend && npm start`): el proxy exige BACKEND_URL en el `.env` raíz; `prestart` genera MailHog desde MAILHOG_WEB_URL.

# 2. Levantar el stack (con IA + modelo custom)
docker compose -f docker-compose.yml -f docker-compose.ai-custom-model.yml --profile ai up -d --build

docker compose -f docker-compose.yml -f docker-compose.ai-custom-model.yml --profile ai up
 -d --build --force-recreate ai-inference

# 3. Esperar a que Postgres esté healthy, luego correr seeds
docker compose exec backend python -m app.seeds

# 4. Verificar
#    API:    http://localhost:8000/docs
#    Web:    http://localhost:80
#    Mail:   http://localhost:8025
```

1
docker compose down -v --rmi all

docker compose --profile ai -f docker-compose.yml -f docker-compose.override.yml down -v --rmi all
2
docker compose -f docker-compose.yml -f docker-compose.ai-custom-model.yml --profile ai up -d --build --force-recreate ai-inference

docker compose -f docker-compose.yml -f docker-compose.ai-custom-model.yml -f docker-compose.override.yml --profile ai up -d --build

docker compose -f docker-compose.yml -f docker-compose.ai-custom-model.yml --profile ai up -d --build

3
docker compose exec backend alembic current
4
docker compose exec backend alembic upgrade head
5
docker compose exec backend python -m app.seeds
###########

1Flujo recomendado (desde cero, limpio)
Levantar y construir contenedores
docker compose -f docker-compose.yml -f docker-compose.ai-custom-model.yml -f docker-compose.override.yml --profile ai up -d --build

2Esperar que DB esté healthy
docker compose -f docker-compose.yml -f docker-compose.ai-custom-model.yml -f docker-compose.override.yml ps
(la DB debe verse healthy)

3Marcar versión Alembic (NO upgrade)
docker compose -f docker-compose.yml -f docker-compose.ai-custom-model.yml -f docker-compose.override.yml exec backend alembic stamp 0006_ciclo2_fase4_pagos

4Cargar seeders
docker compose -f docker-compose.yml -f docker-compose.ai-custom-model.yml -f docker-compose.override.yml exec backend python -m app.seeds

5Verificar
docker compose -f docker-compose.yml -f docker-compose.ai-custom-model.yml -f docker-compose.override.yml exec backend alembic current

#si
