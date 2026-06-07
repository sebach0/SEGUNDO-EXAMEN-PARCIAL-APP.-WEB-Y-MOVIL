-- Ciclo 5 Etapa 1D-E — tenant_id en cotizaciones/pagos + cotizacion_id en pagos

ALTER TABLE cotizaciones
    ADD COLUMN IF NOT EXISTS tenant_id INTEGER REFERENCES tenants(id) ON DELETE SET NULL;

UPDATE cotizaciones c
SET tenant_id = s.tenant_id
FROM solicitudes_emergencia s
WHERE c.solicitud_id = s.id AND c.tenant_id IS NULL;

UPDATE cotizaciones SET tenant_id = 1 WHERE tenant_id IS NULL;

CREATE INDEX IF NOT EXISTS idx_cotizaciones_tenant ON cotizaciones(tenant_id);

ALTER TABLE cotizacion_items
    ADD COLUMN IF NOT EXISTS tenant_id INTEGER REFERENCES tenants(id) ON DELETE SET NULL;

UPDATE cotizacion_items ci
SET tenant_id = c.tenant_id
FROM cotizaciones c
WHERE ci.cotizacion_id = c.id AND ci.tenant_id IS NULL;

UPDATE cotizacion_items SET tenant_id = 1 WHERE tenant_id IS NULL;

ALTER TABLE pagos
    ADD COLUMN IF NOT EXISTS tenant_id INTEGER REFERENCES tenants(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS cotizacion_id INTEGER REFERENCES cotizaciones(id) ON DELETE SET NULL;

UPDATE pagos p
SET tenant_id = s.tenant_id
FROM solicitudes_emergencia s
WHERE p.solicitud_id = s.id AND p.tenant_id IS NULL;

UPDATE pagos SET tenant_id = 1 WHERE tenant_id IS NULL;

UPDATE pagos p
SET cotizacion_id = c.id
FROM cotizaciones c
WHERE c.solicitud_id = p.solicitud_id
  AND c.estado = 'ACEPTADA'
  AND p.cotizacion_id IS NULL;

CREATE INDEX IF NOT EXISTS idx_pagos_tenant ON pagos(tenant_id);
CREATE INDEX IF NOT EXISTS idx_pagos_cotizacion ON pagos(cotizacion_id);

-- Permisos Ciclo 5
INSERT INTO permisos (codigo, nombre, descripcion, modulo, created_at, updated_at)
VALUES
    (
        'cotizaciones:rechazar',
        'Rechazar cotización',
        'Rechazar una cotización enviada por un taller',
        'cotizaciones',
        NOW(),
        NOW()
    ),
    (
        'pagos:admin',
        'Administrar pagos',
        'Listar y validar pagos manuales (admin)',
        'pagos',
        NOW(),
        NOW()
    )
ON CONFLICT (codigo) DO UPDATE SET
    nombre = EXCLUDED.nombre,
    descripcion = EXCLUDED.descripcion,
    modulo = EXCLUDED.modulo,
    updated_at = NOW();

INSERT INTO rol_permiso (rol_id, permiso_id, created_at)
SELECT r.id, p.id, NOW()
FROM roles r
CROSS JOIN permisos p
WHERE r.nombre = 'ADMIN'
  AND p.codigo IN ('cotizaciones:rechazar', 'pagos:admin')
ON CONFLICT DO NOTHING;

INSERT INTO rol_permiso (rol_id, permiso_id, created_at)
SELECT r.id, p.id, NOW()
FROM roles r
JOIN permisos p ON p.codigo = 'cotizaciones:rechazar'
WHERE r.nombre = 'CLIENTE'
ON CONFLICT DO NOTHING;
