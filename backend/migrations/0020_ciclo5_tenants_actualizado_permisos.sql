-- Ciclo 5 Etapa 1A — tenants.actualizado_en + permiso tenants:asignar
-- Idempotente (IF NOT EXISTS / ON CONFLICT).

ALTER TABLE tenants
    ADD COLUMN IF NOT EXISTS actualizado_en TIMESTAMPTZ;

UPDATE tenants
SET actualizado_en = creado_en
WHERE actualizado_en IS NULL;

ALTER TABLE tenants
    ALTER COLUMN actualizado_en SET DEFAULT now();

-- Permiso CU44 — asignar usuarios/talleres/técnicos a tenant
INSERT INTO permisos (codigo, nombre, descripcion, modulo, created_at, updated_at)
VALUES (
    'tenants:asignar',
    'Asignar miembros a tenant',
    'Vincular usuarios, talleres y técnicos a una organización tenant',
    'tenants',
    NOW(),
    NOW()
)
ON CONFLICT (codigo) DO UPDATE SET
    nombre      = EXCLUDED.nombre,
    descripcion = EXCLUDED.descripcion,
    modulo      = EXCLUDED.modulo,
    updated_at  = NOW();

-- ADMIN recibe tenants:asignar
INSERT INTO rol_permiso (rol_id, permiso_id, created_at)
SELECT r.id, p.id, NOW()
FROM roles r
CROSS JOIN permisos p
WHERE r.nombre = 'ADMIN'
  AND p.codigo = 'tenants:asignar'
ON CONFLICT DO NOTHING;
