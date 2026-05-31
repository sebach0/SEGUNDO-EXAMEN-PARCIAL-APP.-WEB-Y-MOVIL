import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../../../core/utils/bolivia_time.dart';
import '../../../application/cliente_injection.dart';
import '../../application/comunicacion_providers.dart';
import '../../domain/notificacion_models.dart';

/// Detalle de una notificación; marca como leída al abrir (CU19).
class NotificacionDetalleScreen extends ConsumerStatefulWidget {
  const NotificacionDetalleScreen({
    super.key,
    required this.notificacionId,
    this.initial,
  });

  final int notificacionId;
  final NotificacionRead? initial;

  @override
  ConsumerState<NotificacionDetalleScreen> createState() => _NotificacionDetalleScreenState();
}

class _NotificacionDetalleScreenState extends ConsumerState<NotificacionDetalleScreen> {
  bool _marcando = false;
  String? _marcarError;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _marcarSiCorresponde());
  }

  Future<void> _marcarSiCorresponde() async {
    final n = widget.initial;
    if (n == null || n.id != widget.notificacionId || n.leida || _marcando) return;
    setState(() {
      _marcando = true;
      _marcarError = null;
    });
    try {
      final repo = ref.read(comunicacionRepositoryProvider);
      await repo.marcarNotificacionLeida(n.id);
      ref.invalidate(notificacionesClienteProvider(false));
      ref.invalidate(notificacionesClienteProvider(true));
    } catch (e) {
      if (mounted) setState(() => _marcarError = e.toString());
    } finally {
      if (mounted) setState(() => _marcando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = ShadTheme.of(context);
    final initial = widget.initial;

    if (initial != null && initial.id == widget.notificacionId) {
      return _buildScaffold(context, theme, initial);
    }

    return FutureBuilder<NotificacionRead?>(
      future: ref.read(comunicacionRepositoryProvider).obtenerNotificacionPorId(widget.notificacionId),
      builder: (context, snap) {
        if (snap.connectionState != ConnectionState.done) {
          return const Scaffold(body: Center(child: CircularProgressIndicator()));
        }
        final n = snap.data;
        if (n == null) {
          return Scaffold(
            appBar: AppBar(title: const Text('Notificación')),
            body: Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text('No se encontró la notificación.', style: theme.textTheme.large),
                    const SizedBox(height: 16),
                    ShadButton.outline(onPressed: () => context.pop(), child: const Text('Volver')),
                  ],
                ),
              ),
            ),
          );
        }
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (mounted && !n.leida) _marcarSiCorrespondeFor(n);
        });
        return _buildScaffold(context, theme, n);
      },
    );
  }

  Future<void> _marcarSiCorrespondeFor(NotificacionRead n) async {
    if (n.leida || _marcando) return;
    setState(() {
      _marcando = true;
      _marcarError = null;
    });
    try {
      await ref.read(comunicacionRepositoryProvider).marcarNotificacionLeida(n.id);
      ref.invalidate(notificacionesClienteProvider(false));
      ref.invalidate(notificacionesClienteProvider(true));
    } catch (e) {
      if (mounted) setState(() => _marcarError = e.toString());
    } finally {
      if (mounted) setState(() => _marcando = false);
    }
  }

  Widget _buildScaffold(BuildContext context, ShadThemeData theme, NotificacionRead n) {
    final fecha = BoliviaTime.formatWithZone(n.createdAt);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Detalle'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.pop(),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          if (_marcarError != null) ...[
            ShadAlert.destructive(
              title: const Text('No se pudo marcar como leída'),
              description: Text(_marcarError!),
            ),
            const SizedBox(height: 16),
          ],
          Text(n.titulo, style: theme.textTheme.h4),
          const SizedBox(height: 8),
          Text(fecha, style: theme.textTheme.muted),
          const SizedBox(height: 20),
          ShadCard(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Text(n.mensaje, style: theme.textTheme.p),
            ),
          ),
          if (n.solicitudId != null) ...[
            const SizedBox(height: 20),
            ShadButton.outline(
              onPressed: () => context.push('/cliente/app/emergencias/solicitudes/${n.solicitudId}'),
              child: Text('Ver solicitud #${n.solicitudId}'),
            ),
            const SizedBox(height: 8),
            ShadButton(
              onPressed: () => context.push('/cliente/app/emergencias/solicitudes/${n.solicitudId}/chat'),
              child: const Text('Abrir chat de la solicitud'),
            ),
          ],
        ],
      ),
    );
  }
}
