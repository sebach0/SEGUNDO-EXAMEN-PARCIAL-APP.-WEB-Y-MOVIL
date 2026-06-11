import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// Navegación principal técnico: Inicio · Servicios · Perfil.
class TecnicoAppShell extends StatelessWidget {
  const TecnicoAppShell({super.key, required this.child});

  final Widget child;

  static bool _showBottomNav(String path) {
    // Detalle / ubicación / estado / chat / comprobante: pantalla completa sin barra inferior.
    if (path.startsWith('/tecnico/app/servicios/')) return false;
    return true;
  }

  static int _indexForPath(String path) {
    if (path.startsWith('/tecnico/app/perfil')) return 3;
    if (path.startsWith('/tecnico/app/historial')) return 2;
    if (path.startsWith('/tecnico/app/servicios')) return 1;
    return 0;
  }

  @override
  Widget build(BuildContext context) {
    final loc = GoRouterState.of(context).uri.path;
    final showNav = _showBottomNav(loc);
    final index = _indexForPath(loc);

    return Scaffold(
      body: SafeArea(child: child),
      bottomNavigationBar: showNav
          ? NavigationBar(
              selectedIndex: index,
              onDestinationSelected: (i) {
                switch (i) {
                  case 0:
                    context.go('/tecnico/app/inicio');
                  case 1:
                    context.go('/tecnico/app/servicios');
                  case 2:
                    context.go('/tecnico/app/historial');
                  default:
                    context.go('/tecnico/app/perfil');
                }
              },
              destinations: const [
                NavigationDestination(
                  icon: Icon(Icons.home_outlined),
                  selectedIcon: Icon(Icons.home_rounded),
                  label: 'Inicio',
                ),
                NavigationDestination(
                  icon: Icon(Icons.assignment_outlined),
                  selectedIcon: Icon(Icons.assignment_rounded),
                  label: 'Servicios',
                ),
                NavigationDestination(
                  icon: Icon(Icons.history_outlined),
                  selectedIcon: Icon(Icons.history_rounded),
                  label: 'Historial',
                ),
                NavigationDestination(
                  icon: Icon(Icons.person_outline),
                  selectedIcon: Icon(Icons.person_rounded),
                  label: 'Perfil',
                ),
              ],
            )
          : null,
    );
  }
}
