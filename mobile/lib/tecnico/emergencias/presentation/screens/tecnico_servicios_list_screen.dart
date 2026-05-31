import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../application/tecnico_emergencias_providers.dart';
import '../widgets/tecnico_servicio_card.dart';

/// CU32 — lista de servicios asignados al técnico.
class TecnicoServiciosListScreen extends ConsumerWidget {
  const TecnicoServiciosListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(tecnicoServiciosAsignadosProvider);
    final scheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(title: const Text('Servicios asignados')),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => _ErrorBody(
          message: e.toString().replaceFirst('Exception: ', ''),
          onRetry: () => ref.invalidate(tecnicoServiciosAsignadosProvider),
        ),
        data: (items) {
          if (items.isEmpty) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(28),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.assignment_turned_in_outlined, size: 56, color: scheme.onSurfaceVariant),
                    const SizedBox(height: 16),
                    Text(
                      'No tenés servicios asignados',
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Cuando el taller te asigne una solicitud, aparecerá aquí.',
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: scheme.onSurface.withValues(alpha: 0.75),
                            height: 1.35,
                          ),
                    ),
                  ],
                ),
              ),
            );
          }
          return RefreshIndicator(
            onRefresh: () => ref.refresh(tecnicoServiciosAsignadosProvider.future),
            child: ListView.separated(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
              itemCount: items.length,
              separatorBuilder: (_, __) => const SizedBox(height: 12),
              itemBuilder: (context, i) {
                final s = items[i];
                return TecnicoServicioCard(
                  servicio: s,
                  onTap: () => context.push('/tecnico/app/servicios/${s.solicitudId}', extra: s),
                );
              },
            ),
          );
        },
      ),
    );
  }
}

class _ErrorBody extends StatelessWidget {
  const _ErrorBody({required this.message, required this.onRetry});

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
            FilledButton(onPressed: onRetry, child: const Text('Reintentar')),
          ],
        ),
      ),
    );
  }
}
