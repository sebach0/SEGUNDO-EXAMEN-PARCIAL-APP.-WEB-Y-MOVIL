import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../../../core/utils/bolivia_time.dart';
import '../../../pagos/presentation/widgets/solicitud_pago_cta_block.dart';
import '../../application/emergencias_providers.dart';
import '../../application/emergencia_ws_provider.dart';
import '../../data/emergencia_ws_service.dart';
import '../widgets/seguimiento/estado_solicitud_badge.dart';
import '../widgets/ai/solicitud_ai_resumen_card.dart';
import '../widgets/seguimiento/eta_llegada_card.dart';
import '../widgets/seguimiento/seguimiento_timeline.dart';
import '../widgets/seguimiento/taller_asignado_card.dart';
import '../widgets/seguimiento/tecnico_asignado_card.dart';

/// Seguimiento de solicitud: estado, taller, técnico, ETA, historial.
/// Ciclo 4 — Auto-actualización vía WebSocket (sin pull-to-refresh manual).
class EmergenciaSeguimientoScreen extends ConsumerStatefulWidget {
  const EmergenciaSeguimientoScreen({super.key, required this.solicitudId});

  final int solicitudId;

  @override
  ConsumerState<EmergenciaSeguimientoScreen> createState() =>
      _EmergenciaSeguimientoScreenState();
}

class _EmergenciaSeguimientoScreenState
    extends ConsumerState<EmergenciaSeguimientoScreen> {
  // Etiqueta del último evento WS para feedback visual
  String? _wsEventLabel;

  @override
  Widget build(BuildContext context) {
    final seguimientoAsync =
        ref.watch(emergenciaSeguimientoProvider(widget.solicitudId));

    // Escuchar WS: cuando llega un evento relevante, invalidar el provider
    // de seguimiento para que se recargue desde el backend.
    ref.listen<AsyncValue<WsSolicitudEvent>>(
      emergenciaWsProvider(widget.solicitudId),
      (_, next) {
        next.whenData((event) {
          const relevantes = {
            'ESTADO_CAMBIADO',
            'ETA_ACTUALIZADO',
            'SERVICIO_RETRASADO',
            'TALLER_ACEPTO',
            'TALLER_RECHAZO',
            'AUXILIO_EN_CAMINO',
            'SERVICIO_ATENDIDO',
            'SERVICIO_FINALIZADO',
          };
          if (relevantes.contains(event.type)) {
            // Forzar recarga del seguimiento
            ref.invalidate(emergenciaSeguimientoProvider(widget.solicitudId));
            if (mounted) {
              setState(() => _wsEventLabel = _labelParaEvento(event));
              // Limpiar el badge después de 4 s
              Future.delayed(const Duration(seconds: 4), () {
                if (mounted) setState(() => _wsEventLabel = null);
              });
            }
          }
        });
      },
    );

    // Estado de la conexión WS (solo para feedback visual)
    final wsState = ref.watch(emergenciaWsProvider(widget.solicitudId));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Seguimiento'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.canPop()
              ? context.pop()
              : context.go(
                  '/cliente/app/emergencias/solicitudes/${widget.solicitudId}'),
        ),
        actions: [
          // Indicador de estado WS
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: _WsStatusDot(wsState: wsState),
          ),
        ],
      ),
      body: Column(
        children: [
          // Banner de último evento WS
          if (_wsEventLabel != null)
            Container(
              width: double.infinity,
              color: Theme.of(context).colorScheme.primaryContainer,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Row(
                children: [
                  Icon(Icons.bolt,
                      size: 16,
                      color: Theme.of(context).colorScheme.primary),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      _wsEventLabel!,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: Theme.of(context).colorScheme.onPrimaryContainer,
                            fontWeight: FontWeight.w600,
                          ),
                    ),
                  ),
                ],
              ),
            ),
          Expanded(
            child: seguimientoAsync.when(
              loading: () =>
                  const Center(child: CircularProgressIndicator()),
              error: (e, _) => _ErrorBody(
                message: e.toString(),
                onRetry: () => ref.invalidate(
                    emergenciaSeguimientoProvider(widget.solicitudId)),
              ),
              data: (s) => RefreshIndicator(
                onRefresh: () => ref
                    .refresh(
                        emergenciaSeguimientoProvider(widget.solicitudId)
                            .future)
                    .then((_) => null),
                child: ListView(
                  padding: const EdgeInsets.all(20),
                  children: [
                    Text('Solicitud #${s.solicitudId}',
                        style: Theme.of(context).textTheme.headlineSmall),
                    const SizedBox(height: 12),
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        Text('Estado actual',
                            style:
                                Theme.of(context).textTheme.titleSmall),
                        const SizedBox(width: 10),
                        EstadoSolicitudBadge(estado: s.estado),
                      ],
                    ),
                    const SizedBox(height: 20),
                    Text('Tiempo estimado',
                        style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 10),
                    EtaLlegadaCard(
                      minutos: s.tiempoEstimadoMin,
                      actualizadoEn: s.updatedAt,
                      minutosRetraso: s.minutosRetraso,
                      servicioRetrasado: s.servicioRetrasado,
                      etaOrigen: s.etaOrigen,
                    ),
                    const SizedBox(height: 20),
                    Text('Análisis asistido (IA)',
                        style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 10),
                    SolicitudAiResumenCard(
                      payload: s.aiPayload,
                      tieneUbicacionServidor: s.tieneUbicacionCliente,
                      tieneFotoServidor: s.tieneEvidenciaFoto,
                      tieneAudioServidor: s.tieneEvidenciaAudio,
                    ),
                    const SizedBox(height: 24),
                    Text('Taller',
                        style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 10),
                    if (s.taller == null)
                      const _InfoPlaceholder(
                        icon: Icons.store_outlined,
                        text:
                            'Todavía no hay taller asignado a esta solicitud.',
                      )
                    else
                      TallerAsignadoCard(taller: s.taller!),
                    const SizedBox(height: 24),
                    Text('Técnico',
                        style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 10),
                    if (s.tecnico == null)
                      const _InfoPlaceholder(
                        icon: Icons.person_outline,
                        text:
                            'Sin técnico asignado. Se mostrará cuando el taller designe movilización.',
                      )
                    else
                      TecnicoAsignadoCard(tecnico: s.tecnico!),
                    if (s.tecnico != null) ...[
                      const SizedBox(height: 16),
                      ShadButton(
                        onPressed: () => context.push(
                            '/cliente/app/emergencias/solicitudes/${widget.solicitudId}/chat'),
                        leading: const Icon(
                            Icons.chat_bubble_outline_rounded,
                            size: 20),
                        child: const Text('Abrir chat con el técnico'),
                      ),
                      const SizedBox(height: 10),
                      ShadButton.outline(
                        onPressed: () => context.push(
                            '/cliente/app/emergencias/solicitudes/${widget.solicitudId}/ubicacion-tecnico'),
                        leading: const Icon(
                            Icons.engineering_outlined,
                            size: 20),
                        child:
                            const Text('Ver ubicación del técnico'),
                      ),
                    ],
                    if (s.presupuestoBob != null) ...[
                      const SizedBox(height: 24),
                      Text('Presupuesto en sitio',
                          style:
                              Theme.of(context).textTheme.titleMedium),
                      const SizedBox(height: 10),
                      ShadCard(
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment:
                                CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Bs. ${s.presupuestoBob!.toStringAsFixed(2)}',
                                style: Theme.of(context)
                                    .textTheme
                                    .headlineSmall
                                    ?.copyWith(
                                      fontWeight: FontWeight.w800,
                                      color: Theme.of(context)
                                          .colorScheme
                                          .primary,
                                    ),
                              ),
                              if (s.presupuestoRegistradoAt != null) ...[
                                const SizedBox(height: 8),
                                Text(
                                  'Registrado: ${BoliviaTime.formatWithZone(s.presupuestoRegistradoAt!, pattern: 'dd/MM/yyyy HH:mm')}',
                                  style: Theme.of(context)
                                      .textTheme
                                      .bodySmall
                                      ?.copyWith(
                                        color: Theme.of(context)
                                            .colorScheme
                                            .onSurfaceVariant,
                                      ),
                                ),
                              ],
                              const SizedBox(height: 8),
                              Text(
                                'Monto indicado por el técnico al iniciar la atención. El pago formal sigue en la sección de abajo.',
                                style: Theme.of(context)
                                    .textTheme
                                    .bodySmall,
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                    const SizedBox(height: 24),
                    Text('Historial de estado',
                        style:
                            Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 10),
                    ShadCard(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: SeguimientoTimeline(
                            items: s.historialEstados),
                      ),
                    ),
                    const SizedBox(height: 24),
                    Text('Pago del servicio',
                        style:
                            Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 10),
                    SolicitudPagoCtaBlock(
                        solicitudId: widget.solicitudId,
                        estado: s.estado),
                    const SizedBox(height: 24),
                    ShadButton.outline(
                      onPressed: () => context.push(
                          '/cliente/app/emergencias/solicitudes/${widget.solicitudId}'),
                      child:
                          const Text('Ver detalle de la solicitud'),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  String _labelParaEvento(WsSolicitudEvent event) {
    return switch (event.type) {
      'ESTADO_CAMBIADO' =>
        '📡 Estado actualizado: ${event.status ?? event.type}',
      'ETA_ACTUALIZADO' => '⏱ ETA actualizado en tiempo real',
      'SERVICIO_RETRASADO' => '⚠️ Servicio con retraso detectado',
      'TALLER_ACEPTO' => '✅ Taller confirmó la atención',
      'TALLER_RECHAZO' => '❌ Taller no pudo atender',
      'AUXILIO_EN_CAMINO' => '🚗 El auxilio está en camino',
      'SERVICIO_ATENDIDO' => '🔧 Técnico atendiendo el vehículo',
      'SERVICIO_FINALIZADO' => '🏁 Servicio finalizado',
      _ => '📡 Actualización recibida: ${event.type}',
    };
  }
}

class _InfoPlaceholder extends StatelessWidget {
  const _InfoPlaceholder({required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return ShadCard(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: scheme.onSurfaceVariant),
            const SizedBox(width: 12),
            Expanded(child: Text(text, style: TextStyle(color: scheme.onSurfaceVariant, height: 1.4))),
          ],
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

/// Pequeño punto indicador del estado de la conexión WebSocket.
class _WsStatusDot extends StatelessWidget {
  const _WsStatusDot({required this.wsState});

  final AsyncValue<WsSolicitudEvent> wsState;

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: wsState.isLoading
          ? 'Conectando al feed en tiempo real…'
          : wsState.hasError
              ? 'Sin conexión en tiempo real'
              : 'Tiempo real activo',
      child: Icon(
        Icons.circle,
        size: 12,
        color: wsState.isLoading
            ? Colors.amber
            : wsState.hasError
                ? Colors.grey
                : Colors.green,
      ),
    );
  }
}
