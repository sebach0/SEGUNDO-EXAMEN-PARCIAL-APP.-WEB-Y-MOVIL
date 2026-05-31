BEGIN;

-- =========================================================
-- FASE 4 - TALLER
-- CU30, CU31
-- Historial de atenciones y comisiones
-- =========================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'estado_comision_taller'
    ) THEN
        CREATE TYPE estado_comision_taller AS ENUM (
            'PENDIENTE',
            'CALCULADA',
            'LIQUIDADA',
            'ANULADA'
        );
    END IF;
END$$;

CREATE TABLE IF NOT EXISTS comisiones_taller (
    id                      INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    solicitud_id            INTEGER NOT NULL UNIQUE,
    taller_id               INTEGER NOT NULL,
    pago_id                 INTEGER UNIQUE,
    porcentaje_plataforma   NUMERIC(5,2) NOT NULL DEFAULT 10.00,
    monto_servicio          NUMERIC(10,2) NOT NULL,
    monto_comision          NUMERIC(10,2) NOT NULL,
    monto_taller_neto       NUMERIC(10,2) NOT NULL,
    estado                  estado_comision_taller NOT NULL DEFAULT 'PENDIENTE',
    calculado_at            TIMESTAMP NOT NULL DEFAULT NOW(),
    liquidado_at            TIMESTAMP,

    CONSTRAINT fk_comision_solicitud
        FOREIGN KEY (solicitud_id) REFERENCES solicitudes_emergencia(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,

    CONSTRAINT fk_comision_taller
        FOREIGN KEY (taller_id) REFERENCES talleres(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,

    CONSTRAINT fk_comision_pago
        FOREIGN KEY (pago_id) REFERENCES pagos(id)
        ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_comision_taller_id
    ON comisiones_taller(taller_id);

CREATE INDEX IF NOT EXISTS idx_comision_estado
    ON comisiones_taller(estado);

CREATE OR REPLACE VIEW vw_historial_atenciones_taller AS
SELECT
    se.id AS solicitud_id,
    se.taller_id,
    se.tecnico_id,
    se.estado,
    se.created_at,
    se.finalizada_at,
    u.nombres,
    u.apellidos,
    v.placa,
    mv.nombre AS marca,
    mdv.nombre AS modelo,
    tv.nombre AS tipo_vehiculo
FROM solicitudes_emergencia se
JOIN clientes c ON c.id = se.cliente_id
JOIN usuarios u ON u.id = c.usuario_id
JOIN vehiculos v ON v.id = se.vehiculo_id
LEFT JOIN marcas_vehiculo mv ON mv.id = v.marca_id
LEFT JOIN modelos_vehiculo mdv ON mdv.id = v.modelo_id
LEFT JOIN tipos_vehiculo tv ON tv.id = v.tipo_vehiculo_id
WHERE se.taller_id IS NOT NULL;

CREATE OR REPLACE VIEW vw_resumen_comisiones_taller AS
SELECT
    ct.taller_id,
    COUNT(ct.id) AS total_registros,
    COALESCE(SUM(ct.monto_servicio), 0) AS total_servicios,
    COALESCE(SUM(ct.monto_comision), 0) AS total_comision,
    COALESCE(SUM(ct.monto_taller_neto), 0) AS total_neto
FROM comisiones_taller ct
GROUP BY ct.taller_id;

INSERT INTO permisos (codigo, nombre, modulo, descripcion, created_at, updated_at)
VALUES
    ('historial_atenciones:leer', 'Ver historial de atenciones', 'taller_control', 'Permite consultar el historial de servicios del taller', NOW(), NOW()),
    ('comisiones:leer', 'Consultar comisiones', 'taller_control', 'Permite consultar comisiones del taller', NOW(), NOW())
ON CONFLICT (codigo) DO NOTHING;

-- ADMIN
INSERT INTO rol_permiso (rol_id, permiso_id, created_at)
SELECT r.id, p.id, NOW()
FROM roles r
JOIN permisos p ON p.codigo IN ('historial_atenciones:leer','comisiones:leer')
WHERE r.nombre = 'ADMIN'
ON CONFLICT (rol_id, permiso_id) DO NOTHING;

-- TALLER_RESPONSABLE
INSERT INTO rol_permiso (rol_id, permiso_id, created_at)
SELECT r.id, p.id, NOW()
FROM roles r
JOIN permisos p ON p.codigo IN ('historial_atenciones:leer','comisiones:leer')
WHERE r.nombre = 'TALLER_RESPONSABLE'
ON CONFLICT (rol_id, permiso_id) DO NOTHING;

COMMIT;