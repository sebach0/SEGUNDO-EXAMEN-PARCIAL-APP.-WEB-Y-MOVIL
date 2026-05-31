-- Idempotente: añade columna faltante alineada con ORM (SolicitudEmergencia.tecnico_asignado_at).
-- Útil si la BD se creó con 0003 anterior a esta columna. En init Docker va después de 0004.
ALTER TABLE solicitudes_emergencia
    ADD COLUMN IF NOT EXISTS tecnico_asignado_at TIMESTAMP;
