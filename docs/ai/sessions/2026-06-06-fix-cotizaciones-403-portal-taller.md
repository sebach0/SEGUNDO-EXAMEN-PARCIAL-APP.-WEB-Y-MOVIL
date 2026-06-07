# Fix 403 cotizaciones portal taller

**Fecha:** 2026-06-06

## Problema

`POST /api/cotizaciones/solicitudes/{id}` devolvía **403** en el portal taller (`http://localhost/taller/panel/cotizaciones/...`).

Causa: mismo patrón que `/api/talleres/{id}/servicios` — el interceptor Angular solo garantiza token **taller** en rutas `/api/app/taller/*`. En `/api/cotizaciones/*` podía enviarse token **admin** (fallback) → backend responde *"Solo el responsable de taller puede usar el portal."*

## Solución

1. **Backend:** endpoints del portal bajo `/api/app/taller/cotizaciones/solicitudes/{id}` (+ `contexto-oferta`, POST proponer) en `taller_responsable/router.py`, delegando a `cotizaciones/service.py`.
2. **Frontend:** `CotizacionService.listar`, `contextoOferta`, `proponer` apuntan a `/app/taller/cotizaciones/...`.

## Verificación

```powershell
# Login taller demo
$login = Invoke-RestMethod -Method POST -Uri "http://localhost/api/auth/login" -ContentType "application/json" -Body '{"email":"luis.rivera@sc-demo.test","password":"scdemo1"}'
Invoke-RestMethod -Uri "http://localhost/api/app/taller/cotizaciones/solicitudes/21/contexto-oferta" -Headers @{Authorization="Bearer $($login.access_token)"}
```

Tras deploy: `docker compose up -d --build frontend` y hard refresh (Ctrl+Shift+R) en el navegador.

## Nota usuario

Si la solicitud ya tiene cotización activa del mismo taller → **409** (no 403). Probar con otra solicitud PENDIENTE en bandeja.
