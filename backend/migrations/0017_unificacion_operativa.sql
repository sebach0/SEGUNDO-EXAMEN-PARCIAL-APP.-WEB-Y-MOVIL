-- =============================================================================
-- 0017 — Unificación operativa: timestamps KPI, tenant, SLA, cancelación, offline
-- Extiende solicitudes_emergencia (flujo real) sin romper Ciclo 1-3.
-- =============================================================================

BEGIN;

-- ── tenant_id en talleres ─────────────────────────────────────────────────────
ALTER TABLE talleres
    ADD COLUMN IF NOT EXISTS tenant_id INTEGER
    REFERENCES tenants(id) ON UPDATE CASCADE ON DELETE SET NULL;

UPDATE talleres t
SET tenant_id = u.tenant_id
FROM usuarios u
WHERE u.id = t.usuario_responsable_id
  AND t.tenant_id IS NULL;

UPDATE talleres
SET tenant_id = (SELECT id FROM tenants WHERE slug = 'principal' LIMIT 1)
WHERE tenant_id IS NULL;

CREATE INDEX IF NOT EXISTS idx_talleres_tenant_id ON talleres(tenant_id);

-- ── solicitudes_emergencia: campos operativos ─────────────────────────────────
ALTER TABLE solicitudes_emergencia
    ADD COLUMN IF NOT EXISTS tenant_id INTEGER
        REFERENCES tenants(id) ON UPDATE CASCADE ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS reportado_en TIMESTAMP,
    ADD COLUMN IF NOT EXISTS asignado_en TIMESTAMP,
    ADD COLUMN IF NOT EXISTS en_camino_en TIMESTAMP,
    ADD COLUMN IF NOT EXISTS en_atencion_en TIMESTAMP,
    ADD COLUMN IF NOT EXISTS llegada_real_en TIMESTAMP,
    ADD COLUMN IF NOT EXISTS sla_minutos INTEGER NOT NULL DEFAULT 60,
    ADD COLUMN IF NOT EXISTS cancelado_por_usuario_id INTEGER
        REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS cancelacion_fase VARCHAR(30),
    ADD COLUMN IF NOT EXISTS taller_habia_llegado BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS eta_actualizado_en TIMESTAMP,
    ADD COLUMN IF NOT EXISTS eta_origen VARCHAR(20),
    ADD COLUMN IF NOT EXISTS retraso_notificado_en TIMESTAMP,
    ADD COLUMN IF NOT EXISTS client_uuid UUID,
    ADD COLUMN IF NOT EXISTS sync_estado VARCHAR(20) NOT NULL DEFAULT 'SINCRONIZADO',
    ADD COLUMN IF NOT EXISTS zona_id INTEGER
        REFERENCES zonas(id) ON UPDATE CASCADE ON DELETE SET NULL;

-- Retrocompatibilidad: reportado_en = created_at
UPDATE solicitudes_emergencia
SET reportado_en = created_at
WHERE reportado_en IS NULL;

-- tenant desde cliente → usuario
UPDATE solicitudes_emergencia se
SET tenant_id = u.tenant_id
FROM clientes c
JOIN usuarios u ON u.id = c.usuario_id
WHERE se.cliente_id = c.id
  AND se.tenant_id IS NULL;

UPDATE solicitudes_emergencia
SET tenant_id = (SELECT id FROM tenants WHERE slug = 'principal' LIMIT 1)
WHERE tenant_id IS NULL;

-- Timestamps desde historial de estados
UPDATE solicitudes_emergencia se
SET asignado_en = sub.ts
FROM (
    SELECT solicitud_id, MIN(created_at) AS ts
    FROM solicitud_historial_estado
    WHERE estado_nuevo IN ('TALLER_ASIGNADO', 'TECNICO_ASIGNADO')
    GROUP BY solicitud_id
) sub
WHERE se.id = sub.solicitud_id
  AND se.asignado_en IS NULL;

UPDATE solicitudes_emergencia se
SET en_camino_en = sub.ts
FROM (
    SELECT solicitud_id, MIN(created_at) AS ts
    FROM solicitud_historial_estado
    WHERE estado_nuevo = 'EN_CAMINO'
    GROUP BY solicitud_id
) sub
WHERE se.id = sub.solicitud_id
  AND se.en_camino_en IS NULL;

UPDATE solicitudes_emergencia se
SET en_atencion_en = sub.ts,
    llegada_real_en = sub.ts
FROM (
    SELECT solicitud_id, MIN(created_at) AS ts
    FROM solicitud_historial_estado
    WHERE estado_nuevo = 'EN_ATENCION'
    GROUP BY solicitud_id
) sub
WHERE se.id = sub.solicitud_id
  AND se.en_atencion_en IS NULL;

-- Índices
CREATE INDEX IF NOT EXISTS idx_solicitudes_tenant_id ON solicitudes_emergencia(tenant_id);
CREATE INDEX IF NOT EXISTS idx_solicitudes_reportado_en ON solicitudes_emergencia(reportado_en);
CREATE INDEX IF NOT EXISTS idx_solicitudes_zona_id ON solicitudes_emergencia(zona_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_solicitudes_tenant_client_uuid
    ON solicitudes_emergencia(tenant_id, client_uuid)
    WHERE client_uuid IS NOT NULL;

COMMIT;
