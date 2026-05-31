-- =========================================================
-- Permisos portal taller / técnico (antes solo en scripts/*.sql).
-- Sin esto, TALLER_RESPONSABLE no recibe códigos en /auth/me y el
-- sidebar Angular oculta Solicitudes / Disponibilidad.
-- Idempotente: ON CONFLICT DO NOTHING.
-- =========================================================

BEGIN;

INSERT INTO permisos (codigo, nombre, modulo, descripcion, created_at, updated_at)
VALUES
    ('solicitudes_taller:leer', 'Ver solicitudes disponibles para taller', 'taller_operacion', 'Permite revisar información estructurada del incidente', NOW(), NOW()),
    ('solicitudes_taller:aceptar', 'Aceptar solicitud de asistencia', 'taller_operacion', 'Permite aceptar una solicitud desde la bandeja del taller', NOW(), NOW()),
    ('solicitudes_taller:rechazar', 'Rechazar solicitud de asistencia', 'taller_operacion', 'Permite rechazar una solicitud desde la bandeja del taller', NOW(), NOW()),
    ('disponibilidad:gestionar', 'Gestionar disponibilidad del taller', 'taller_operacion', 'Permite administrar disponibilidad y capacidad del taller', NOW(), NOW()),
    ('tecnicos:asignar', 'Asignar técnico a solicitud', 'taller_operacion', 'Permite asignar un técnico a una atención', NOW(), NOW()),
    ('servicios_tecnico:leer', 'Ver servicios asignados al técnico', 'tecnico_operacion', 'Permite consultar servicios asignados', NOW(), NOW()),
    ('cliente_ubicacion:leer', 'Consultar ubicación del cliente', 'tecnico_operacion', 'Permite al técnico consultar la ubicación actual del cliente', NOW(), NOW()),
    ('servicios_tecnico:actualizar_estado', 'Actualizar estado del servicio', 'tecnico_operacion', 'Permite al técnico actualizar el estado del servicio', NOW(), NOW()),
    ('mensajes_tecnico:crear', 'Enviar mensajes al cliente', 'tecnico_operacion', 'Permite al técnico comunicarse con el cliente', NOW(), NOW()),
    ('mensajes_tecnico:leer', 'Leer mensajes del cliente', 'tecnico_operacion', 'Permite consultar mensajes asociados a la solicitud', NOW(), NOW()),
    ('historial_atenciones:leer', 'Ver historial de atenciones', 'taller_control', 'Permite consultar el historial de servicios del taller', NOW(), NOW()),
    ('comisiones:leer', 'Consultar comisiones', 'taller_control', 'Permite consultar comisiones del taller', NOW(), NOW())
ON CONFLICT (codigo) DO NOTHING;

-- ADMIN: todos los códigos nuevos
INSERT INTO rol_permiso (rol_id, permiso_id, created_at)
SELECT r.id, p.id, NOW()
FROM roles r
JOIN permisos p ON p.codigo IN (
    'solicitudes_taller:leer',
    'solicitudes_taller:aceptar',
    'solicitudes_taller:rechazar',
    'disponibilidad:gestionar',
    'tecnicos:asignar',
    'servicios_tecnico:leer',
    'cliente_ubicacion:leer',
    'servicios_tecnico:actualizar_estado',
    'mensajes_tecnico:crear',
    'mensajes_tecnico:leer',
    'historial_atenciones:leer',
    'comisiones:leer'
)
WHERE r.nombre = 'ADMIN'
ON CONFLICT (rol_id, permiso_id) DO NOTHING;

-- TALLER_RESPONSABLE
INSERT INTO rol_permiso (rol_id, permiso_id, created_at)
SELECT r.id, p.id, NOW()
FROM roles r
JOIN permisos p ON p.codigo IN (
    'solicitudes_taller:leer',
    'solicitudes_taller:aceptar',
    'solicitudes_taller:rechazar',
    'disponibilidad:gestionar',
    'tecnicos:asignar',
    'historial_atenciones:leer',
    'comisiones:leer'
)
WHERE r.nombre = 'TALLER_RESPONSABLE'
ON CONFLICT (rol_id, permiso_id) DO NOTHING;

-- TECNICO
INSERT INTO rol_permiso (rol_id, permiso_id, created_at)
SELECT r.id, p.id, NOW()
FROM roles r
JOIN permisos p ON p.codigo IN (
    'servicios_tecnico:leer',
    'cliente_ubicacion:leer',
    'servicios_tecnico:actualizar_estado',
    'mensajes_tecnico:crear',
    'mensajes_tecnico:leer'
)
WHERE r.nombre = 'TECNICO'
ON CONFLICT (rol_id, permiso_id) DO NOTHING;

COMMIT;
