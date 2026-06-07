-- Marketplace emergencias: distancia y servicios en cotización (modelo Uber/InDrive).
-- Idempotente.

ALTER TABLE cotizaciones
    ADD COLUMN IF NOT EXISTS distancia_km NUMERIC(8, 2);

ALTER TABLE cotizaciones
    ADD COLUMN IF NOT EXISTS servicios_ofrecidos JSONB;

COMMENT ON COLUMN cotizaciones.distancia_km IS 'Distancia Haversine taller→ubicación del incidente (km).';
COMMENT ON COLUMN cotizaciones.servicios_ofrecidos IS 'Snapshot de servicios del taller al enviar la cotización.';
