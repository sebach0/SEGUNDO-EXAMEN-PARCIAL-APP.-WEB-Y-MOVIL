BEGIN;

-- =========================================================
-- Asignación técnico (scripts/007 DDL sin permisos ni ALTER duplicado).
-- Columna tecnico_asignado_at: 0006_tecnico_asignado_at.sql
-- =========================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'estado_asignacion_tecnico'
    ) THEN
        CREATE TYPE estado_asignacion_tecnico AS ENUM (
            'ASIGNADO',
            'REASIGNADO',
            'CANCELADO'
        );
    END IF;
END$$;

CREATE TABLE IF NOT EXISTS solicitud_asignaciones_tecnico (
    id                      INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    solicitud_id            INTEGER NOT NULL,
    taller_id               INTEGER NOT NULL,
    tecnico_id              INTEGER NOT NULL,
    estado                  estado_asignacion_tecnico NOT NULL DEFAULT 'ASIGNADO',
    asignado_por_usuario_id INTEGER,
    observacion             TEXT,
    created_at              TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_asignacion_solicitud
        FOREIGN KEY (solicitud_id) REFERENCES solicitudes_emergencia(id)
        ON UPDATE CASCADE ON DELETE CASCADE,

    CONSTRAINT fk_asignacion_taller
        FOREIGN KEY (taller_id) REFERENCES talleres(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,

    CONSTRAINT fk_asignacion_tecnico
        FOREIGN KEY (tecnico_id) REFERENCES tecnicos(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,

    CONSTRAINT fk_asignacion_usuario
        FOREIGN KEY (asignado_por_usuario_id) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_asignacion_solicitud_id
    ON solicitud_asignaciones_tecnico(solicitud_id);

CREATE INDEX IF NOT EXISTS idx_asignacion_taller_id
    ON solicitud_asignaciones_tecnico(taller_id);

CREATE INDEX IF NOT EXISTS idx_asignacion_tecnico_id
    ON solicitud_asignaciones_tecnico(tecnico_id);

COMMIT;
