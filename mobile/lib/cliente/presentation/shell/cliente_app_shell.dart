import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// Bottom navigation + área de contenido para el área autenticada `/cliente/app/*`.
class ClienteAppShell extends StatelessWidget {
  const ClienteAppShell({super.key, required this.child});

  final Widget child;

  static bool _showBottomNav(String path) {
    if (path.startsWith('/cliente/app/vehiculos/')) return false;
    if (path.startsWith('/cliente/app/emergencias/')) return false;
    return true;
  }

  static int _indexForPath(String path) {
    if (path.startsWith('/cliente/app/perfil')) return 2;
    if (path.startsWith('/cliente/app/vehiculos')) return 1;
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
                    context.go('/cliente/app/home');
                  case 1:
                    context.go('/cliente/app/vehiculos');
                  default:
                    context.go('/cliente/app/perfil');
                }
              },
              destinations: const [
                NavigationDestination(
                  icon: Icon(Icons.home_outlined),
                  selectedIcon: Icon(Icons.home),
                  label: 'Inicio',
                ),
                NavigationDestination(
                  icon: Icon(Icons.directions_car_outlined),
                  selectedIcon: Icon(Icons.directions_car),
                  label: 'Vehículos',
                ),
                NavigationDestination(
                  icon: Icon(Icons.person_outline),
                  selectedIcon: Icon(Icons.person),
                  label: 'Perfil',
                ),
              ],
            )
          : null,
    );
  }
}
