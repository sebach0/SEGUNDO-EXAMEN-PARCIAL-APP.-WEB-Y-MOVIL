BEGIN;

-- Tokens opacos (hash SHA-256) para verificación de email y recuperación de contraseña.

CREATE TABLE IF NOT EXISTS usuario_tokens_seguridad (
    id              INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    usuario_id      INTEGER NOT NULL,
    tipo            VARCHAR(32) NOT NULL,
    token_hash      CHAR(64) NOT NULL,
    expires_at      TIMESTAMP NOT NULL,
    usado_at        TIMESTAMP,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_usuario_token_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE CASCADE,

    CONSTRAINT ck_usuario_token_tipo
        CHECK (tipo IN ('VERIFICAR_EMAIL', 'RESTABLECER_PASSWORD'))
);

CREATE INDEX IF NOT EXISTS idx_usuario_tokens_lookup
    ON usuario_tokens_seguridad (tipo, token_hash);

CREATE INDEX IF NOT EXISTS idx_usuario_tokens_usuario_tipo
    ON usuario_tokens_seguridad (usuario_id, tipo);

COMMIT;
