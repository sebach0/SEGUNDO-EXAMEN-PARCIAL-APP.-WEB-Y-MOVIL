# Sesión 2026-04-26 — FCM + GoRouter (provider)

## Problema

- En runtime: `No GoRouter found in context` desde `fcm_message_listener.dart` al llegar FCM en foreground.
- Causa: `FcmMessageListener` envuelve a `ShadApp.router(routerConfig: ...)`. `GoRouter` se expone vía `InheritedGoRouter` **debajo** de ese árbol; el `context` del listener no ve el router.

## Cambio

- `FcmMessageListener` pasa a `ConsumerStatefulWidget`.
- Sustituir `GoRouter.of(context)` por `ref.read(goRouterProvider)` (misma instancia que `routerConfig`).
- Navegación en tap de notificación local y en `onMessageOpenedApp` / mensaje inicial con la misma instancia.

## Nota (build Android)

- Errores Kotlin `Could not close incremental caches` / `Storage is already registered`: caché incremental corrupta o daemon en Windows. Mitigación típica: cerrar Android Studio, `cd mobile && flutter clean`, borrar `mobile/build` y `mobile/android/.gradle` si persiste, volver a compilar. Si vuelve a ocurrir, compilar con un solo worker (`org.gradle.workers.max=1` o desactivar paralelismo) como último recurso.
