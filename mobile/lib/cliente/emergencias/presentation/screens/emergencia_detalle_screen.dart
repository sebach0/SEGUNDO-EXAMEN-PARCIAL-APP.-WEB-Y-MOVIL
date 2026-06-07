import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../../pagos/presentation/widgets/solicitud_pago_cta_block.dart';
import '../../application/emergencias_providers.dart';
import '../../domain/solicitud_emergencia_models.dart';
import '../../../../core/utils/eta_format.dart';
import '../widgets/ai/solicitud_ai_resumen_card.dart';
import '../widgets/seguimiento/estado_solicitud_badge.dart';

/// Detalle de una solicitud (API fase 1 + campos fase 2 en JSON).
class EmergenciaDetalleScreen extends ConsumerStatefulWidget {
  const EmergenciaDetalleScreen({super.key, required this.solicitudId});

  final int solicitudId;

  @override
  ConsumerState<EmergenciaDetalleScreen> createState() =>
      _EmergenciaDetalleScreenState();
}

class _EmergenciaDetalleScreenState
    extends ConsumerState<EmergenciaDetalleScreen> {
  @override
  Widget build(BuildContext context) {
    final async = ref.watch(emergenciaDetailProvider(widget.solicitudId));
    final cancelAsync = ref.watch(cancelarSolicitudProvider);

    // Escuchar resultado de la cancelación
    ref.listen<AsyncValue<SolicitudEmergenciaDetail?>>(
      cancelarSolicitudProvider,
      (_, next) {
        if (next is AsyncData && next.value != null) {
          if (!mounted) return;
          ShadToaster.of(context).show(
            const ShadToast(
              title: Text('Solicitud cancelada'),
              description: Text('La solicitud fue cancelada correctamente.'),
            ),
          );
          WidgetsBinding.instance.addPostFrameCallback((_) {
            if (!mounted) return;
            ref.invalidate(emergenciaDetailProvider(widget.solicitudId));
            ref.invalidate(misSolicitudesEmergenciasProvider);
          });
        }
        if (next is AsyncError && mounted) {
          ShadToaster.of(context).show(
            ShadToast.destructive(
              title: const Text('No se pudo cancelar'),
              description: Text(next.error.toString()),
            ),
          );
        }
      },
    );

    return Scaffold(
      appBar: AppBar(
        title: Text('Solicitud #${widget.solicitudId}'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.canPop()
              ? context.pop()
              : context.go('/cliente/app/emergencias/solicitudes'),
        ),
      ),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => _ErrorBody(
          message: e.toString(),
          onRetry: () =>
              ref.invalidate(emergenciaDetailProvider(widget.solicitudId)),
        ),
        data: (d) => RefreshIndicator(
          onRefresh: () =>
              ref.refresh(emergenciaDetailProvider(widget.solicitudId).future),
          child: ListView(
            padding: const EdgeInsets.all(20),
            children: [
              // ── Estado ───────────────────────────────────────────────────
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

              // ── Resumen ───────────────────────────────────────────────────
              Text('Resumen', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              Text(
                'Ubicaciones: ${d.ubicaciones.length} · Evidencias: ${d.evidencias.length}',
                style: TextStyle(
                    color: Theme.of(context).colorScheme.onSurfaceVariant),
              ),
              if (d.descripcionTexto != null &&
                  d.descripcionTexto!.trim().isNotEmpty) ...[
                const SizedBox(height: 16),
                ShadCard(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Text(d.descripcionTexto!),
                  ),
                ),
              ],

              // ── Análisis IA ───────────────────────────────────────────────
              const SizedBox(height: 20),
              Text('Análisis asistido',
                  style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 10),
              SolicitudAiResumenCard(
                payload: d.aiPayload,
                tieneUbicacionServidor: d.ubicaciones.isNotEmpty,
                tieneFotoServidor: d.evidencias
                    .any((e) => e.tipo == TipoEvidenciaSolicitud.foto),
                tieneAudioServidor: d.evidencias
                    .any((e) => e.tipo == TipoEvidenciaSolicitud.audio),
              ),
              if (d.tiempoEstimadoMin != null) ...[
                const SizedBox(height: 12),
                Text(
                  'ETA registrada: ${formatEtaMinutos(d.tiempoEstimadoMin)}.',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],

              // ── Acciones de seguimiento ───────────────────────────────────
              const SizedBox(height: 28),
              ShadButton(
                onPressed: () => context.push(
                  '/cliente/app/emergencias/solicitudes/${widget.solicitudId}/seguimiento',
                ),
                child: const Text('Ver seguimiento completo'),
              ),
              const SizedBox(height: 12),
              ShadButton.outline(
                onPressed: () => context.push(
                  '/cliente/app/emergencias/solicitudes/${widget.solicitudId}/chat',
                ),
                leading: const Icon(Icons.chat_bubble_outline_rounded, size: 20),
                child: Text(d.tecnicoId != null
                    ? 'Chat con el técnico'
                    : 'Chat (se habilita con técnico asignado)'),
              ),

              // ── Cotizaciones ──────────────────────────────────────────────
              const SizedBox(height: 12),
              ShadButton.outline(
                onPressed: () => context.push(
                  '/cliente/app/emergencias/solicitudes/${widget.solicitudId}/cotizaciones',
                ),
                leading: const Icon(Icons.request_quote_outlined, size: 20),
                child: const Text('Comparar ofertas de talleres'),
              ),

              // ── Pago ─────────────────────────────────────────────────────
              const SizedBox(height: 20),
              Text('Pago', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 10),
              SolicitudPagoCtaBlock(
                  solicitudId: widget.solicitudId, estado: d.estado),

              // ── Cancelar solicitud ────────────────────────────────────────
              if (_puedeCancelar(d.estado)) ...[
                const SizedBox(height: 24),
                const Divider(),
                const SizedBox(height: 12),
                ShadButton.destructive(
                  onPressed: cancelAsync.isLoading
                      ? null
                      : () => _mostrarDialogoCancelar(context, widget.solicitudId),
                  leading: cancelAsync.isLoading
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Icon(Icons.cancel_outlined, size: 18),
                  child: const Text('Cancelar solicitud'),
                ),
              ],
              const SizedBox(height: 16),
              ShadButton.outline(
                onPressed: () =>
                    context.push('/cliente/app/emergencias/solicitudes'),
                child: const Text('Volver a la lista'),
              ),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }

  /// Solo se puede cancelar si la solicitud no ha finalizado ni está cancelada.
  bool _puedeCancelar(EstadoSolicitudEmergencia estado) {
    return estado != EstadoSolicitudEmergencia.finalizada &&
        estado != EstadoSolicitudEmergencia.cancelada;
  }

  Future<void> _mostrarDialogoCancelar(
      BuildContext context, int solicitudId) async {
    final motivo = await showDialog<String>(
      context: context,
      builder: (ctx) => const _CancelarSolicitudDialog(),
    );

    if (motivo == null || !mounted) return;

    await ref.read(cancelarSolicitudProvider.notifier).cancelar(
          solicitudId,
          motivo: motivo,
        );
  }
}

class _CancelarSolicitudDialog extends StatefulWidget {
  const _CancelarSolicitudDialog();

  @override
  State<_CancelarSolicitudDialog> createState() =>
      _CancelarSolicitudDialogState();
}

class _CancelarSolicitudDialogState extends State<_CancelarSolicitudDialog> {
  final _controller = TextEditingController();
  final _formKey = GlobalKey<FormState>();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _confirmar() {
    if (!_formKey.currentState!.validate()) return;
    Navigator.pop(context, _controller.text.trim());
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Cancelar solicitud'),
      content: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Esta acción no se puede deshacer. El taller o técnico asignado será notificado.',
              style: TextStyle(fontSize: 13),
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _controller,
              autofocus: true,
              maxLines: 3,
              decoration: const InputDecoration(
                labelText: 'Motivo de cancelación *',
                hintText: 'Ej: Ya no necesito el servicio...',
                border: OutlineInputBorder(),
              ),
              validator: (v) {
                if (v == null || v.trim().isEmpty) {
                  return 'El motivo es obligatorio';
                }
                if (v.trim().length < 5) {
                  return 'Ingresa un motivo más descriptivo';
                }
                return null;
              },
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('No, mantener'),
        ),
        FilledButton(
          style: FilledButton.styleFrom(
            backgroundColor: Theme.of(context).colorScheme.error,
          ),
          onPressed: _confirmar,
          child: const Text('Sí, cancelar'),
        ),
      ],
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
            Text(message,
                textAlign: TextAlign.center,
                style:
                    TextStyle(color: Theme.of(context).colorScheme.error)),
            const SizedBox(height: 16),
            ShadButton.outline(
                onPressed: onRetry, child: const Text('Reintentar')),
          ],
        ),
      ),
    );
  }
}
