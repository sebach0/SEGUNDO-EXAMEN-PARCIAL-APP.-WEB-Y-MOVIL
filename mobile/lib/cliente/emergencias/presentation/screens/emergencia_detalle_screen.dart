import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../../pagos/presentation/widgets/solicitud_pago_cta_block.dart';
import '../../application/emergencias_providers.dart';
import '../../domain/solicitud_emergencia_models.dart';
import '../widgets/ai/solicitud_ai_resumen_card.dart';
import '../widgets/seguimiento/estado_solicitud_badge.dart';

/// Detalle de una solicitud (API fase 1 + campos fase 2 en JSON).
class EmergenciaDetalleScreen extends ConsumerWidget {
  const EmergenciaDetalleScreen({super.key, required this.solicitudId});

  final int solicitudId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(emergenciaDetailProvider(solicitudId));

    return Scaffold(
      appBar: AppBar(
        title: Text('Solicitud #$solicitudId'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.canPop() ? context.pop() : context.go('/cliente/app/emergencias/solicitudes'),
        ),
      ),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => _ErrorBody(
          message: e.toString(),
          onRetry: () => ref.invalidate(emergenciaDetailProvider(solicitudId)),
        ),
        data: (d) => RefreshIndicator(
          onRefresh: () => ref.refresh(emergenciaDetailProvider(solicitudId).future),
          child: ListView(
            padding: const EdgeInsets.all(20),
            children: [
              Row(
                children: [
                  EstadoSolicitudBadge(estado: d.estado),
                  const Spacer(),
                  Text(
                    'Vehículo #${d.vehiculoId}',
                    style: Theme.of(context).textTheme.labelLarge,
                  ),
                ],
              ),
              const SizedBox(height: 20),
              Text('Resumen', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              Text(
                'Ubicaciones: ${d.ubicaciones.length} · Evidencias: ${d.evidencias.length}',
                style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant),
              ),
              if (d.descripcionTexto != null && d.descripcionTexto!.trim().isNotEmpty) ...[
                const SizedBox(height: 16),
                ShadCard(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Text(d.descripcionTexto!),
                  ),
                ),
              ],
              const SizedBox(height: 20),
              Text('Análisis asistido', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 10),
              SolicitudAiResumenCard(
                payload: d.aiPayload,
                tieneUbicacionServidor: d.ubicaciones.isNotEmpty,
                tieneFotoServidor: d.evidencias.any((e) => e.tipo == TipoEvidenciaSolicitud.foto),
                tieneAudioServidor: d.evidencias.any((e) => e.tipo == TipoEvidenciaSolicitud.audio),
              ),
              if (d.tiempoEstimadoMin != null) ...[
                const SizedBox(height: 12),
                Text(
                  'ETA registrada: ${d.tiempoEstimadoMin} min (ver pantalla de seguimiento para contexto).',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
              const SizedBox(height: 28),
              ShadButton(
                onPressed: () => context.push('/cliente/app/emergencias/solicitudes/$solicitudId/seguimiento'),
                child: const Text('Ver seguimiento completo'),
              ),
              const SizedBox(height: 12),
              ShadButton.outline(
                onPressed: () => context.push('/cliente/app/emergencias/solicitudes/$solicitudId/chat'),
                leading: const Icon(Icons.chat_bubble_outline_rounded, size: 20),
                child: Text(d.tecnicoId != null ? 'Chat con el técnico' : 'Chat (se habilita con técnico asignado)'),
              ),
              const SizedBox(height: 20),
              Text('Pago', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 10),
              SolicitudPagoCtaBlock(solicitudId: solicitudId, estado: d.estado),
              const SizedBox(height: 12),
              ShadButton.outline(
                onPressed: () => context.push('/cliente/app/emergencias/solicitudes'),
                child: const Text('Volver a la lista'),
              ),
            ],
          ),
        ),
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
            Text(message, textAlign: TextAlign.center, style: TextStyle(color: Theme.of(context).colorScheme.error)),
            const SizedBox(height: 16),
            ShadButton.outline(onPressed: onRetry, child: const Text('Reintentar')),
          ],
        ),
      ),
    );
  }
}
