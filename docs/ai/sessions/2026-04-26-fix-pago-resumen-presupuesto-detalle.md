# Sesión 2026-04-26 — Fix pago resumen: presupuesto técnico desde detalle

## Contexto

Se reportó que en mobile cliente (`pago_resumen`) aparecía “monto no definido” aunque el técnico ya había registrado `presupuesto_bob` para la solicitud.

## Causa raíz

La pantalla de pago consume `emergenciaDetailProvider` (`GET /api/portal/cliente/emergencias/{id}`), pero el schema base `SolicitudEmergenciaRead` no exponía `presupuesto_bob` ni `presupuesto_registrado_at`.

Resultado: en detalle esos campos llegaban `null`, mientras en seguimiento sí existían, generando inconsistencia visual.

## Cambios aplicados

1. **Backend**
   - Archivo: `backend/app/modules/emergencias/schemas.py`
   - Se añadieron a `SolicitudEmergenciaRead`:
     - `presupuesto_bob: Decimal | None`
     - `presupuesto_registrado_at: datetime | None`
   - `SolicitudEmergenciaDetailRead` hereda esos campos automáticamente.

2. **Mobile**
   - Archivo: `mobile/lib/cliente/pagos/presentation/screens/pago_resumen_screen.dart`
   - Se mantiene la regla de negocio: cliente no puede escribir monto.
   - Se agregó refresco manual:
     - botón `refresh` en `AppBar`
     - `RefreshIndicator` (pull-to-refresh)
   - Objetivo: sincronizar rápidamente cuando el técnico registra presupuesto mientras el cliente ya tiene abierta la pantalla.

## Validación rápida

- `python -m py_compile backend/app/modules/emergencias/schemas.py` ✅
- `flutter analyze lib/cliente/pagos/presentation/screens/pago_resumen_screen.dart` ✅

## Resultado esperado

En `pago_resumen`, cuando exista `presupuesto_bob` en backend:

- se mostrará el monto bloqueado fijado por técnico,
- se habilitará `Continuar`,
- no será necesario reiniciar app; bastará refrescar la vista.
