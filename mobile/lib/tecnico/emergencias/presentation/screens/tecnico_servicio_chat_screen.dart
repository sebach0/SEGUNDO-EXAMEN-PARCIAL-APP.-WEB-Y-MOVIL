import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../cliente/comunicacion/presentation/widgets/chat_bubble.dart';
import '../../../../cliente/comunicacion/presentation/widgets/chat_composer.dart';
import '../../../application/tecnico_auth_provider.dart';
import '../../application/tecnico_emergencias_providers.dart';
import '../../domain/tecnico_servicio_models.dart';

/// CU35 — mensajes con el cliente de la solicitud asignada.
class TecnicoServicioChatScreen extends ConsumerStatefulWidget {
  const TecnicoServicioChatScreen({
    super.key,
    required this.solicitudId,
    this.initial,
  });

  final int solicitudId;
  final ServicioAsignadoTecnico? initial;

  @override
  ConsumerState<TecnicoServicioChatScreen> createState() => _TecnicoServicioChatScreenState();
}

class _TecnicoServicioChatScreenState extends ConsumerState<TecnicoServicioChatScreen> {
  bool _enviando = false;

  Future<void> _enviar(String texto) async {
    setState(() => _enviando = true);
    try {
      await ref.read(tecnicoEmergenciasRepositoryProvider).enviarMensaje(
            solicitudId: widget.solicitudId,
            texto: texto,
          );
      ref.invalidate(tecnicoMensajesSolicitudProvider(widget.solicitudId));
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString().replaceFirst('Exception: ', ''))),
        );
      }
    } finally {
      if (mounted) setState(() => _enviando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final mensajesAsync = ref.watch(tecnicoMensajesSolicitudProvider(widget.solicitudId));
    final miUsuarioId = ref.watch(tecnicoAuthNotifierProvider).perfil?.usuarioId;
    final listAsync = ref.watch(tecnicoServiciosAsignadosProvider);
    var tituloCliente = widget.initial?.clienteNombreCompleto ?? 'Cliente';
    if (listAsync case AsyncData(:final value)) {
      for (final x in value) {
        if (x.solicitudId == widget.solicitudId) {
          tituloCliente = x.clienteNombreCompleto;
          break;
        }
      }
    }

    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Chat', style: TextStyle(fontSize: 18)),
            Text(
              'Solicitud #${widget.solicitudId} · $tituloCliente',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.85),
                  ),
            ),
          ],
        ),
        leading: BackButton(onPressed: () => context.pop()),
      ),
      body: Column(
        children: [
          Expanded(
            child: mensajesAsync.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => _ErrorChat(
                message: e.toString().replaceFirst('Exception: ', ''),
                onRetry: () => ref.invalidate(tecnicoMensajesSolicitudProvider(widget.solicitudId)),
              ),
              data: (mensajes) {
                if (mensajes.isEmpty) {
                  return _EmptyChat(onRefrescar: () => ref.invalidate(tecnicoMensajesSolicitudProvider(widget.solicitudId)));
                }
                final uid = miUsuarioId;
                return RefreshIndicator(
                  onRefresh: () => ref.refresh(tecnicoMensajesSolicitudProvider(widget.solicitudId).future),
                  child: ListView.builder(
                    padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
                    itemCount: mensajes.length,
                    itemBuilder: (context, i) {
                      final m = mensajes[i];
                      final esMio = uid != null && m.emisorUsuarioId == uid;
                      return Padding(
                        padding: const EdgeInsets.only(bottom: 10),
                        child: ChatBubble(
                          texto: m.mensaje,
                          hora: m.createdAt,
                          esMio: esMio,
                        ),
                      );
                    },
                  ),
                );
              },
            ),
          ),
          ChatComposer(
            habilitado: miUsuarioId != null,
            enviando: _enviando,
            onEnviar: _enviar,
          ),
        ],
      ),
    );
  }
}

class _EmptyChat extends StatelessWidget {
  const _EmptyChat({required this.onRefrescar});

  final VoidCallback onRefrescar;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(28),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.chat_bubble_outline_rounded, size: 52, color: scheme.onSurfaceVariant),
            const SizedBox(height: 16),
            Text(
              'Sin mensajes todavía',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 8),
            Text(
              'Escribí abajo para contactar al cliente sobre este servicio.',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: scheme.onSurface.withValues(alpha: 0.75),
                    height: 1.35,
                  ),
            ),
            const SizedBox(height: 20),
            OutlinedButton.icon(onPressed: onRefrescar, icon: const Icon(Icons.refresh), label: const Text('Actualizar')),
          ],
        ),
      ),
    );
  }
}

class _ErrorChat extends StatelessWidget {
  const _ErrorChat({required this.message, required this.onRetry});

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
            FilledButton.tonal(onPressed: onRetry, child: const Text('Reintentar')),
          ],
        ),
      ),
    );
  }
}
