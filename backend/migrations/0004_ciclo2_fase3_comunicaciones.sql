-- =========================================================
-- Ciclo 2 — Fase 3 (CU19, CU21): notificaciones in-app + push (FCM) + mensajes por solicitud.
-- Idempotente. Requiere fase 1–2 (solicitudes_emergencia, usuarios, permisos).
-- =========================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'tipo_notificacion'
    ) THEN
        CREATE TYPE tipo_notificacion AS ENUM (
            'SOLICITUD_CREADA',
            'ESTADO_ACTUALIZADO',
            'TALLER_ASIGNADO',
            'TECNICO_ASIGNADO',
            'MENSAJE_NUEVO'
        );
    END IF;
END$$;

CREATE TABLE IF NOT EXISTS notificaciones (
    id              INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    usuario_id      INTEGER NOT NULL,
    solicitud_id    INTEGER,
    tipo            tipo_notificacion NOT NULL,
    titulo          VARCHAR(150) NOT NULL,
    mensaje         TEXT NOT NULL,
    leida           BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    leida_at        TIMESTAMP,

    CONSTRAINT fk_notificaciones_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE CASCADE,

    CONSTRAINT fk_notificaciones_solicitud
        FOREIGN KEY (solicitud_id) REFERENCES solicitudes_emergencia(id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS solicitud_mensajes (
    id                  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    solicitud_id        INTEGER NOT NULL,
    emisor_usuario_id   INTEGER NOT NULL,
    receptor_usuario_id INTEGER NOT NULL,
    mensaje             TEXT NOT NULL,
    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    leido_at            TIMESTAMP,

    CONSTRAINT fk_mensajes_solicitud
        FOREIGN KEY (solicitud_id) REFERENCES solicitudes_emergencia(id)
        ON UPDATE CASCADE ON DELETE CASCADE,

    CONSTRAINT fk_mensajes_emisor
        FOREIGN KEY (emisor_usuario_id) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,

    CONSTRAINT fk_mensajes_receptor
        FOREIGN KEY (receptor_usuario_id) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- Tokens FCM por usuario (CU19 — envío push desde backend).
CREATE TABLE IF NOT EXISTS usuario_fcm_tokens (
    id          INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    usuario_id  INTEGER NOT NULL,
    token       TEXT NOT NULL,
    platform    VARCHAR(20),
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_fcm_tokens_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT uq_usuario_fcm_token UNIQUE (token)
);

CREATE INDEX IF NOT EXISTS idx_notificaciones_usuario_id
    ON notificaciones(usuario_id);

CREATE INDEX IF NOT EXISTS idx_notificaciones_solicitud_id
    ON notificaciones(solicitud_id);

CREATE INDEX IF NOT EXISTS idx_notificaciones_leida
    ON notificaciones(leida);

CREATE INDEX IF NOT EXISTS idx_mensajes_solicitud_id
    ON solicitud_mensajes(solicitud_id);

CREATE INDEX IF NOT EXISTS idx_mensajes_emisor_usuario_id
    ON solicitud_mensajes(emisor_usuario_id);

CREATE INDEX IF NOT EXISTS idx_mensajes_receptor_usuario_id
    ON solicitud_mensajes(receptor_usuario_id);

CREATE INDEX IF NOT EXISTS idx_usuario_fcm_tokens_usuario_id
    ON usuario_fcm_tokens(usuario_id);

INSERT INTO permisos (codigo, nombre, modulo, descripcion, created_at, updated_at)
VALUES
    ('notificaciones:leer', 'Ver notificaciones', 'notificaciones', 'Consultar notificaciones del sistema', NOW(), NOW()),
    ('mensajes:crear', 'Enviar mensajes', 'comunicacion', 'Enviar mensajes asociados a una solicitud', NOW(), NOW()),
    ('mensajes:leer', 'Ver mensajes', 'comunicacion', 'Consultar mensajes de una solicitud', NOW(), NOW()),
    ('dispositivos:fcm', 'Registrar token FCM', 'notificaciones', 'Asociar dispositivo para push', NOW(), NOW())
ON CONFLICT (codigo) DO NOTHING;

INSERT INTO rol_permiso (rol_id, permiso_id, created_at)
SELECT r.id, p.id, NOW()
FROM roles r
JOIN permisos p
  ON p.codigo IN ('notificaciones:leer','mensajes:crear','mensajes:leer','dispositivos:fcm')
WHERE r.nombre = 'ADMIN'
ON CONFLICT (rol_id, permiso_id) DO NOTHING;

INSERT INTO rol_permiso (rol_id, permiso_id, created_at)
SELECT r.id, p.id, NOW()
FROM roles r
JOIN permisos p
  ON p.codigo IN ('notificaciones:leer','mensajes:crear','mensajes:leer','dispositivos:fcm')
WHERE r.nombre = 'CLIENTE'
ON CONFLICT (rol_id, permiso_id) DO NOTHING;

INSERT INTO rol_permiso (rol_id, permiso_id, created_at)
SELECT r.id, p.id, NOW()
FROM roles r
JOIN permisos p
  ON p.codigo IN ('notificaciones:leer','mensajes:crear','mensajes:leer','dispositivos:fcm')
WHERE r.nombre = 'TECNICO'
ON CONFLICT (rol_id, permiso_id) DO NOTHING;

INSERT INTO rol_permiso (rol_id, permiso_id, created_at)
SELECT r.id, p.id, NOW()
FROM roles r
JOIN permisos p
  ON p.codigo IN ('notificaciones:leer')
WHERE r.nombre = 'TALLER_RESPONSABLE'
ON CONFLICT (rol_id, permiso_id) DO NOTHING;
