-- Backup admin panel — permiso
INSERT INTO permisos (codigo, nombre, descripcion, modulo, created_at, updated_at)
VALUES (
    'admin:backup',
    'Descargar backup del sistema',
    'Descarga un archivo ZIP con todas las tablas principales del sistema',
    'admin',
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
  AND p.codigo = 'admin:backup'
ON CONFLICT DO NOTHING;
