# Sesión 2026-04-26 — Velocidad de build Docker

## Resumen

- Diagnóstico y plan: `docs/ai/DOCKER_BUILD_OPTIMIZATION.md`.
- Implementación: contexto `./services/ai-inference`, Dockerfile movido a lógica solo en ese árbol, `.dockerignore` en ai-inference; backend `COPY --chown`; ignores backend/frontend.
- Decisión registrada: `DECISIONS_LOG.md` **DEC-018**.

## Verificación

`docker compose --profile ai config --quiet` (exit 0).
