-- =========================================================
-- Ciclo 2 — Fase 1 (CU11–CU15)
-- Idempotente: seguro re-ejecutar en BD ya migrada.
-- Sin BEGIN/COMMIT externo (compatible con Alembic y con initdb).
-- =========================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'estado_solicitud_emergencia'
    ) THEN
        CREATE TYPE estado_solicitud_emergencia AS ENUM (
            'REGISTRADA',
            'EN_REVISION',
            'CANCELADA'
        );
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'tipo_evidencia_solicitud'
    ) THEN
        CREATE TYPE tipo_evidencia_solicitud AS ENUM (
            'FOTO',
            'AUDIO'
        );
    END IF;
END$$;

CREATE TABLE IF NOT EXISTS solicitudes_emergencia (
    id                    INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cliente_id            INTEGER NOT NULL,
    vehiculo_id           INTEGER NOT NULL,
    estado                estado_solicitud_emergencia NOT NULL DEFAULT 'REGISTRADA',
    descripcion_texto     TEXT,
    created_at            TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_solicitudes_cliente
        FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,

    CONSTRAINT fk_solicitudes_vehiculo
        FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS solicitud_ubicaciones (
    id                    INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    solicitud_id          INTEGER NOT NULL,
    latitud               NUMERIC(10,7) NOT NULL,
    longitud              NUMERIC(10,7) NOT NULL,
    precision_metros      NUMERIC(8,2),
    direccion_referencia  TEXT,
    es_actual             BOOLEAN NOT NULL DEFAULT FALSE,
    registrado_at         TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_solicitud_ubicaciones_solicitud
        FOREIGN KEY (solicitud_id) REFERENCES solicitudes_emergencia(id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_solicitud_ubicacion_actual
    ON solicitud_ubicaciones (solicitud_id)
    WHERE es_actual = TRUE;

CREATE TABLE IF NOT EXISTS solicitud_evidencias (
    id              INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    solicitud_id  INTEGER NOT NULL,
    tipo            tipo_evidencia_solicitud NOT NULL,
    archivo_url     TEXT NOT NULL,
    mime_type       VARCHAR(100),
    nombre_archivo  VARCHAR(255),
    tamano_bytes    BIGINT,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_solicitud_evidencias_solicitud
        FOREIGN KEY (solicitud_id) REFERENCES solicitudes_emergencia(id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_solicitudes_cliente_id
    ON solicitudes_emergencia(cliente_id);

CREATE INDEX IF NOT EXISTS idx_solicitudes_vehiculo_id
    ON solicitudes_emergencia(vehiculo_id);

CREATE INDEX IF NOT EXISTS idx_solicitudes_estado
    ON solicitudes_emergencia(estado);

CREATE INDEX IF NOT EXISTS idx_solicitud_ubicaciones_solicitud_id
    ON solicitud_ubicaciones(solicitud_id);

CREATE INDEX IF NOT EXISTS idx_solicitud_evidencias_solicitud_id
    ON solicitud_evidencias(solicitud_id);

CREATE INDEX IF NOT EXISTS idx_solicitud_evidencias_tipo
    ON solicitud_evidencias(tipo);

INSERT INTO permisos (codigo, nombre, modulo, descripcion, created_at, updated_at)
VALUES
    ('incidentes:crear', 'Crear solicitudes de emergencia', 'incidentes', 'Registrar emergencia vehicular', NOW(), NOW()),
    ('incidentes:leer', 'Ver solicitudes propias', 'incidentes', 'Consultar solicitudes del cliente', NOW(), NOW()),
    ('incidentes:actualizar', 'Actualizar solicitud propia (texto)', 'incidentes', 'Editar texto mientras REGISTRADA', NOW(), NOW()),
    ('ubicacion:crear', 'Enviar ubicación', 'incidentes', 'Registrar ubicación asociada a una solicitud', NOW(), NOW()),
    ('evidencias:crear', 'Adjuntar evidencias', 'incidentes', 'Subir fotos y audios', NOW(), NOW())
ON CONFLICT (codigo) DO NOTHING;

INSERT INTO rol_permiso (rol_id, permiso_id, created_at)
SELECT r.id, p.id, NOW()
FROM roles r
JOIN permisos p
  ON p.codigo IN (
    'incidentes:crear','incidentes:leer','incidentes:actualizar',
    'ubicacion:crear','evidencias:crear'
  )
WHERE r.nombre = 'ADMIN'
ON CONFLICT (rol_id, permiso_id) DO NOTHING;

INSERT INTO rol_permiso (rol_id, permiso_id, created_at)
SELECT r.id, p.id, NOW()
FROM roles r
JOIN permisos p
  ON p.codigo IN (
    'incidentes:crear','incidentes:leer','incidentes:actualizar',
    'ubicacion:crear','evidencias:crear'
  )
WHERE r.nombre = 'CLIENTE'
ON CONFLICT (rol_id, permiso_id) DO NOTHING;
