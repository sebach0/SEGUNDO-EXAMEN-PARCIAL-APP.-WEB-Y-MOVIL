import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import 'cliente/presentation/router/cliente_go_router.dart';
import 'core/config/app_env.dart';
import 'core/push/fcm_message_listener.dart';
import 'core/services/offline_emergencia_sync_listener.dart';
import 'core/theme/app_theme.dart';
import 'core/theme/emergencias_shad_theme.dart';

class EmergenciasApp extends ConsumerWidget {
  const EmergenciasApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(goRouterProvider);
    // go_router + ShadApp: asegurar ancestro para SnackBar (p. ej. emergencias / permisos / FCM).
    final shad = ShadApp.router(
      title: AppEnv.appName,
      debugShowCheckedModeBanner: false,
      themeMode: ThemeMode.dark,
      theme: EmergenciasShadTheme.dark(),
      materialThemeBuilder: (context, theme) => AppTheme.dark,
      locale: const Locale('es', 'BO'),
      supportedLocales: const [Locale('es', 'BO'), Locale('es')],
      routerConfig: router,
    );
    return OfflineEmergenciaSyncListener(
      child: ScaffoldMessenger(
        child: kIsWeb ? shad : FcmMessageListener(child: shad),
      ),
    );
  }
}
