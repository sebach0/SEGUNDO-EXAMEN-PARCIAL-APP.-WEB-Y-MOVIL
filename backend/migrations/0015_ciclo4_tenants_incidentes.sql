-- =========================================================
-- 0015_ciclo4_tenants_incidentes.sql
-- Ciclo #4: Multi-tenant + Incidentes v2 + Tiempo Real + Offline Sync
-- NO modifica solicitudes_emergencia (Ciclo 1-3 intacto).
-- =========================================================

BEGIN;

-- =========================================================
-- TENANTS  (raíz del aislamiento SaaS)
-- =========================================================
CREATE TABLE IF NOT EXISTS tenants (
    id      INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre  VARCHAR(150) NOT NULL,
    slug    VARCHAR(80)  NOT NULL UNIQUE,
    estado  VARCHAR(20)  NOT NULL DEFAULT 'ACTIVO',
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_tenants_estado CHECK (estado IN ('ACTIVO','INACTIVO','SUSPENDIDO'))
);

-- Tenant por defecto (retrocompatibilidad con datos Ciclo 1-3)
INSERT INTO tenants (nombre, slug, estado)
VALUES ('Red Principal', 'principal', 'ACTIVO')
ON CONFLICT (slug) DO NOTHING;

-- =========================================================
-- TENANT_ID en USUARIOS  (nullable — retrocompatible)
-- =========================================================
ALTER TABLE usuarios
    ADD COLUMN IF NOT EXISTS tenant_id INTEGER
    REFERENCES tenants(id) ON UPDATE CASCADE ON DELETE SET NULL;

-- Asignar usuarios existentes al tenant por defecto
UPDATE usuarios SET tenant_id = (SELECT id FROM tenants WHERE slug = 'principal')
WHERE tenant_id IS NULL;

CREATE INDEX IF NOT EXISTS idx_usuarios_tenant_id ON usuarios(tenant_id);

-- =========================================================
-- CATÁLOGOS OPERATIVOS
-- =========================================================
CREATE TABLE IF NOT EXISTS tipos_incidente (
    id          INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre      VARCHAR(60)  NOT NULL UNIQUE,
    descripcion VARCHAR(150)
);

INSERT INTO tipos_incidente (nombre, descripcion) VALUES
    ('BATERIA', 'Fallo o descarga de batería'),
    ('LLANTA',  'Pinchazo o cambio de llanta'),
    ('MOTOR',   'Falla mecánica de motor'),
    ('CHOQUE',  'Colisión o accidente'),
    ('OTROS',   'Otro tipo de emergencia')
ON CONFLICT (nombre) DO NOTHING;

CREATE TABLE IF NOT EXISTS zonas (
    id        INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    nombre    VARCHAR(100) NOT NULL,
    ciudad    VARCHAR(100),
    CONSTRAINT fk_zonas_tenant  FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT uq_zonas_tenant_nombre UNIQUE (tenant_id, nombre)
);

-- =========================================================
-- ENUMS  Ciclo 4
-- =========================================================
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'estado_incidente_v2') THEN
        CREATE TYPE estado_incidente_v2 AS ENUM (
            'PENDIENTE',
            'BUSCANDO_TALLER',
            'TALLER_ASIGNADO',
            'EN_CAMINO',
            'EN_ATENCION',
            'FINALIZADO',
            'CANCELADO'
        );
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sync_estado_incidente') THEN
        CREATE TYPE sync_estado_incidente AS ENUM (
            'pendiente',
            'enviado',
            'sincronizado',
            'error'
        );
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'origen_incidente') THEN
        CREATE TYPE origen_incidente AS ENUM (
            'ONLINE',
            'OFFLINE'
        );
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'estado_incidente_taller') THEN
        CREATE TYPE estado_incidente_taller AS ENUM (
            'OFRECIDO',
            'ACEPTADO',
            'RECHAZADO',
            'SELECCIONADO',
            'CANCELADO'
        );
    END IF;
END $$;

-- =========================================================
-- INCIDENTES v2  (núcleo de tiempo real + offline + KPIs)
-- =========================================================
CREATE TABLE IF NOT EXISTS incidentes (
    id                   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_id            INTEGER  NOT NULL,
    cliente_id           INTEGER  NOT NULL,
    vehiculo_id          INTEGER  NOT NULL,
    tipo_incidente_id    INTEGER,
    zona_id              INTEGER,
    taller_asignado_id   INTEGER,
    descripcion          TEXT,
    estado               estado_incidente_v2    NOT NULL DEFAULT 'PENDIENTE',
    prioridad            VARCHAR(10)            NOT NULL DEFAULT 'MEDIA',
    latitud              NUMERIC(9,6),
    longitud             NUMERIC(9,6),
    direccion_referencia VARCHAR(255),
    sla_minutos          INTEGER                NOT NULL DEFAULT 60,
    -- soporte offline
    origen               origen_incidente       NOT NULL DEFAULT 'ONLINE',
    client_uuid          UUID,
    sync_estado          sync_estado_incidente  NOT NULL DEFAULT 'sincronizado',
    -- timestamps ciclo de vida  (base de KPIs)
    reportado_en         TIMESTAMPTZ            NOT NULL DEFAULT now(),
    buscando_taller_en   TIMESTAMPTZ,
    asignado_en          TIMESTAMPTZ,
    en_camino_en         TIMESTAMPTZ,
    en_atencion_en       TIMESTAMPTZ,
    finalizado_en        TIMESTAMPTZ,
    cancelado_en         TIMESTAMPTZ,
    motivo_cancelacion   VARCHAR(255),
    creado_en            TIMESTAMPTZ            NOT NULL DEFAULT now(),
    actualizado_en       TIMESTAMPTZ            NOT NULL DEFAULT now(),
    CONSTRAINT fk_incidentes_tenant   FOREIGN KEY (tenant_id)          REFERENCES tenants(id)        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_incidentes_cliente  FOREIGN KEY (cliente_id)         REFERENCES clientes(id)       ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_incidentes_vehiculo FOREIGN KEY (vehiculo_id)        REFERENCES vehiculos(id)      ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_incidentes_tipo     FOREIGN KEY (tipo_incidente_id)  REFERENCES tipos_incidente(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_incidentes_zona     FOREIGN KEY (zona_id)            REFERENCES zonas(id)          ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_incidentes_taller   FOREIGN KEY (taller_asignado_id) REFERENCES talleres(id)       ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_incidentes_prioridad CHECK (prioridad IN ('BAJA','MEDIA','ALTA','CRITICA')),
    -- anti-duplicado offline: mismo client_uuid+tenant nunca entra dos veces
    CONSTRAINT uq_incidentes_tenant_clientuuid UNIQUE (tenant_id, client_uuid)
);

-- =========================================================
-- ASIGNACIÓN TALLER ↔ INCIDENTE
-- =========================================================
CREATE TABLE IF NOT EXISTS incidente_taller (
    id             INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_id      INTEGER  NOT NULL,
    incidente_id   INTEGER  NOT NULL,
    taller_id      INTEGER  NOT NULL,
    estado         estado_incidente_taller NOT NULL DEFAULT 'OFRECIDO',
    distancia_km   NUMERIC(8,2),
    ofrecido_en    TIMESTAMPTZ NOT NULL DEFAULT now(),
    respondido_en  TIMESTAMPTZ,
    motivo_rechazo VARCHAR(255),
    CONSTRAINT fk_inctaller_tenant    FOREIGN KEY (tenant_id)    REFERENCES tenants(id)    ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_inctaller_incidente FOREIGN KEY (incidente_id) REFERENCES incidentes(id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_inctaller_taller    FOREIGN KEY (taller_id)    REFERENCES talleres(id)   ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT uq_inctaller           UNIQUE (incidente_id, taller_id)
);

-- =========================================================
-- HISTORIAL DE ESTADOS  (trazabilidad)
-- =========================================================
CREATE TABLE IF NOT EXISTS incidente_estado_historial (
    id              INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_id       INTEGER      NOT NULL,
    incidente_id    INTEGER      NOT NULL,
    estado_anterior VARCHAR(30),
    estado_nuevo    VARCHAR(30)  NOT NULL,
    usuario_id      INTEGER,
    comentario      VARCHAR(255),
    creado_en       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT fk_histestado_tenant    FOREIGN KEY (tenant_id)    REFERENCES tenants(id)    ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_histestado_incidente FOREIGN KEY (incidente_id) REFERENCES incidentes(id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_histestado_usuario   FOREIGN KEY (usuario_id)   REFERENCES usuarios(id)   ON UPDATE CASCADE ON DELETE SET NULL
);

-- =========================================================
-- TRACKING EN TIEMPO REAL  (GPS del técnico/taller)
-- =========================================================
CREATE TABLE IF NOT EXISTS incidente_tracking (
    id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_id      INTEGER       NOT NULL,
    incidente_id   INTEGER       NOT NULL,
    taller_id      INTEGER,
    tecnico_id     INTEGER,
    latitud        NUMERIC(9,6)  NOT NULL,
    longitud       NUMERIC(9,6)  NOT NULL,
    velocidad_kmh  NUMERIC(6,2),
    registrado_en  TIMESTAMPTZ   NOT NULL DEFAULT now(),
    CONSTRAINT fk_tracking_tenant    FOREIGN KEY (tenant_id)    REFERENCES tenants(id)    ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_tracking_incidente FOREIGN KEY (incidente_id) REFERENCES incidentes(id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_tracking_taller    FOREIGN KEY (taller_id)    REFERENCES talleres(id)   ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT fk_tracking_tecnico   FOREIGN KEY (tecnico_id)   REFERENCES tecnicos(id)   ON UPDATE CASCADE ON DELETE SET NULL
);

-- =========================================================
-- EVENTOS DE TIEMPO REAL  (log de WebSocket events)
-- =========================================================
CREATE TABLE IF NOT EXISTS eventos_tiempo_real (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_id    INTEGER       NOT NULL,
    incidente_id INTEGER,
    usuario_id   INTEGER,
    canal        VARCHAR(120)  NOT NULL,   -- ej. "incidente:123"
    tipo_evento  VARCHAR(80)   NOT NULL,   -- ESTADO_CAMBIADO, TRACKING_UPDATE, …
    payload      JSONB,
    emitido_en   TIMESTAMPTZ   NOT NULL DEFAULT now(),
    CONSTRAINT fk_evtrt_tenant    FOREIGN KEY (tenant_id)    REFERENCES tenants(id)    ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_evtrt_incidente FOREIGN KEY (incidente_id) REFERENCES incidentes(id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_evtrt_usuario   FOREIGN KEY (usuario_id)   REFERENCES usuarios(id)   ON UPDATE CASCADE ON DELETE SET NULL
);

-- =========================================================
-- SINCRONIZACIÓN OFFLINE  (cola + anti-duplicado)
-- =========================================================
CREATE TABLE IF NOT EXISTS sincronizacion_offline (
    id                  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_id           INTEGER      NOT NULL,
    usuario_id          INTEGER,
    entidad             VARCHAR(50)  NOT NULL,   -- 'incidente', 'evento', …
    client_uuid         UUID         NOT NULL,
    payload             JSONB        NOT NULL,
    estado_local        VARCHAR(20)  NOT NULL DEFAULT 'pendiente',
    intentos            INTEGER      NOT NULL DEFAULT 0,
    ultimo_error        TEXT,
    incidente_id        INTEGER,
    registrado_local_en TIMESTAMPTZ,
    sincronizado_en     TIMESTAMPTZ,
    creado_en           TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT fk_syncoff_tenant    FOREIGN KEY (tenant_id)    REFERENCES tenants(id)    ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_syncoff_usuario   FOREIGN KEY (usuario_id)   REFERENCES usuarios(id)   ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT fk_syncoff_incidente FOREIGN KEY (incidente_id) REFERENCES incidentes(id) ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT chk_syncoff_estado   CHECK (estado_local IN ('pendiente','enviado','sincronizado','error')),
    CONSTRAINT uq_syncoff_tenant_uuid UNIQUE (tenant_id, client_uuid)
);

CREATE TABLE IF NOT EXISTS errores_sincronizacion (
    id                INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_id         INTEGER      NOT NULL,
    sincronizacion_id INTEGER      NOT NULL,
    intento_num       INTEGER      NOT NULL,
    codigo_error      VARCHAR(60),
    detalle           TEXT,
    ocurrido_en       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT fk_errsync_tenant FOREIGN KEY (tenant_id)         REFERENCES tenants(id)               ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_errsync_sync   FOREIGN KEY (sincronizacion_id) REFERENCES sincronizacion_offline(id) ON UPDATE CASCADE ON DELETE CASCADE
);

-- =========================================================
-- ÍNDICES
-- =========================================================
CREATE INDEX IF NOT EXISTS idx_zonas_tenant_id           ON zonas(tenant_id);
CREATE INDEX IF NOT EXISTS idx_incidentes_tenant_id      ON incidentes(tenant_id);
CREATE INDEX IF NOT EXISTS idx_incidentes_cliente_id     ON incidentes(cliente_id);
CREATE INDEX IF NOT EXISTS idx_incidentes_vehiculo_id    ON incidentes(vehiculo_id);
CREATE INDEX IF NOT EXISTS idx_incidentes_estado         ON incidentes(estado);
CREATE INDEX IF NOT EXISTS idx_incidentes_sync_estado    ON incidentes(sync_estado);
CREATE INDEX IF NOT EXISTS idx_incidentes_taller_asig    ON incidentes(taller_asignado_id);
CREATE INDEX IF NOT EXISTS idx_inctaller_incidente_id    ON incidente_taller(incidente_id);
CREATE INDEX IF NOT EXISTS idx_inctaller_taller_id       ON incidente_taller(taller_id);
CREATE INDEX IF NOT EXISTS idx_histestado_incidente_id   ON incidente_estado_historial(incidente_id);
CREATE INDEX IF NOT EXISTS idx_tracking_incidente_id     ON incidente_tracking(incidente_id);
CREATE INDEX IF NOT EXISTS idx_evtrt_tenant_id           ON eventos_tiempo_real(tenant_id);
CREATE INDEX IF NOT EXISTS idx_evtrt_incidente_id        ON eventos_tiempo_real(incidente_id);
CREATE INDEX IF NOT EXISTS idx_syncoff_tenant_id         ON sincronizacion_offline(tenant_id);
CREATE INDEX IF NOT EXISTS idx_syncoff_estado            ON sincronizacion_offline(estado_local);
CREATE INDEX IF NOT EXISTS idx_errsync_sync_id           ON errores_sincronizacion(sincronizacion_id);

-- =========================================================
-- PERMISOS Ciclo 4  (incidentes v2 + sync)
-- =========================================================
INSERT INTO permisos (codigo, nombre, modulo, created_at, updated_at) VALUES
    ('incidentes_v2:crear',     'Crear incidentes Ciclo 4',         'incidentes_v2', NOW(), NOW()),
    ('incidentes_v2:leer',      'Ver incidentes Ciclo 4',           'incidentes_v2', NOW(), NOW()),
    ('incidentes_v2:actualizar','Actualizar estado incidente C4',   'incidentes_v2', NOW(), NOW()),
    ('sync:usar',               'Usar endpoints de sincronización', 'sync',          NOW(), NOW()),
    ('tracking:enviar',         'Enviar posición GPS de tracking',  'incidentes_v2', NOW(), NOW()),
    ('tenants:gestionar',       'Gestionar tenants (admin)',        'tenants',       NOW(), NOW())
ON CONFLICT (codigo) DO NOTHING;

-- Asignar nuevos permisos al ADMIN (todos)
INSERT INTO rol_permiso (rol_id, permiso_id, created_at)
SELECT r.id, p.id, NOW()
FROM roles r
CROSS JOIN permisos p
WHERE r.nombre = 'ADMIN'
  AND p.codigo IN (
    'incidentes_v2:crear','incidentes_v2:leer','incidentes_v2:actualizar',
    'sync:usar','tracking:enviar','tenants:gestionar'
  )
ON CONFLICT (rol_id, permiso_id) DO NOTHING;

-- CLIENTE: crear + leer + sync
INSERT INTO rol_permiso (rol_id, permiso_id, created_at)
SELECT r.id, p.id, NOW()
FROM roles r
JOIN permisos p ON p.codigo IN ('incidentes_v2:crear','incidentes_v2:leer','sync:usar')
WHERE r.nombre = 'CLIENTE'
ON CONFLICT (rol_id, permiso_id) DO NOTHING;

-- TALLER_RESPONSABLE: leer + actualizar
INSERT INTO rol_permiso (rol_id, permiso_id, created_at)
SELECT r.id, p.id, NOW()
FROM roles r
JOIN permisos p ON p.codigo IN ('incidentes_v2:leer','incidentes_v2:actualizar','tracking:enviar')
WHERE r.nombre = 'TALLER_RESPONSABLE'
ON CONFLICT (rol_id, permiso_id) DO NOTHING;

-- TECNICO: leer + actualizar + tracking
INSERT INTO rol_permiso (rol_id, permiso_id, created_at)
SELECT r.id, p.id, NOW()
FROM roles r
JOIN permisos p ON p.codigo IN ('incidentes_v2:leer','incidentes_v2:actualizar','tracking:enviar')
WHERE r.nombre = 'TECNICO'
ON CONFLICT (rol_id, permiso_id) DO NOTHING;

COMMIT;
