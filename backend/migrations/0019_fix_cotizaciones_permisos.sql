-- Fix permisos Ciclo 4: codigo debe ser module:accion (require_permission usa Permiso.codigo).
-- La migración 0016 insertó codigo/nombre invertidos (p. ej. codigo=cotizaciones_crear).
-- Idempotente.

UPDATE permisos
SET codigo = 'cotizaciones:crear',
    nombre = 'Proponer cotización',
    descripcion = 'Proponer cotización para una solicitud'
WHERE codigo = 'cotizaciones_crear';

UPDATE permisos
SET codigo = 'cotizaciones:leer',
    nombre = 'Ver cotizaciones',
    descripcion = 'Ver cotizaciones de una solicitud'
WHERE codigo = 'cotizaciones_leer';

UPDATE permisos
SET codigo = 'cotizaciones:aceptar',
    nombre = 'Aceptar cotización',
    descripcion = 'Aceptar una cotización (cliente o admin)'
WHERE codigo = 'cotizaciones_aceptar';

UPDATE permisos
SET codigo = 'servicios:gestionar',
    nombre = 'Gestionar servicios del taller',
    descripcion = 'Gestionar catálogo de servicios del taller'
WHERE codigo = 'servicios_gestionar';

UPDATE permisos
SET codigo = 'kpis:leer',
    nombre = 'Ver KPIs operacionales',
    descripcion = 'Ver KPIs operacionales del taller o red'
WHERE codigo = 'kpis_leer';

-- Taller responsable: marketplace (cotizar + ver propias)
INSERT INTO rol_permiso (rol_id, permiso_id, created_at)
SELECT r.id, p.id, NOW()
FROM roles r
JOIN permisos p ON p.codigo IN (
    'cotizaciones:crear',
    'cotizaciones:leer',
    'servicios:gestionar'
)
WHERE r.nombre = 'TALLER_RESPONSABLE'
ON CONFLICT (rol_id, permiso_id) DO NOTHING;

-- Cliente: comparar y seleccionar cotización
INSERT INTO rol_permiso (rol_id, permiso_id, created_at)
SELECT r.id, p.id, NOW()
FROM roles r
JOIN permisos p ON p.codigo IN ('cotizaciones:leer', 'cotizaciones:aceptar')
WHERE r.nombre = 'CLIENTE'
ON CONFLICT (rol_id, permiso_id) DO NOTHING;

-- Admin KPIs (si no lo tenía)
INSERT INTO rol_permiso (rol_id, permiso_id, created_at)
SELECT r.id, p.id, NOW()
FROM roles r
JOIN permisos p ON p.codigo = 'kpis:leer'
WHERE r.nombre = 'ADMIN'
ON CONFLICT (rol_id, permiso_id) DO NOTHING;
