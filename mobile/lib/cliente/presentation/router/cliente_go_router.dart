import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../application/client_auth_provider.dart';
import '../../application/client_auth_state.dart';
import '../screens/actor_select_screen.dart';
import '../screens/cliente_auth_screens.dart';
import '../screens/cliente_home_screen.dart';
import '../screens/cliente_perfil_screen.dart';
import '../screens/cliente_vehiculos_flow.dart';
import '../../pagos/domain/pago_models.dart';
import '../../pagos/presentation/screens/pago_confirmacion_screen.dart';
import '../../pagos/presentation/screens/pago_metodo_screen.dart';
import '../../pagos/presentation/screens/pago_resumen_screen.dart';
import '../../pagos/presentation/screens/pago_resultado_screen.dart';
import '../../pagos/presentation/screens/solicitud_pagos_historial_screen.dart';
import '../../emergencias/presentation/screens/emergencia_detalle_screen.dart';
import '../../emergencias/presentation/screens/emergencia_seguimiento_screen.dart';
import '../../emergencias/presentation/screens/emergencia_ubicacion_tecnico_screen.dart';
import '../../emergencias/presentation/screens/emergencia_seleccion_vehiculo_screen.dart';
import '../../emergencias/presentation/screens/emergencia_wizard_screen.dart';
import '../../comunicacion/presentation/screens/chat_solicitud_screen.dart';
import '../../comunicacion/presentation/screens/notificacion_detalle_screen.dart';
import '../../comunicacion/presentation/screens/notificaciones_centro_screen.dart';
import '../../comunicacion/domain/notificacion_models.dart';
import '../../emergencias/presentation/screens/emergencias_mis_solicitudes_screen.dart';
import '../screens/onboarding_screen.dart';
import '../screens/splash_screen.dart';
import '../shell/cliente_app_shell.dart';
import '../../../tecnico/application/tecnico_auth_provider.dart';
import '../../../tecnico/application/tecnico_auth_state.dart';
import '../../../tecnico/presentation/screens/tecnico_home_screen.dart';
import '../../../tecnico/presentation/screens/tecnico_login_screen.dart';
import '../../../tecnico/emergencias/domain/tecnico_servicio_models.dart';
import '../../../tecnico/emergencias/presentation/screens/tecnico_servicio_actualizar_estado_screen.dart';
import '../../../tecnico/emergencias/presentation/screens/tecnico_servicio_chat_screen.dart';
import '../../../tecnico/emergencias/presentation/screens/tecnico_servicio_detalle_screen.dart';
import '../../../tecnico/emergencias/presentation/screens/tecnico_servicio_ubicacion_screen.dart';
import '../../../tecnico/emergencias/presentation/screens/tecnico_servicio_compartir_ubicacion_screen.dart';
import '../../../tecnico/emergencias/presentation/screens/tecnico_servicios_list_screen.dart';
import '../../../tecnico/presentation/screens/tecnico_placeholder_screen.dart';
import '../../../tecnico/presentation/screens/tecnico_perfil_screen.dart';
import '../../../tecnico/presentation/screens/tecnico_recover_screen.dart';
import '../../../tecnico/presentation/screens/tecnico_splash_screen.dart';
import '../../../tecnico/presentation/shell/tecnico_app_shell.dart';

/// Router principal: splash/onboarding/modo, **cliente** y **técnico** (módulos separados).
final goRouterProvider = Provider<GoRouter>((ref) {
  final refresh = ValueNotifier<int>(0);
  ref.listen<ClientAuthState>(clientAuthNotifierProvider, (_, __) {
    refresh.value++;
  });
  ref.listen<TecnicoAuthState>(tecnicoAuthNotifierProvider, (_, __) {
    refresh.value++;
  });
  ref.onDispose(refresh.dispose);

  return GoRouter(
    initialLocation: '/splash',
    refreshListenable: refresh,
    redirect: (context, state) {
      final loc = state.matchedLocation;

      if (loc.startsWith('/tecnico')) {
        final t = ref.read(tecnicoAuthNotifierProvider);
        if (t.status == TecnicoAuthStatus.checking) return null;
        final publicTecnico = loc.startsWith('/tecnico/login') ||
            loc.startsWith('/tecnico/recuperar') ||
            loc.startsWith('/tecnico/splash');
        if (t.isAuthenticated) {
          if (publicTecnico && !loc.startsWith('/tecnico/splash')) {
            return '/tecnico/app/inicio';
          }
          return null;
        }
        if (loc.startsWith('/tecnico/app')) return '/tecnico/login';
        return null;
      }

      final auth = ref.read(clientAuthNotifierProvider);
      if (auth.status == ClientAuthStatus.checking) return null;

      final publicAuth = loc.startsWith('/cliente/login') ||
          loc.startsWith('/cliente/registro') ||
          loc.startsWith('/cliente/recuperar');

      if (auth.isAuthenticated) {
        if (publicAuth) return '/cliente/app/home';
        return null;
      }

      if (loc.startsWith('/cliente/app')) return '/cliente/login';
      return null;
    },
    routes: [
      GoRoute(
        path: '/splash',
        builder: (context, state) => const SplashScreen(),
      ),
      GoRoute(
        path: '/onboarding',
        builder: (context, state) => const OnboardingScreen(),
      ),
      GoRoute(
        path: '/modo',
        builder: (context, state) => const ActorSelectScreen(),
      ),
      GoRoute(
        path: '/cliente/login',
        builder: (context, state) => const ClienteLoginScreen(),
      ),
      GoRoute(
        path: '/cliente/registro',
        builder: (context, state) => const ClienteRegisterScreen(),
      ),
      GoRoute(
        path: '/cliente/recuperar',
        builder: (context, state) => const ClienteRecoverScreen(),
      ),
      GoRoute(
        path: '/tecnico/splash',
        builder: (context, state) => const TecnicoSplashScreen(),
      ),
      GoRoute(
        path: '/tecnico/login',
        builder: (context, state) => const TecnicoLoginScreen(),
      ),
      GoRoute(
        path: '/tecnico/recuperar',
        builder: (context, state) => const TecnicoRecoverScreen(),
      ),
      ShellRoute(
        builder: (context, state, child) => TecnicoAppShell(child: child),
        routes: [
          GoRoute(
            path: '/tecnico/app/inicio',
            builder: (context, state) => const TecnicoHomeScreen(),
          ),
          GoRoute(
            path: '/tecnico/app/servicios',
            builder: (context, state) => const TecnicoServiciosListScreen(),
          ),
          GoRoute(
            path: '/tecnico/app/servicios/:sid',
            builder: (context, state) {
              final id = int.tryParse(state.pathParameters['sid'] ?? '');
              if (id == null) return const SizedBox.shrink();
              final extra = state.extra;
              return TecnicoServicioDetalleScreen(
                solicitudId: id,
                initial: extra is ServicioAsignadoTecnico ? extra : null,
              );
            },
          ),
          GoRoute(
            path: '/tecnico/app/servicios/:sid/ubicacion',
            builder: (context, state) {
              final id = int.tryParse(state.pathParameters['sid'] ?? '');
              if (id == null) return const SizedBox.shrink();
              return TecnicoServicioUbicacionScreen(solicitudId: id);
            },
          ),
          GoRoute(
            path: '/tecnico/app/servicios/:sid/compartir-ubicacion',
            builder: (context, state) {
              final id = int.tryParse(state.pathParameters['sid'] ?? '');
              if (id == null) return const SizedBox.shrink();
              return TecnicoServicioCompartirUbicacionScreen(solicitudId: id);
            },
          ),
          GoRoute(
            path: '/tecnico/app/servicios/:sid/estado',
            builder: (context, state) {
              final id = int.tryParse(state.pathParameters['sid'] ?? '');
              if (id == null) return const SizedBox.shrink();
              final extra = state.extra;
              return TecnicoServicioActualizarEstadoScreen(
                solicitudId: id,
                initial: extra is ServicioAsignadoTecnico ? extra : null,
              );
            },
          ),
          GoRoute(
            path: '/tecnico/app/servicios/:sid/chat',
            builder: (context, state) {
              final id = int.tryParse(state.pathParameters['sid'] ?? '');
              if (id == null) return const SizedBox.shrink();
              final extra = state.extra;
              return TecnicoServicioChatScreen(
                solicitudId: id,
                initial: extra is ServicioAsignadoTecnico ? extra : null,
              );
            },
          ),
          GoRoute(
            path: '/tecnico/app/historial',
            builder: (context, state) => Scaffold(
              appBar: AppBar(
                title: const Text('Historial'),
                leading: BackButton(onPressed: () => context.pop()),
              ),
              body: const TecnicoPlaceholderScreen(
                title: '',
                message:
                    'Próximamente podrás revisar el historial de atenciones desde esta pantalla.',
                icon: Icons.history_rounded,
              ),
            ),
          ),
          GoRoute(
            path: '/tecnico/app/perfil',
            builder: (context, state) => const TecnicoPerfilScreen(),
          ),
        ],
      ),
      ShellRoute(
        builder: (context, state, child) => ClienteAppShell(child: child),
        routes: [
          GoRoute(
            path: '/cliente/app/home',
            builder: (context, state) => const ClienteHomeScreen(),
          ),
          GoRoute(
            path: '/cliente/app/emergencias',
            builder: (context, state) => const EmergenciaSeleccionVehiculoScreen(),
          ),
          GoRoute(
            path: '/cliente/app/emergencias/solicitudes/:sid/seguimiento',
            builder: (context, state) {
              final id = int.tryParse(state.pathParameters['sid'] ?? '');
              if (id == null) return const SizedBox.shrink();
              return EmergenciaSeguimientoScreen(solicitudId: id);
            },
          ),
          GoRoute(
            path: '/cliente/app/emergencias/solicitudes/:sid/ubicacion-tecnico',
            builder: (context, state) {
              final id = int.tryParse(state.pathParameters['sid'] ?? '');
              if (id == null) return const SizedBox.shrink();
              return EmergenciaUbicacionTecnicoScreen(solicitudId: id);
            },
          ),
          GoRoute(
            path: '/cliente/app/emergencias/solicitudes/:sid/chat',
            builder: (context, state) {
              final id = int.tryParse(state.pathParameters['sid'] ?? '');
              if (id == null) return const SizedBox.shrink();
              return ChatSolicitudScreen(solicitudId: id);
            },
          ),
          GoRoute(
            path: '/cliente/app/emergencias/solicitudes/:sid/pagos',
            builder: (context, state) {
              final id = int.tryParse(state.pathParameters['sid'] ?? '');
              if (id == null) return const SizedBox.shrink();
              return SolicitudPagosHistorialScreen(solicitudId: id);
            },
          ),
          GoRoute(
            path: '/cliente/app/emergencias/solicitudes/:sid/pago/resumen',
            builder: (context, state) {
              final id = int.tryParse(state.pathParameters['sid'] ?? '');
              if (id == null) return const SizedBox.shrink();
              return PagoResumenScreen(solicitudId: id);
            },
          ),
          GoRoute(
            path: '/cliente/app/emergencias/solicitudes/:sid/pago/metodo',
            builder: (context, state) {
              final id = int.tryParse(state.pathParameters['sid'] ?? '');
              final extra = state.extra;
              if (id == null || extra is! PagoDraft) return const SizedBox.shrink();
              return PagoMetodoScreen(solicitudId: id, draft: extra);
            },
          ),
          GoRoute(
            path: '/cliente/app/emergencias/solicitudes/:sid/pago/confirmar',
            builder: (context, state) {
              final id = int.tryParse(state.pathParameters['sid'] ?? '');
              final extra = state.extra;
              if (id == null || extra is! PagoDraft || extra.metodo == null) return const SizedBox.shrink();
              return PagoConfirmacionScreen(solicitudId: id, draft: extra);
            },
          ),
          GoRoute(
            path: '/cliente/app/emergencias/solicitudes/:sid/pago/resultado',
            builder: (context, state) {
              final id = int.tryParse(state.pathParameters['sid'] ?? '');
              final extra = state.extra;
              if (id == null || extra is! PagoRead) return const SizedBox.shrink();
              return PagoResultadoScreen(solicitudId: id, pagoInicial: extra);
            },
          ),
          GoRoute(
            path: '/cliente/app/emergencias/solicitudes/:sid',
            builder: (context, state) {
              final id = int.tryParse(state.pathParameters['sid'] ?? '');
              if (id == null) return const SizedBox.shrink();
              return EmergenciaDetalleScreen(solicitudId: id);
            },
          ),
          GoRoute(
            path: '/cliente/app/emergencias/solicitudes',
            builder: (context, state) => const EmergenciasMisSolicitudesScreen(),
          ),
          GoRoute(
            path: '/cliente/app/emergencias/crear/:vid',
            builder: (context, state) {
              final id = int.tryParse(state.pathParameters['vid'] ?? '');
              if (id == null) return const SizedBox.shrink();
              return EmergenciaWizardScreen(vehiculoId: id);
            },
          ),
          GoRoute(
            path: '/cliente/app/vehiculos/nuevo',
            builder: (context, state) => const ClienteVehiculoFormScreen(),
          ),
          GoRoute(
            path: '/cliente/app/vehiculos/:vid/editar',
            builder: (context, state) {
              final id = int.tryParse(state.pathParameters['vid'] ?? '');
              if (id == null) return const SizedBox.shrink();
              return ClienteVehiculoFormScreen(vehiculoId: id);
            },
          ),
          GoRoute(
            path: '/cliente/app/vehiculos/:vid',
            builder: (context, state) {
              final id = int.tryParse(state.pathParameters['vid'] ?? '');
              if (id == null) return const SizedBox.shrink();
              return ClienteVehiculoDetailScreen(vehiculoId: id);
            },
          ),
          GoRoute(
            path: '/cliente/app/vehiculos',
            builder: (context, state) => const ClienteVehiculosListScreen(),
          ),
          GoRoute(
            path: '/cliente/app/perfil',
            builder: (context, state) => const ClientePerfilScreen(),
          ),
          GoRoute(
            path: '/cliente/app/notificaciones',
            builder: (context, state) => const NotificacionesCentroScreen(),
          ),
          GoRoute(
            path: '/cliente/app/notificaciones/:nid',
            builder: (context, state) {
              final id = int.tryParse(state.pathParameters['nid'] ?? '');
              if (id == null) return const SizedBox.shrink();
              final extra = state.extra;
              return NotificacionDetalleScreen(
                notificacionId: id,
                initial: extra is NotificacionRead ? extra : null,
              );
            },
          ),
        ],
      ),
    ],
    debugLogDiagnostics: kDebugMode,
  );
});
