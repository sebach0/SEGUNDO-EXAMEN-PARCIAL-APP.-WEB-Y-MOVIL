# 2026-04-26 — Documentación de pruebas API: `servicios`

## Objetivo

Formalizar una matriz de pruebas API para el recurso `servicios` con foco en consultas por ID y listados.

## Resultado

- Se creó `docs/ai/TESTING_STRATEGY.md`.
- Incluye 10 pruebas:
  1. Obtener existente.
  2. Obtener inexistente.
  3. ID inválido.
  4. ID negativo.
  5. Consulta post-eliminación.
  6. Consistencia en múltiples lecturas.
  7. Lectura post-actualización.
  8. Listado general.
  9. Listado vacío.
  10. Listado con alto volumen.
- Incluye plantilla de ejecución manual (`curl`) y criterios de aceptación.

## Nota técnica

Al momento de documentar, no se encontró ruta `/servicios` en `backend/app`.  
El documento queda como estrategia reusable para aplicarse al endpoint real cuando se implemente o se mapee al módulo correspondiente.

