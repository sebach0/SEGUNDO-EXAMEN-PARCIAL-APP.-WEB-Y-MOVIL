import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../../application/client_auth_provider.dart';
import '../../../application/cliente_injection.dart';
import '../../application/comunicacion_providers.dart';
import '../../../emergencias/application/emergencias_providers.dart';
import '../widgets/chat_bubble.dart';
import '../widgets/chat_composer.dart';
import '../widgets/solicitud_chat_header.dart';

/// CU21 — chat ligado a una solicitud (REST).
class ChatSolicitudScreen extends ConsumerStatefulWidget {
  const ChatSolicitudScreen({super.key, required this.solicitudId});

  final int solicitudId;

  @override
  ConsumerState<ChatSolicitudScreen> createState() => _ChatSolicitudScreenState();
}

class _ChatSolicitudScreenState extends ConsumerState<ChatSolicitudScreen> {
  bool _enviando = false;

  Future<void> _enviar(String texto) async {
    setState(() => _enviando = true);
    try {
      await ref.read(comunicacionRepositoryProvider).enviarMensaje(
            solicitudId: widget.solicitudId,
            texto: texto,
          );
      ref.invalidate(mensajesSolicitudProvider(widget.solicitudId));
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
    final detalleAsync = ref.watch(emergenciaDetailProvider(widget.solicitudId));
    final mensajesAsync = ref.watch(mensajesSolicitudProvider(widget.solicitudId));
    final miUsuarioId = ref.watch(clientAuthNotifierProvider).profile?.usuarioId;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Chat con el taller'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.canPop() ? context.pop() : context.go('/cliente/app/emergencias/solicitudes/${widget.solicitudId}'),
        ),
      ),
      body: detalleAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => _ErrorChat(
          message: e.toString(),
          onRetry: () => ref.invalidate(emergenciaDetailProvider(widget.solicitudId)),
        ),
        data: (detalle) {
          final sinTecnico = detalle.tecnicoId == null;
          final theme = ShadTheme.of(context);

          return Column(
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
                child: SolicitudChatHeader(
                  solicitudId: widget.solicitudId,
                  estado: detalle.estado,
                  subtitulo: sinTecnico
                      ? 'Cuando se asigne un técnico podrás enviar mensajes.'
                      : 'Conversación con el técnico asignado.',
                ),
              ),
              Expanded(
                child: mensajesAsync.when(
                  loading: () => const Center(child: CircularProgressIndicator()),
                  error: (e, _) => _ErrorChat(
                    message: e.toString(),
                    onRetry: () => ref.invalidate(mensajesSolicitudProvider(widget.solicitudId)),
                  ),
                  data: (mensajes) {
                    if (sinTecnico) {
                      return _EmptySinTecnico(theme: theme);
                    }
                    if (mensajes.isEmpty) {
                      return _EmptySinMensajes(
                        theme: theme,
                        onRefrescar: () => ref.invalidate(mensajesSolicitudProvider(widget.solicitudId)),
                      );
                    }
                    final uid = miUsuarioId;
                    return RefreshIndicator(
                      onRefresh: () => ref.refresh(mensajesSolicitudProvider(widget.solicitudId).future),
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
              if (!sinTecnico)
                ChatComposer(
                  habilitado: miUsuarioId != null,
                  enviando: _enviando,
                  onEnviar: _enviar,
                ),
            ],
          );
        },
      ),
    );
  }
}

class _EmptySinTecnico extends StatelessWidget {
  const _EmptySinTecnico({required this.theme});

  final ShadThemeData theme;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(28),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.support_agent_outlined, size: 52, color: theme.colorScheme.mutedForeground),
            const SizedBox(height: 16),
            Text('Aún no hay técnico asignado', textAlign: TextAlign.center, style: theme.textTheme.large),
            const SizedBox(height: 8),
            Text(
              'El chat se habilita cuando el taller asigna un técnico a tu solicitud.',
              textAlign: TextAlign.center,
              style: theme.textTheme.muted,
            ),
          ],
        ),
      ),
    );
  }
}

class _EmptySinMensajes extends StatelessWidget {
  const _EmptySinMensajes({required this.theme, required this.onRefrescar});

  final ShadThemeData theme;
  final VoidCallback onRefrescar;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(28),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.chat_bubble_outline_rounded, size: 52, color: theme.colorScheme.mutedForeground),
            const SizedBox(height: 16),
            Text('Sin mensajes todavía', textAlign: TextAlign.center, style: theme.textTheme.large),
            const SizedBox(height: 8),
            Text(
              'Escribí abajo para iniciar la conversación con el técnico.',
              textAlign: TextAlign.center,
              style: theme.textTheme.muted,
            ),
            const SizedBox(height: 20),
            ShadButton.outline(onPressed: onRefrescar, child: const Text('Actualizar')),
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
            ShadButton.outline(onPressed: onRetry, child: const Text('Reintentar')),
          ],
        ),
      ),
    );
  }
}
