// CU11 — elegir vehículo antes del asistente de reporte.
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../../application/vehiculos_providers.dart';

class EmergenciaSeleccionVehiculoScreen extends ConsumerWidget {
  const EmergenciaSeleccionVehiculoScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(vehiculosMineProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Reportar emergencia'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.canPop() ? context.pop() : context.go('/cliente/app/home'),
        ),
      ),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(vehiculosMineProvider),
        child: async.when(
          loading: () => const Center(child: Padding(padding: EdgeInsets.all(32), child: CircularProgressIndicator())),
          error: (e, _) => ListView(
            padding: const EdgeInsets.all(24),
            children: [
              Text(e.toString(), style: TextStyle(color: Theme.of(context).colorScheme.error)),
              const SizedBox(height: 12),
              ShadButton(onPressed: () => ref.invalidate(vehiculosMineProvider), child: const Text('Reintentar')),
            ],
          ),
          data: (items) {
            if (items.isEmpty) {
              return ListView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.all(24),
                children: [
                  const SizedBox(height: 40),
                  Icon(Icons.car_crash_outlined, size: 56, color: Theme.of(context).colorScheme.outline),
                  const SizedBox(height: 16),
                  Text(
                    'Necesitás un vehículo registrado',
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Registrá tu vehículo y volvé para poder reportar una emergencia.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant),
                  ),
                  const SizedBox(height: 24),
                  ShadButton(
                    onPressed: () => context.push('/cliente/app/vehiculos/nuevo'),
                    child: const Text('Registrar vehículo'),
                  ),
                ],
              );
            }
            return ListView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.all(16),
              children: [
                for (var i = 0; i < items.length; i++) ...[
                  if (i > 0) const SizedBox(height: 10),
                  ShadCard(
                    child: InkWell(
                      onTap: () => context.push('/cliente/app/emergencias/crear/${items[i].id}'),
                      borderRadius: BorderRadius.circular(12),
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Row(
                          children: [
                            Icon(Icons.emergency_share_rounded, color: Theme.of(context).colorScheme.error),
                            const SizedBox(width: 14),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    items[i].placa,
                                    style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 18),
                                  ),
                                  Text(
                                    '${items[i].marcaNombre} ${items[i].modeloNombre} · ${items[i].tipoNombre}',
                                    style: TextStyle(
                                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                                      fontSize: 13,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            const Icon(Icons.chevron_right),
                          ],
                        ),
                      ),
                    ),
                  ),
                ],
                const SizedBox(height: 20),
                Center(
                  child: ShadButton.outline(
                    onPressed: () => context.push('/cliente/app/emergencias/solicitudes'),
                    child: const Text('Ver mis solicitudes'),
                  ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}
