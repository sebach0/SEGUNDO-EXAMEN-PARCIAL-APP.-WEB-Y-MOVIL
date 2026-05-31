# 2026-04-26 — Variables de entorno solo en la raíz

- Eliminado `backend/.env.example` (duplicado de la plantilla).
- `backend/app/core/config.py`: `pydantic-settings` carga solo `<repo>/.env` si existe.
- `.env.example` raíz: bloque comentado opcional `DATABASE_URL` para uvicorn en host sin Docker.
- `.env` raíz: comentario de una sola fuente; `mobile/.env` se mantiene aparte.
- README y `.gitignore` alineados; `backend/.dockerignore` sin excepción `!.env.example`.
