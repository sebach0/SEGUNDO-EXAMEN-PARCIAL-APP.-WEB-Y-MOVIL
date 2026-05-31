import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:shared_preferences/shared_preferences.dart';

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final _controller = PageController();
  int _page = 0;

  static const _pages = <({String title, String body})>[
    (
      title: 'Tu cuenta',
      body: 'Registra tu cuenta para acceder a servicios de emergencia vehicular cuando los necesites.',
    ),
    (
      title: 'Tus vehículos',
      body: 'Administra placa, marca, modelo y datos clave de cada vehículo en un solo lugar.',
    ),
    (
      title: 'Preparación',
      body: 'Mantén tu información al día para agilizar solicitudes de asistencia en el futuro.',
    ),
  ];

  Future<void> _finish() async {
    final p = await SharedPreferences.getInstance();
    await p.setBool('cliente_onboarding_v1_done', true);
    if (!mounted) return;
    context.go('/modo');
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Bienvenido'),
        actions: [
          TextButton(
            onPressed: _finish,
            child: const Text('Omitir'),
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: PageView.builder(
              controller: _controller,
              itemCount: _pages.length,
              onPageChanged: (i) => setState(() => _page = i),
              itemBuilder: (context, i) {
                final p = _pages[i];
                return Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SizedBox(height: 24),
                      Text(
                        p.title,
                        style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                      ),
                      const SizedBox(height: 16),
                      Text(
                        p.body,
                        style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                              color: scheme.onSurfaceVariant,
                              height: 1.4,
                            ),
                      ),
                    ],
                  ),
                );
              },
            ),
          ),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(
              _pages.length,
              (i) => Padding(
                padding: const EdgeInsets.all(4),
                child: CircleAvatar(
                  radius: 4,
                  backgroundColor: i == _page ? scheme.primary : scheme.outlineVariant,
                ),
              ),
            ),
          ),
          const SizedBox(height: 12),
          Padding(
            padding: const EdgeInsets.fromLTRB(24, 0, 24, 24),
            child: SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: () {
                  if (_page < _pages.length - 1) {
                    _controller.nextPage(
                      duration: const Duration(milliseconds: 280),
                      curve: Curves.easeOut,
                    );
                  } else {
                    _finish();
                  }
                },
                child: Text(_page < _pages.length - 1 ? 'Continuar' : 'Empezar'),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
