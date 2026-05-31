import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/config/app_env.dart';
import '../../../core/theme/app_theme.dart';
import '../../application/tecnico_auth_provider.dart';
import '../../application/tecnico_auth_state.dart';

/// Splash de entrada al flujo técnico (desde selector de modo).
class TecnicoSplashScreen extends ConsumerStatefulWidget {
  const TecnicoSplashScreen({super.key});

  @override
  ConsumerState<TecnicoSplashScreen> createState() => _TecnicoSplashScreenState();
}

class _TecnicoSplashScreenState extends ConsumerState<TecnicoSplashScreen> {
  bool _routed = false;

  void _route(TecnicoAuthState auth) {
    if (_routed || !mounted) return;
    if (auth.status == TecnicoAuthStatus.checking) return;
    _routed = true;
    if (auth.isAuthenticated) {
      context.go('/tecnico/app/inicio');
    } else {
      context.go('/tecnico/login');
    }
  }

  @override
  Widget build(BuildContext context) {
    ref.watch(tecnicoAuthNotifierProvider);
    ref.listen<TecnicoAuthState>(tecnicoAuthNotifierProvider, (p, n) {
      _route(n);
    });

    Future<void>.delayed(const Duration(milliseconds: 900), () {
      if (mounted) _route(ref.read(tecnicoAuthNotifierProvider));
    });

    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      body: DecoratedBox(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              Color(0xFF0B1020),
              Color(0xFF121A30),
              Color(0xFF0B1020),
            ],
          ),
        ),
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              DecoratedBox(
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(
                      color: AppTheme.secondaryColor.withValues(alpha: 0.35),
                      blurRadius: 28,
                      offset: const Offset(0, 10),
                    ),
                  ],
                ),
                child: CircleAvatar(
                  radius: 40,
                  backgroundColor: scheme.surfaceContainerHighest,
                  child: const Icon(Icons.build_circle_rounded, size: 48, color: AppTheme.secondaryColor),
                ),
              ),
              const SizedBox(height: 24),
              Text(
                AppEnv.appName,
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.w700,
                      letterSpacing: -0.2,
                    ),
              ),
              const SizedBox(height: 8),
              Text(
                'Acceso técnico y taller',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: scheme.onSurface.withValues(alpha: 0.72),
                    ),
              ),
              const SizedBox(height: 40),
              const SizedBox(
                width: 32,
                height: 32,
                child: CircularProgressIndicator(strokeWidth: 3),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
