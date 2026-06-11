import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../cliente/emergencias/domain/solicitud_emergencia_models.dart';
import '../../application/tecnico_emergencias_providers.dart';
import '../../domain/tecnico_servicio_models.dart';

/// CU34 — actualizar estado con transiciones válidas del backend.
class TecnicoServicioActualizarEstadoScreen extends ConsumerStatefulWidget {
  const TecnicoServicioActualizarEstadoScreen({
    super.key,
    required this.solicitudId,
    this.initial,
  });

  final int solicitudId;
  final ServicioAsignadoTecnico? initial;

  @override
  ConsumerState<TecnicoServicioActualizarEstadoScreen> createState() => _TecnicoServicioActualizarEstadoScreenState();
}

class _TecnicoServicioActualizarEstadoScreenState extends ConsumerState<TecnicoServicioActualizarEstadoScreen> {
  final _obsCtrl = TextEditingController();
  EstadoSolicitudEmergencia? _elegido;
  bool _guardando = false;

  @override
  void dispose() {
    _obsCtrl.dispose();
    super.dispose();
  }

  Future<void> _confirmarYGuardar(EstadoSolicitudEmergencia destino) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Confirmar cambio'),
        content: Text('¿Marcar el servicio como “${destino.etiquetaUi}”?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Guardar')),
        ],
      ),
    );
    if (ok != true || !mounted) return;

    setState(() => _guardando = true);
    try {
      final repo = ref.read(tecnicoEmergenciasRepositoryProvider);
      final obs = _obsCtrl.text.trim();
      await repo.actualizarEstado(
        solicitudId: widget.solicitudId,
        nuevoEstado: destino,
        observacion: obs.isEmpty ? null : obs,
      );
      ref.invalidate(tecnicoServiciosAsignadosProvider);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Estado actualizado')));
        context.pop();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString().replaceFirst('Exception: ', ''))),
        );
      }
    } finally {
      if (mounted) setState(() => _guardando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final listAsync = ref.watch(tecnicoServiciosAsignadosProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Actualizar estado'),
        leading: BackButton(onPressed: () => context.pop()),
      ),
      body: listAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text(e.toString())),
        data: (list) {
          ServicioAsignadoTecnico? found;
          for (final x in list) {
            if (x.solicitudId == widget.solicitudId) {
              found = x;
              break;
            }
          }
          final s = found ?? widget.initial;
          if (s == null) {
            return const Center(child: Text('No se encontró el servicio.'));
          }
          final permitidos = estadosDestinoPermitidos(s.estado);
          if (permitidos.isEmpty || s.esTerminal) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text(
                  s.esTerminal
                      ? 'Este servicio ya está cerrado; no se puede cambiar el estado.'
                      : 'No hay transiciones disponibles desde el estado actual.',
                  textAlign: TextAlign.center,
                ),
              ),
            );
          }
          final grupo = (_elegido != null && permitidos.contains(_elegido!)) ? _elegido! : permitidos.first;

          return ListView(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 28),
            children: [
              Text(
                'Estado actual: ${s.estado.etiquetaUi}',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 16),
              Text('Nuevo estado', style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
              const SizedBox(height: 10),
              Wrap(
                spacing: 10,
                runSpacing: 10,
                children: permitidos.map((e) {
                  final selected = grupo == e;
                  return FilterChip(
                    label: Text(etiquetaAccionEstado(e)),
                    selected: selected,
                    onSelected: _guardando
                        ? null
                        : (_) => setState(() => _elegido = e),
                  );
                }).toList(),
              ),
              const SizedBox(height: 16),
              Text('Observación (opcional)', style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
              const SizedBox(height: 8),
              TextField(
                controller: _obsCtrl,
                maxLines: 4,
                maxLength: 2000,
                enabled: !_guardando,
                decoration: const InputDecoration(
                  border: OutlineInputBorder(),
                  hintText: 'Ej.: llegué al punto de encuentro, demora por tráfico…',
                ),
              ),
              const SizedBox(height: 24),
              FilledButton(
                onPressed: _guardando ? null : () => _confirmarYGuardar(grupo),
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  child: Text(_guardando ? 'Guardando…' : 'Guardar cambio', style: const TextStyle(fontSize: 16)),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}
