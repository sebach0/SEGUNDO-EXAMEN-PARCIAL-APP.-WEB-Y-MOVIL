BEGIN;

-- =========================================================
-- FASE 3 - TECNICO
-- CU32, CU33, CU34, CU35
-- Servicios asignados, ubicación, actualización de estado y chat
-- =========================================================

-- Vistas útiles para app/panel del técnico
CREATE OR REPLACE VIEW vw_servicios_asignados_tecnico AS
SELECT
    se.id AS solicitud_id,
    se.tecnico_id,
    se.taller_id,
    se.estado,
    se.tiempo_estimado_min,
    se.created_at,
    se.updated_at,
    c.id AS cliente_id,
    u.nombres,
    u.apellidos,
    u.telefono,
    v.placa,
    mv.nombre AS marca,
    mdv.nombre AS modelo,
    tv.nombre AS tipo_vehiculo,
    su.latitud,
    su.longitud,
    su.direccion_referencia
FROM solicitudes_emergencia se
JOIN clientes c ON c.id = se.cliente_id
JOIN usuarios u ON u.id = c.usuario_id
JOIN vehiculos v ON v.id = se.vehiculo_id
LEFT JOIN marcas_vehiculo mv ON mv.id = v.marca_id
LEFT JOIN modelos_vehiculo mdv ON mdv.id = v.modelo_id
LEFT JOIN tipos_vehiculo tv ON tv.id = v.tipo_vehiculo_id
LEFT JOIN solicitud_ubicaciones su
       ON su.solicitud_id = se.id AND su.es_actual = TRUE
WHERE se.tecnico_id IS NOT NULL;

CREATE OR REPLACE VIEW vw_ubicacion_actual_cliente AS
SELECT
    su.solicitud_id,
    su.latitud,
    su.longitud,
    su.precision_metros,
    su.direccion_referencia,
    su.registrado_at
FROM solicitud_ubicaciones su
WHERE su.es_actual = TRUE;

INSERT INTO permisos (codigo, nombre, modulo, descripcion, created_at, updated_at)
VALUES
    ('cliente_ubicacion:leer', 'Consultar ubicación del cliente', 'tecnico_operacion', 'Permite al técnico consultar la ubicación actual del cliente', NOW(), NOW()),
    ('servicios_tecnico:actualizar_estado', 'Actualizar estado del servicio', 'tecnico_operacion', 'Permite al técnico actualizar el estado del servicio', NOW(), NOW()),
    ('mensajes_tecnico:crear', 'Enviar mensajes al cliente', 'tecnico_operacion', 'Permite al técnico comunicarse con el cliente', NOW(), NOW()),
    ('mensajes_tecnico:leer', 'Leer mensajes del cliente', 'tecnico_operacion', 'Permite consultar mensajes asociados a la solicitud', NOW(), NOW())
ON CONFLICT (codigo) DO NOTHING;

-- ADMIN
INSERT INTO rol_permiso (rol_id, permiso_id, created_at)
SELECT r.id, p.id, NOW()
FROM roles r
JOIN permisos p ON p.codigo IN (
    'cliente_ubicacion:leer',
    'servicios_tecnico:actualizar_estado',
    'mensajes_tecnico:crear',
    'mensajes_tecnico:leer'
)
WHERE r.nombre = 'ADMIN'
ON CONFLICT (rol_id, permiso_id) DO NOTHING;

-- TECNICO
INSERT INTO rol_permiso (rol_id, permiso_id, created_at)
SELECT r.id, p.id, NOW()
FROM roles r
JOIN permisos p ON p.codigo IN (
    'cliente_ubicacion:leer',
    'servicios_tecnico:actualizar_estado',
    'mensajes_tecnico:crear',
    'mensajes_tecnico:leer'
)
WHERE r.nombre = 'TECNICO'
ON CONFLICT (rol_id, permiso_id) DO NOTHING;

COMMIT;