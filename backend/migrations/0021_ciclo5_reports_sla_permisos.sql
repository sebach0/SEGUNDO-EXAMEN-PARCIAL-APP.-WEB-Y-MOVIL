-- Ciclo 5 Etapa 1B — permisos reportes y SLA

INSERT INTO permisos (codigo, nombre, descripcion, modulo, created_at, updated_at)
VALUES
    (
        'reports:leer',
        'Consultar reportes operativos',
        'Ver reportes de incidentes, rendimiento y cancelaciones',
        'reports',
        NOW(),
        NOW()
    ),
    (
        'reports:exportar',
        'Exportar reportes',
        'Exportar reportes operativos en CSV',
        'reports',
        NOW(),
        NOW()
    ),
    (
        'sla:leer',
        'Consultar cumplimiento SLA',
        'Ver cumplimiento SLA por taller',
        'sla',
        NOW(),
        NOW()
    )
ON CONFLICT (codigo) DO UPDATE SET
    nombre      = EXCLUDED.nombre,
    descripcion = EXCLUDED.descripcion,
    modulo      = EXCLUDED.modulo,
    updated_at  = NOW();

INSERT INTO rol_permiso (rol_id, permiso_id, created_at)
SELECT r.id, p.id, NOW()
FROM roles r
CROSS JOIN permisos p
WHERE r.nombre = 'ADMIN'
  AND p.codigo IN ('reports:leer', 'reports:exportar', 'sla:leer')
ON CONFLICT DO NOTHING;
