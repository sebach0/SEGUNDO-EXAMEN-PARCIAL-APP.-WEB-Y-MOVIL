import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

/// Restablecer contraseña (flujo informativo; backend según despliegue).
class TecnicoRecoverScreen extends StatefulWidget {
  const TecnicoRecoverScreen({super.key});

  @override
  State<TecnicoRecoverScreen> createState() => _TecnicoRecoverScreenState();
}

class _TecnicoRecoverScreenState extends State<TecnicoRecoverScreen> {
  final _email = TextEditingController();
  bool _sent = false;

  @override
  void dispose() {
    _email.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded),
          onPressed: () {
            if (context.canPop()) {
              context.pop();
            } else {
              context.go('/tecnico/login');
            }
          },
        ),
        title: const Text('Restablecer contraseña'),
      ),
      body: DecoratedBox(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [
              Color(0xFF0B1020),
              Color(0xFF121A30),
            ],
          ),
        ),
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: _sent
                ? Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(Icons.mark_email_read_outlined, size: 48, color: theme.colorScheme.primary),
                      const SizedBox(height: 16),
                      Text(
                        'Si el correo existe en el sistema, recibirás instrucciones para restablecer tu contraseña.',
                        style: theme.textTheme.bodyLarge?.copyWith(height: 1.35),
                      ),
                      const SizedBox(height: 24),
                      ShadButton(
                        onPressed: () => context.go('/tecnico/login'),
                        child: const Text('Volver al inicio de sesión'),
                      ),
                    ],
                  )
                : ListView(
                    children: [
                      Text(
                        'Ingresá el correo de tu cuenta de técnico o responsable de taller.',
                        style: theme.textTheme.bodyMedium?.copyWith(
                          color: theme.colorScheme.onSurface.withValues(alpha: 0.8),
                          height: 1.35,
                        ),
                      ),
                      const SizedBox(height: 20),
                      Text('Correo', style: theme.textTheme.labelLarge?.copyWith(fontWeight: FontWeight.w600)),
                      const SizedBox(height: 8),
                      ShadInput(
                        controller: _email,
                        placeholder: const Text('correo@ejemplo.com'),
                        keyboardType: TextInputType.emailAddress,
                      ),
                      const SizedBox(height: 24),
                      ShadButton(
                        width: double.infinity,
                        onPressed: () {
                          if (_email.text.trim().isEmpty) return;
                          setState(() => _sent = true);
                        },
                        child: const Text('Enviar solicitud'),
                      ),
                      const SizedBox(height: 12),
                      ShadButton.link(
                        onPressed: () => context.go('/tecnico/login'),
                        child: const Text('Volver'),
                      ),
                    ],
                  ),
          ),
        ),
      ),
    );
  }
}
