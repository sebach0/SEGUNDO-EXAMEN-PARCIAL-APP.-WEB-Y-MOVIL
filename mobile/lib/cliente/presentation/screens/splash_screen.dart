import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../../core/config/app_env.dart';
import '../../application/client_auth_provider.dart';
import '../../application/client_auth_state.dart';

class SplashScreen extends ConsumerStatefulWidget {
  const SplashScreen({super.key});

  @override
  ConsumerState<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends ConsumerState<SplashScreen> {
  bool _navigated = false;

  Future<void> _go(ClientAuthState auth) async {
    if (_navigated || !mounted) return;
    await Future<void>.delayed(const Duration(milliseconds: 900));
    if (!mounted) return;
    final prefs = await SharedPreferences.getInstance();
    if (!mounted) return;
    final onboardingDone = prefs.getBool('cliente_onboarding_v1_done') ?? false;

    if (auth.isAuthenticated) {
      _navigated = true;
      context.go('/cliente/app/home');
      return;
    }
    if (!onboardingDone) {
      _navigated = true;
      context.go('/onboarding');
      return;
    }
    _navigated = true;
    context.go('/modo');
  }

  @override
  Widget build(BuildContext context) {
    ref.listen<ClientAuthState>(clientAuthNotifierProvider, (prev, next) {
      if (next.status != ClientAuthStatus.checking) {
        _go(next);
      }
    });

    ref.watch(clientAuthNotifierProvider);

    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      backgroundColor: scheme.surface,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.shield_moon, size: 72, color: scheme.primary),
            const SizedBox(height: 20),
            Text(
              AppEnv.appName,
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.5,
                  ),
            ),
            const SizedBox(height: 8),
            Text(
              'Asistencia vehicular inteligente',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: scheme.onSurfaceVariant,
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
    );
  }
}
