-- Última ubicación compartida por el técnico en una solicitud (cliente puede consultar vía API).
-- Permiso nuevo: tecnico_ubicacion:compartir (rol TECNICO + ADMIN).

BEGIN;

ALTER TABLE solicitudes_emergencia
    ADD COLUMN IF NOT EXISTS tecnico_ult_latitud NUMERIC(10, 7),
    ADD COLUMN IF NOT EXISTS tecnico_ult_longitud NUMERIC(10, 7),
    ADD COLUMN IF NOT EXISTS tecnico_ult_precision_metros NUMERIC(8, 2),
    ADD COLUMN IF NOT EXISTS tecnico_ult_ubicacion_at TIMESTAMP WITHOUT TIME ZONE;

INSERT INTO permisos (codigo, nombre, modulo, descripcion, created_at, updated_at)
VALUES (
    'tecnico_ubicacion:compartir',
    'Compartir ubicación del técnico en servicio',
    'tecnico_operacion',
    'Permite enviar la posición actual del técnico asociada a la solicitud',
    NOW(),
    NOW()
)
ON CONFLICT (codigo) DO NOTHING;

INSERT INTO rol_permiso (rol_id, permiso_id, created_at)
SELECT r.id, p.id, NOW()
FROM roles r
JOIN permisos p ON p.codigo = 'tecnico_ubicacion:compartir'
WHERE r.nombre IN ('ADMIN', 'TECNICO')
ON CONFLICT (rol_id, permiso_id) DO NOTHING;

COMMIT;
