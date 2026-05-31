import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../application/comunicacion_providers.dart';
import '../widgets/notificacion_list_item.dart';

/// CU19 — centro de notificaciones.
class NotificacionesCentroScreen extends ConsumerStatefulWidget {
  const NotificacionesCentroScreen({super.key});

  @override
  ConsumerState<NotificacionesCentroScreen> createState() => _NotificacionesCentroScreenState();
}

class _NotificacionesCentroScreenState extends ConsumerState<NotificacionesCentroScreen> {
  bool _soloNoLeidas = false;

  @override
  Widget build(BuildContext context) {
    final async = ref.watch(notificacionesClienteProvider(_soloNoLeidas));
    final theme = ShadTheme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Notificaciones'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.canPop() ? context.pop() : context.go('/cliente/app/home'),
        ),
      ),
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            child: Row(
              children: [
                FilterChip(
                  label: const Text('Todas'),
                  selected: !_soloNoLeidas,
                  onSelected: (_) => setState(() => _soloNoLeidas = false),
                ),
                const SizedBox(width: 8),
                FilterChip(
                  label: const Text('No leídas'),
                  selected: _soloNoLeidas,
                  onSelected: (_) => setState(() => _soloNoLeidas = true),
                ),
              ],
            ),
          ),
          Expanded(
            child: async.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => _ErrorCentro(
                message: e.toString(),
                onRetry: () => ref.invalidate(notificacionesClienteProvider(_soloNoLeidas)),
              ),
              data: (list) {
                if (list.isEmpty) {
                  return _EmptyCentro(soloNoLeidas: _soloNoLeidas, theme: theme);
                }
                return RefreshIndicator(
                  onRefresh: () => ref.refresh(notificacionesClienteProvider(_soloNoLeidas).future),
                  child: ListView.separated(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    itemCount: list.length,
                    separatorBuilder: (_, __) => Divider(height: 1, color: theme.colorScheme.border),
                    itemBuilder: (context, i) {
                      final n = list[i];
                      return NotificacionListItem(
                        notificacion: n,
                        onTap: () => context.push('/cliente/app/notificaciones/${n.id}', extra: n),
                      );
                    },
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _EmptyCentro extends StatelessWidget {
  const _EmptyCentro({required this.soloNoLeidas, required this.theme});

  final bool soloNoLeidas;
  final ShadThemeData theme;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.notifications_none_rounded, size: 56, color: theme.colorScheme.mutedForeground),
            const SizedBox(height: 16),
            Text(
              soloNoLeidas ? 'No tenés notificaciones sin leer.' : 'Todavía no hay notificaciones.',
              textAlign: TextAlign.center,
              style: theme.textTheme.large,
            ),
            const SizedBox(height: 8),
            Text(
              'Cuando haya novedades en tus solicitudes, las verás acá.',
              textAlign: TextAlign.center,
              style: theme.textTheme.muted,
            ),
          ],
        ),
      ),
    );
  }
}

class _ErrorCentro extends StatelessWidget {
  const _ErrorCentro({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            ShadButton.outline(onPressed: onRetry, child: const Text('Reintentar')),
          ],
        ),
      ),
    );
  }
}
