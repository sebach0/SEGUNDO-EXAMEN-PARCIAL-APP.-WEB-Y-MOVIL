# Sesión 2026-06-07 — Fix admin panel 403 usuarios/talleres/permisos

## Síntoma

Panel admin no cargaba usuarios, talleres, roles, permisos ni bitácora (`403 Forbidden`).

## Causa

- Frontend llamaba `/api/usuarios`, `/api/roles`, etc. **sin barra final**.
- FastAPI redirige con **307** a `/api/usuarios/`.
- En el redirect el cliente **pierde el header `Authorization`** → backend responde 403 (HTTPBearer sin credenciales).
- Finanzas (`/api/admin/finanzas/resumen`) funcionaba porque no dispara ese redirect.

## Fix

Trailing slash en `frontend/src/app/core/services/admin-api.service.ts`:
- `/usuarios/`, `/roles/`, `/permisos/`, `/bitacora/`, `/talleres/` (GET y POST colección).

## Verificación

```powershell
# Sin slash → 403; con slash → 200 (con token admin)
GET /api/usuarios   → 403
GET /api/usuarios/  → 200
```
