BEGIN;

-- =========================================================
-- DDL bandeja + disponibilidad taller (scripts/006 sin permisos).
-- Los permisos viven en 0007_taller_operacion_permisos.sql.
-- =========================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'estado_bandeja_taller'
    ) THEN
        CREATE TYPE estado_bandeja_taller AS ENUM (
            'PENDIENTE',
            'ACEPTADA',
            'RECHAZADA',
            'EXPIRADA'
        );
    END IF;
END$$;

CREATE TABLE IF NOT EXISTS taller_disponibilidad (
    id                          INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    taller_id                   INTEGER NOT NULL UNIQUE,
    acepta_nuevas_solicitudes   BOOLEAN NOT NULL DEFAULT TRUE,
    capacidad_maxima_diaria     INTEGER NOT NULL DEFAULT 10,
    servicios_activos           INTEGER NOT NULL DEFAULT 0,
    observacion                 TEXT,
    updated_by_usuario_id       INTEGER,
    updated_at                  TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_taller_disponibilidad_taller
        FOREIGN KEY (taller_id) REFERENCES talleres(id)
        ON UPDATE CASCADE ON DELETE CASCADE,

    CONSTRAINT fk_taller_disponibilidad_usuario
        FOREIGN KEY (updated_by_usuario_id) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS solicitud_taller_bandeja (
    id                  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    solicitud_id        INTEGER NOT NULL,
    taller_id           INTEGER NOT NULL,
    estado              estado_bandeja_taller NOT NULL DEFAULT 'PENDIENTE',
    motivo_rechazo      TEXT,
    creado_at           TIMESTAMP NOT NULL DEFAULT NOW(),
    respondido_at       TIMESTAMP,

    CONSTRAINT uq_solicitud_taller_bandeja UNIQUE (solicitud_id, taller_id),

    CONSTRAINT fk_bandeja_solicitud
        FOREIGN KEY (solicitud_id) REFERENCES solicitudes_emergencia(id)
        ON UPDATE CASCADE ON DELETE CASCADE,

    CONSTRAINT fk_bandeja_taller
        FOREIGN KEY (taller_id) REFERENCES talleres(id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_taller_disponibilidad_taller_id
    ON taller_disponibilidad(taller_id);

CREATE INDEX IF NOT EXISTS idx_bandeja_taller_id
    ON solicitud_taller_bandeja(taller_id);

CREATE INDEX IF NOT EXISTS idx_bandeja_solicitud_id
    ON solicitud_taller_bandeja(solicitud_id);

CREATE INDEX IF NOT EXISTS idx_bandeja_estado
    ON solicitud_taller_bandeja(estado);

CREATE OR REPLACE VIEW vw_solicitudes_disponibles_taller AS
SELECT
    stb.id AS bandeja_id,
    stb.taller_id,
    se.id AS solicitud_id,
    se.estado AS estado_solicitud,
    se.descripcion_texto,
    se.created_at,
    se.vehiculo_id,
    v.placa,
    mv.nombre AS marca,
    mdv.nombre AS modelo,
    tv.nombre AS tipo_vehiculo,
    c.id AS cliente_id,
    u.nombres,
    u.apellidos,
    su.latitud,
    su.longitud,
    su.direccion_referencia
FROM solicitud_taller_bandeja stb
JOIN solicitudes_emergencia se ON se.id = stb.solicitud_id
JOIN vehiculos v ON v.id = se.vehiculo_id
JOIN clientes c ON c.id = se.cliente_id
JOIN usuarios u ON u.id = c.usuario_id
LEFT JOIN marcas_vehiculo mv ON mv.id = v.marca_id
LEFT JOIN modelos_vehiculo mdv ON mdv.id = v.modelo_id
LEFT JOIN tipos_vehiculo tv ON tv.id = v.tipo_vehiculo_id
LEFT JOIN solicitud_ubicaciones su
       ON su.solicitud_id = se.id AND su.es_actual = TRUE
WHERE stb.estado = 'PENDIENTE';

COMMIT;
