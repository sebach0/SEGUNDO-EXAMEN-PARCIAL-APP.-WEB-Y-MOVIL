-- Presupuesto en bolivianos (BOB) al llegar / iniciar atención en sitio (técnico → cliente).
ALTER TABLE solicitudes_emergencia
  ADD COLUMN IF NOT EXISTS presupuesto_bob NUMERIC(12, 2) NULL,
  ADD COLUMN IF NOT EXISTS presupuesto_registrado_at TIMESTAMP WITHOUT TIME ZONE NULL;

COMMENT ON COLUMN solicitudes_emergencia.presupuesto_bob IS 'Monto cotizado por el técnico al iniciar atención en sitio (BOB).';
COMMENT ON COLUMN solicitudes_emergencia.presupuesto_registrado_at IS 'Momento en que se registró el presupuesto.';
