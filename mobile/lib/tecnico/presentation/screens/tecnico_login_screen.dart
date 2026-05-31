import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../../core/config/app_env.dart';
import '../../../core/theme/app_theme.dart';
import '../../application/tecnico_auth_provider.dart';
import '../../application/tecnico_auth_state.dart';

/// CU2 — Iniciar sesión móvil (técnico / responsable de taller).
class TecnicoLoginScreen extends ConsumerStatefulWidget {
  const TecnicoLoginScreen({super.key});

  @override
  ConsumerState<TecnicoLoginScreen> createState() => _TecnicoLoginScreenState();
}

class _TecnicoLoginScreenState extends ConsumerState<TecnicoLoginScreen> {
  final _email = TextEditingController();
  final _password = TextEditingController();
  final _emailFocus = FocusNode();
  final _passwordFocus = FocusNode();
  bool _obscurePassword = true;

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    _emailFocus.dispose();
    _passwordFocus.dispose();
    super.dispose();
  }

  void _goBack() {
    if (context.canPop()) {
      context.pop();
    } else {
      context.go('/modo');
    }
  }

  void _submit() {
    FocusScope.of(context).unfocus();
    ref.read(tecnicoAuthNotifierProvider.notifier).clearError();
    ref.read(tecnicoAuthNotifierProvider.notifier).login(
          email: _email.text,
          password: _password.text,
        );
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(tecnicoAuthNotifierProvider);
    final theme = Theme.of(context);
    final cs = theme.colorScheme;
    final bottomInset = MediaQuery.viewInsetsOf(context).bottom;

    ref.listen<TecnicoAuthState>(tecnicoAuthNotifierProvider, (p, n) {
      if (n.isAuthenticated) context.go('/tecnico/app/inicio');
    });

    return Scaffold(
      resizeToAvoidBottomInset: true,
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
        child: SafeArea(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(4, 4, 8, 0),
                child: Row(
                  children: [
                    IconButton(
                      onPressed: _goBack,
                      icon: const Icon(Icons.arrow_back_rounded),
                      tooltip: 'Volver',
                      style: IconButton.styleFrom(foregroundColor: cs.onSurface),
                    ),
                    const Spacer(),
                  ],
                ),
              ),
              Expanded(
                child: GestureDetector(
                  onTap: () => FocusScope.of(context).unfocus(),
                  behavior: HitTestBehavior.opaque,
                  child: ListView(
                    keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
                    padding: EdgeInsets.fromLTRB(24, 8, 24, 24 + bottomInset),
                    children: [
                      _TecnicoLoginBrandHeader(theme: theme),
                      const SizedBox(height: 28),
                      DecoratedBox(
                        decoration: BoxDecoration(
                          color: const Color(0xFF141B2E),
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(color: const Color(0xFF2A3658)),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withValues(alpha: 0.35),
                              blurRadius: 24,
                              offset: const Offset(0, 12),
                            ),
                          ],
                        ),
                        child: Padding(
                          padding: const EdgeInsets.fromLTRB(20, 22, 20, 22),
                          child: AutofillGroup(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.stretch,
                              children: [
                                Text(
                                  'Acceso técnico',
                                  style: theme.textTheme.titleLarge?.copyWith(
                                    fontWeight: FontWeight.w600,
                                    letterSpacing: -0.3,
                                  ),
                                ),
                                const SizedBox(height: 6),
                                Text(
                                  'Correo y contraseña de tu cuenta institucional.',
                                  style: theme.textTheme.bodyMedium?.copyWith(
                                    color: cs.onSurface.withValues(alpha: 0.72),
                                    height: 1.35,
                                  ),
                                ),
                                const SizedBox(height: 22),
                                Text(
                                  'Correo electrónico',
                                  style: theme.textTheme.labelLarge?.copyWith(
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                                const SizedBox(height: 8),
                                ShadInput(
                                  controller: _email,
                                  focusNode: _emailFocus,
                                  placeholder: const Text('correo@ejemplo.com'),
                                  keyboardType: TextInputType.emailAddress,
                                  textInputAction: TextInputAction.next,
                                  autofillHints: const [AutofillHints.username, AutofillHints.email],
                                  autocorrect: false,
                                  leading: Icon(
                                    Icons.alternate_email_rounded,
                                    size: 20,
                                    color: cs.onSurface.withValues(alpha: 0.55),
                                  ),
                                  onSubmitted: (_) => _passwordFocus.requestFocus(),
                                ),
                                const SizedBox(height: 18),
                                Text(
                                  'Contraseña',
                                  style: theme.textTheme.labelLarge?.copyWith(
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                                const SizedBox(height: 8),
                                ShadInput(
                                  controller: _password,
                                  focusNode: _passwordFocus,
                                  placeholder: const Text('Tu contraseña'),
                                  obscureText: _obscurePassword,
                                  textInputAction: TextInputAction.done,
                                  autofillHints: const [AutofillHints.password],
                                  autocorrect: false,
                                  enableSuggestions: false,
                                  leading: Icon(
                                    Icons.lock_outline_rounded,
                                    size: 20,
                                    color: cs.onSurface.withValues(alpha: 0.55),
                                  ),
                                  trailing: IconButton(
                                    onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                                    tooltip: _obscurePassword ? 'Mostrar contraseña' : 'Ocultar contraseña',
                                    icon: Icon(
                                      _obscurePassword ? Icons.visibility_outlined : Icons.visibility_off_outlined,
                                      size: 22,
                                      color: cs.onSurface.withValues(alpha: 0.65),
                                    ),
                                  ),
                                  onSubmitted: (_) => _submit(),
                                ),
                                if (auth.authError != null) ...[
                                  const SizedBox(height: 16),
                                  _TecnicoLoginErrorBanner(message: auth.authError!),
                                ],
                                const SizedBox(height: 22),
                                ShadButton(
                                  width: double.infinity,
                                  size: ShadButtonSize.lg,
                                  onPressed: auth.isLoggingIn ? null : _submit,
                                  child: auth.isLoggingIn
                                      ? SizedBox(
                                          height: 22,
                                          width: 22,
                                          child: CircularProgressIndicator(
                                            strokeWidth: 2.5,
                                            color: cs.onPrimary,
                                          ),
                                        )
                                      : const Text('Ingresar'),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 20),
                      Align(
                        alignment: Alignment.centerRight,
                        child: ShadButton.link(
                          onPressed: () => context.go('/tecnico/recuperar'),
                          child: const Text('¿Olvidaste tu contraseña?'),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _TecnicoLoginBrandHeader extends StatelessWidget {
  const _TecnicoLoginBrandHeader({required this.theme});

  final ThemeData theme;

  @override
  Widget build(BuildContext context) {
    final secondary = theme.colorScheme.secondary;
    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        DecoratedBox(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                AppTheme.primaryColor.withValues(alpha: 0.95),
                const Color(0xFF3949AB),
              ],
            ),
            boxShadow: [
              BoxShadow(
                color: secondary.withValues(alpha: 0.35),
                blurRadius: 20,
                offset: const Offset(0, 8),
              ),
            ],
          ),
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Icon(Icons.build_circle_rounded, size: 32, color: secondary),
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                AppEnv.appName,
                style: theme.textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w700,
                  letterSpacing: -0.2,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                'Operaciones de taller y campo.',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.68),
                  height: 1.35,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _TecnicoLoginErrorBanner extends StatelessWidget {
  const _TecnicoLoginErrorBanner({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    final error = Theme.of(context).colorScheme.error;
    return DecoratedBox(
      decoration: BoxDecoration(
        color: error.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: error.withValues(alpha: 0.45)),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.error_outline_rounded, color: error, size: 22),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                message,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: Theme.of(context).colorScheme.onErrorContainer,
                      height: 1.35,
                    ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
