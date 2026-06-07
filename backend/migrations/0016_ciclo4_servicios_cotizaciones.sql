-- =============================================================================
-- Migración 0016 — Ciclo 4 Segunda Fase
-- Servicios de taller, cotizaciones, cancelación legacy y pago con seguro
-- =============================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. CATÁLOGO DE SERVICIOS
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS servicios_catalogo (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL UNIQUE,
    descripcion VARCHAR(255),
    codigo      VARCHAR(50)  NOT NULL UNIQUE
);

-- Seed: 10 servicios base
INSERT INTO servicios_catalogo (nombre, descripcion, codigo) VALUES
    ('Chaperío y pintura',     'Reparación de carrocería, abolladuras y pintura', 'CHAPERIA'),
    ('Llantería',              'Cambio, parches, balanceo y alineación de llantas', 'LLANTERIA'),
    ('Electricidad',           'Sistema eléctrico, cableado y luces', 'ELECTRICIDAD'),
    ('Electrónica automotriz', 'Diagnóstico y reparación de sistemas electrónicos', 'ELECTRONICA'),
    ('Mecánica general',       'Motor, transmisión, frenos y suspensión', 'MECANICA_GENERAL'),
    ('Servicio de grúa',       'Remolque y traslado de vehículo', 'GRUA'),
    ('Batería y alternador',   'Carga, cambio de batería y alternador', 'BATERIA'),
    ('Reparación de motor',    'Diagnóstico y reparación mayor de motor', 'MOTOR'),
    ('Auxilio en carretera',   'Asistencia en ruta: combustible, llanta, arranque', 'AUXILIO_CARRETERA'),
    ('Otros servicios',        'Servicios adicionales no categorizados', 'OTROS')
ON CONFLICT (codigo) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. RELACIÓN TALLER ↔ SERVICIOS (N:M)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS taller_servicios (
    id          SERIAL PRIMARY KEY,
    taller_id   INTEGER NOT NULL REFERENCES talleres(id)           ON DELETE CASCADE,
    servicio_id INTEGER NOT NULL REFERENCES servicios_catalogo(id) ON DELETE CASCADE,
    UNIQUE (taller_id, servicio_id)
);

CREATE INDEX IF NOT EXISTS idx_taller_servicios_taller   ON taller_servicios(taller_id);
CREATE INDEX IF NOT EXISTS idx_taller_servicios_servicio ON taller_servicios(servicio_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- 3. COLUMNA tiene_grua EN TALLERES
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE talleres
    ADD COLUMN IF NOT EXISTS tiene_grua BOOLEAN NOT NULL DEFAULT FALSE;

-- ─────────────────────────────────────────────────────────────────────────────
-- 4. COTIZACIONES
-- ─────────────────────────────────────────────────────────────────────────────

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'estado_cotizacion') THEN
        CREATE TYPE estado_cotizacion AS ENUM (
            'ENVIADA',
            'ACEPTADA',
            'RECHAZADA',
            'EXPIRADA'
        );
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS cotizaciones (
    id                              SERIAL PRIMARY KEY,
    solicitud_id                    INTEGER       NOT NULL REFERENCES solicitudes_emergencia(id) ON DELETE RESTRICT,
    taller_id                       INTEGER       NOT NULL REFERENCES talleres(id)               ON DELETE RESTRICT,
    estado                          estado_cotizacion NOT NULL DEFAULT 'ENVIADA',
    descripcion_danio               TEXT          NOT NULL,
    detalle_servicio                TEXT          NOT NULL,
    monto_total                     NUMERIC(12,2) NOT NULL CHECK (monto_total > 0),
    tiempo_estimado_llegada_min     INTEGER,
    tiempo_estimado_reparacion_min  INTEGER,
    incluye_grua                    BOOLEAN       NOT NULL DEFAULT FALSE,
    garantia_descripcion            TEXT,
    comentarios                     TEXT,
    seleccionada_at                 TIMESTAMP,
    creado_at                       TIMESTAMP     NOT NULL DEFAULT NOW(),
    actualizado_at                  TIMESTAMP     NOT NULL DEFAULT NOW(),
    UNIQUE (solicitud_id, taller_id)
);

CREATE INDEX IF NOT EXISTS idx_cotizaciones_solicitud ON cotizaciones(solicitud_id);
CREATE INDEX IF NOT EXISTS idx_cotizaciones_taller    ON cotizaciones(taller_id, estado);

CREATE TABLE IF NOT EXISTS cotizacion_items (
    id              SERIAL PRIMARY KEY,
    cotizacion_id   INTEGER       NOT NULL REFERENCES cotizaciones(id) ON DELETE CASCADE,
    descripcion     VARCHAR(255)  NOT NULL,
    cantidad        NUMERIC(10,3) NOT NULL DEFAULT 1 CHECK (cantidad > 0),
    precio_unitario NUMERIC(12,2) NOT NULL CHECK (precio_unitario >= 0)
);

CREATE INDEX IF NOT EXISTS idx_cotizacion_items_cotizacion ON cotizacion_items(cotizacion_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- 5. CANCELACIÓN LEGACY (solicitudes_emergencia)
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE solicitudes_emergencia
    ADD COLUMN IF NOT EXISTS motivo_cancelacion TEXT,
    ADD COLUMN IF NOT EXISTS cancelado_en       TIMESTAMP;

-- ─────────────────────────────────────────────────────────────────────────────
-- 6. RESPONSABLE DE PAGO / SEGURO
-- ─────────────────────────────────────────────────────────────────────────────

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'responsable_pago') THEN
        CREATE TYPE responsable_pago AS ENUM ('CLIENTE', 'SEGURO', 'MIXTO');
    END IF;
END $$;

ALTER TABLE pagos
    ADD COLUMN IF NOT EXISTS responsable_pago responsable_pago DEFAULT 'CLIENTE',
    ADD COLUMN IF NOT EXISTS monto_seguro     NUMERIC(10,2),
    ADD COLUMN IF NOT EXISTS numero_poliza    VARCHAR(100),
    ADD COLUMN IF NOT EXISTS aseguradora      VARCHAR(150);

-- ─────────────────────────────────────────────────────────────────────────────
-- 7. PERMISOS NUEVOS
-- ─────────────────────────────────────────────────────────────────────────────

INSERT INTO permisos (codigo, nombre, descripcion, modulo)
SELECT codigo, nombre, descripcion, modulo
FROM (VALUES
    ('cotizaciones:crear',   'Proponer cotización',        'Proponer cotización para una solicitud',      'cotizaciones'),
    ('cotizaciones:leer',    'Ver cotizaciones',           'Ver cotizaciones de una solicitud',           'cotizaciones'),
    ('cotizaciones:aceptar', 'Aceptar cotización',         'Aceptar una cotización (cliente o admin)',    'cotizaciones'),
    ('servicios:gestionar',  'Gestionar servicios taller', 'Gestionar catálogo de servicios del taller',  'servicios'),
    ('kpis:leer',            'Ver KPIs operacionales',     'Ver KPIs operacionales del taller o red',     'kpis')
) AS t(codigo, nombre, descripcion, modulo)
WHERE NOT EXISTS (SELECT 1 FROM permisos p WHERE p.codigo = t.codigo);
