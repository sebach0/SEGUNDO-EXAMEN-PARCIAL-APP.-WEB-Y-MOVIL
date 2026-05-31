-- IA modular: permiso inferencia, payload JSON en solicitud, coordenadas taller (scoring distancia).
-- Idempotente (ON CONFLICT / IF NOT EXISTS).

INSERT INTO permisos (codigo, nombre, modulo, descripcion, created_at, updated_at)
VALUES
    (
        'ai:inferir',
        'Usar servicios de inferencia IA',
        'ia',
        'Transcripción de audio, análisis de imagen y endpoints de apoyo IA',
        NOW(),
        NOW()
    )
ON CONFLICT (codigo) DO NOTHING;

INSERT INTO rol_permiso (rol_id, permiso_id, created_at)
SELECT r.id, p.id, NOW()
FROM roles r
JOIN permisos p ON p.codigo = 'ai:inferir'
WHERE r.nombre IN ('ADMIN', 'CLIENTE', 'TALLER_RESPONSABLE')
ON CONFLICT (rol_id, permiso_id) DO NOTHING;

ALTER TABLE solicitudes_emergencia
    ADD COLUMN IF NOT EXISTS ai_payload JSONB;

ALTER TABLE talleres
    ADD COLUMN IF NOT EXISTS latitud NUMERIC(10, 7),
    ADD COLUMN IF NOT EXISTS longitud NUMERIC(10, 7);

COMMENT ON COLUMN solicitudes_emergencia.ai_payload IS 'Resultado agregado de pipeline IA (clasificación, prioridad, ficha, sugerencias).';
