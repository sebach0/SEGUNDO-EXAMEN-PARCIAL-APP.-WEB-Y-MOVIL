import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../cliente/emergencias/domain/solicitud_emergencia_models.dart'
    show EstadoSolicitudEmergencia;
import '../../application/tecnico_emergencias_providers.dart';
import '../../domain/tecnico_servicio_models.dart';

class TecnicoEditarCotizacionScreen extends ConsumerStatefulWidget {
  const TecnicoEditarCotizacionScreen({
    super.key,
    required this.solicitudId,
    this.comprobante,
  });

  final int solicitudId;
  final ComprobanteTecnico? comprobante;

  @override
  ConsumerState<TecnicoEditarCotizacionScreen> createState() =>
      _TecnicoEditarCotizacionScreenState();
}

class _TecnicoEditarCotizacionScreenState
    extends ConsumerState<TecnicoEditarCotizacionScreen> {
  late final List<_ItemEditable> _items;
  bool _guardando = false;
  String? _error;
  int _nextId = 0;

  @override
  void initState() {
    super.initState();
    final comp = widget.comprobante;
    _items = comp != null
        ? comp.cotizacionItems
            .map((i) => _ItemEditable(
                  localId: _nextId++,
                  descripcion: i.descripcion,
                  cantidad: i.cantidad,
                  precioUnitario: i.precioUnitario,
                ))
            .toList()
        : [];
  }

  double get _total => _items.fold(0.0, (s, i) => s + i.subtotal);

  Future<void> _guardar() async {
    if (_items.isEmpty) {
      setState(() => _error = 'La cotización debe tener al menos un ítem.');
      return;
    }
    setState(() {
      _guardando = true;
      _error = null;
    });
    try {
      final repo = ref.read(tecnicoEmergenciasRepositoryProvider);
      await repo.actualizarItemsCotizacion(
        widget.solicitudId,
        _items
            .map((i) => {
                  'descripcion': i.descripcion,
                  'cantidad': i.cantidad,
                  'precio_unitario': i.precioUnitario,
                })
            .toList(),
      );
      ref.invalidate(tecnicoComprobanteSolicitudProvider(widget.solicitudId));
      if (mounted) context.pop();
    } catch (e) {
      if (mounted) setState(() => _error = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _guardando = false);
    }
  }

  Future<void> _mostrarFormAgregar() async {
    final item = await showModalBottomSheet<_ItemEditable>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (_) => const _AgregarItemSheet(),
    );
    if (item != null && mounted) {
      setState(() => _items.add(item.copyWith(localId: _nextId++)));
    }
  }

  /// Devuelve null si se puede editar, o un mensaje de bloqueo si no.
  String? get _bloqueadoPorque {
    final comp = widget.comprobante;
    if (comp == null) return null; // sin datos aún, dejamos que intente
    if (comp.cotizacionId == null) {
      return 'Este servicio no tiene una cotización aceptada.\n\n'
          'El editor de ítems requiere que el cliente haya aceptado '
          'la cotización del taller. Si el servicio se asignó directamente '
          'sin una cotización, coordiná el detalle con el taller.';
    }
    if (comp.estado != EstadoSolicitudEmergencia.enAtencion) {
      return 'Solo podés editar los ítems cuando el servicio está '
          'en estado "En Atención".\n\n'
          'Estado actual: ${comp.estado.etiquetaUi}';
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final tt = Theme.of(context).textTheme;

    final bloqueado = _bloqueadoPorque;

    return Scaffold(
      appBar: AppBar(
        title: Text('Editar cotización #${widget.solicitudId}'),
        leading: BackButton(onPressed: () => context.pop()),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 8),
            child: bloqueado != null
                ? const SizedBox.shrink()
                : _guardando
                ? Center(
                    child: SizedBox(
                      width: 22,
                      height: 22,
                      child: CircularProgressIndicator(
                          strokeWidth: 2.5, color: scheme.primary),
                    ),
                  )
                : TextButton(
                    onPressed: _guardar,
                    child: const Text('Guardar',
                        style: TextStyle(fontWeight: FontWeight.w700)),
                  ),
          ),
        ],
      ),
      body: bloqueado != null
          ? Center(
              child: Padding(
                padding: const EdgeInsets.all(28),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.lock_outline_rounded,
                        size: 52, color: scheme.onSurfaceVariant.withValues(alpha: 0.5)),
                    const SizedBox(height: 16),
                    Text(
                      bloqueado,
                      textAlign: TextAlign.center,
                      style: tt.bodyMedium?.copyWith(
                          color: scheme.onSurfaceVariant, height: 1.5),
                    ),
                    const SizedBox(height: 20),
                    OutlinedButton(
                      onPressed: () => context.pop(),
                      child: const Text('Volver'),
                    ),
                  ],
                ),
              ),
            )
          : Column(
        children: [
          Expanded(
            child: _items.isEmpty
                ? Center(
                    child: Padding(
                      padding: const EdgeInsets.all(32),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.playlist_add_rounded,
                              size: 52, color: scheme.onSurfaceVariant.withValues(alpha: 0.4)),
                          const SizedBox(height: 12),
                          Text(
                            'Sin ítems aún.\nAgregá piezas, repuestos o mano de obra.',
                            textAlign: TextAlign.center,
                            style: tt.bodyMedium?.copyWith(
                                color: scheme.onSurfaceVariant, height: 1.45),
                          ),
                        ],
                      ),
                    ),
                  )
                : ReorderableListView.builder(
                    padding: const EdgeInsets.fromLTRB(14, 10, 14, 4),
                    onReorderItem: (oldIndex, newIndex) {
                      setState(() {
                        final item = _items.removeAt(oldIndex);
                        _items.insert(newIndex, item);
                      });
                    },
                    itemCount: _items.length,
                    itemBuilder: (context, i) {
                      final item = _items[i];
                      return Card(
                        key: ValueKey(item.localId),
                        margin: const EdgeInsets.only(bottom: 8),
                        child: ListTile(
                          contentPadding:
                              const EdgeInsets.symmetric(horizontal: 14, vertical: 2),
                          title: Text(item.descripcion,
                              style: tt.bodyMedium?.copyWith(fontWeight: FontWeight.w500)),
                          subtitle: Text(
                            'Cant: ${_fmtNum(item.cantidad)}  ×  Bs. ${item.precioUnitario.toStringAsFixed(2)}',
                            style: tt.bodySmall?.copyWith(color: scheme.onSurfaceVariant),
                          ),
                          trailing: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(
                                'Bs. ${item.subtotal.toStringAsFixed(2)}',
                                style: tt.bodyMedium
                                    ?.copyWith(fontWeight: FontWeight.w700),
                              ),
                              const SizedBox(width: 4),
                              IconButton(
                                icon: Icon(Icons.delete_outline_rounded,
                                    color: scheme.error, size: 22),
                                tooltip: 'Eliminar',
                                onPressed: _guardando
                                    ? null
                                    : () => setState(
                                        () => _items.removeAt(i)),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
          ),

          // ── Barra de total ─────────────────────────────────────────────────
          if (_items.isNotEmpty)
            ColoredBox(
              color: scheme.primaryContainer,
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('NUEVO TOTAL',
                        style: tt.titleSmall?.copyWith(
                            color: scheme.onPrimaryContainer,
                            fontWeight: FontWeight.w800)),
                    Text(
                      'Bs. ${_total.toStringAsFixed(2)}',
                      style: tt.titleMedium?.copyWith(
                          color: scheme.primary, fontWeight: FontWeight.w900),
                    ),
                  ],
                ),
              ),
            ),

          // ── Error ──────────────────────────────────────────────────────────
          if (_error != null)
            ColoredBox(
              color: scheme.errorContainer,
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                child: Row(
                  children: [
                    Icon(Icons.error_outline_rounded, color: scheme.error, size: 18),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(_error!,
                          style: tt.bodySmall?.copyWith(color: scheme.onErrorContainer)),
                    ),
                  ],
                ),
              ),
            ),

          // ── Botón agregar ──────────────────────────────────────────────────
          Padding(
            padding: EdgeInsets.fromLTRB(
              16,
              10,
              16,
              MediaQuery.of(context).padding.bottom + 12,
            ),
            child: OutlinedButton.icon(
              onPressed: _guardando ? null : _mostrarFormAgregar,
              icon: const Icon(Icons.add_rounded),
              label: const Text('Agregar ítem'),
              style: OutlinedButton.styleFrom(
                minimumSize: const Size.fromHeight(48),
              ),
            ),
          ),
        ],
      ),
    );
  }

  static String _fmtNum(double v) =>
      v % 1 == 0 ? v.toInt().toString() : v.toStringAsFixed(2);
}

// ── Modelo editable local ─────────────────────────────────────────────────────

class _ItemEditable {
  const _ItemEditable({
    required this.localId,
    required this.descripcion,
    required this.cantidad,
    required this.precioUnitario,
  });

  final int localId;
  final String descripcion;
  final double cantidad;
  final double precioUnitario;

  double get subtotal => cantidad * precioUnitario;

  _ItemEditable copyWith({
    int? localId,
    String? descripcion,
    double? cantidad,
    double? precioUnitario,
  }) =>
      _ItemEditable(
        localId: localId ?? this.localId,
        descripcion: descripcion ?? this.descripcion,
        cantidad: cantidad ?? this.cantidad,
        precioUnitario: precioUnitario ?? this.precioUnitario,
      );
}

// ── Bottom sheet: agregar ítem ────────────────────────────────────────────────

class _AgregarItemSheet extends StatefulWidget {
  const _AgregarItemSheet();

  @override
  State<_AgregarItemSheet> createState() => _AgregarItemSheetState();
}

class _AgregarItemSheetState extends State<_AgregarItemSheet> {
  final _formKey = GlobalKey<FormState>();
  final _descCtrl = TextEditingController();
  final _cantCtrl = TextEditingController(text: '1');
  final _precioCtrl = TextEditingController();

  double get _subtotalPreview {
    final c = double.tryParse(_cantCtrl.text) ?? 0;
    final p = double.tryParse(_precioCtrl.text) ?? 0;
    return c * p;
  }

  @override
  void dispose() {
    _descCtrl.dispose();
    _cantCtrl.dispose();
    _precioCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final tt = Theme.of(context).textTheme;
    final bottom = MediaQuery.of(context).viewInsets.bottom;

    return Padding(
      padding: EdgeInsets.fromLTRB(20, 24, 20, bottom + 24),
      child: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Handle bar
            Center(
              child: Container(
                width: 40,
                height: 4,
                margin: const EdgeInsets.only(bottom: 20),
                decoration: BoxDecoration(
                  color: scheme.onSurfaceVariant.withValues(alpha: 0.3),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            Text('Nuevo ítem',
                style: tt.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
            const SizedBox(height: 16),
            TextFormField(
              controller: _descCtrl,
              decoration: const InputDecoration(
                labelText: 'Descripción *',
                hintText: 'Ej: Cambio de correa de distribución',
                border: OutlineInputBorder(),
              ),
              textCapitalization: TextCapitalization.sentences,
              autofocus: true,
              validator: (v) =>
                  (v == null || v.trim().isEmpty) ? 'Ingresá una descripción' : null,
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  flex: 2,
                  child: TextFormField(
                    controller: _cantCtrl,
                    decoration: const InputDecoration(
                      labelText: 'Cantidad *',
                      border: OutlineInputBorder(),
                    ),
                    keyboardType:
                        const TextInputType.numberWithOptions(decimal: true),
                    onChanged: (_) => setState(() {}),
                    validator: (v) {
                      final n = double.tryParse(v ?? '');
                      if (n == null || n <= 0) return '> 0';
                      return null;
                    },
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  flex: 3,
                  child: TextFormField(
                    controller: _precioCtrl,
                    decoration: const InputDecoration(
                      labelText: 'Precio unit. (Bs.) *',
                      border: OutlineInputBorder(),
                    ),
                    keyboardType:
                        const TextInputType.numberWithOptions(decimal: true),
                    onChanged: (_) => setState(() {}),
                    validator: (v) {
                      final n = double.tryParse(v ?? '');
                      if (n == null || n < 0) return 'Valor inválido';
                      return null;
                    },
                  ),
                ),
              ],
            ),
            if (_subtotalPreview > 0) ...[
              const SizedBox(height: 10),
              Align(
                alignment: Alignment.centerRight,
                child: Text(
                  'Subtotal: Bs. ${_subtotalPreview.toStringAsFixed(2)}',
                  style: tt.bodyMedium?.copyWith(
                      color: scheme.primary, fontWeight: FontWeight.w600),
                ),
              ),
            ],
            const SizedBox(height: 18),
            FilledButton.icon(
              icon: const Icon(Icons.add_rounded),
              label: const Text('Agregar ítem',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
              style: FilledButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 14)),
              onPressed: () {
                if (_formKey.currentState!.validate()) {
                  Navigator.pop(
                    context,
                    _ItemEditable(
                      localId: 0,
                      descripcion: _descCtrl.text.trim(),
                      cantidad: double.parse(_cantCtrl.text),
                      precioUnitario: double.parse(_precioCtrl.text),
                    ),
                  );
                }
              },
            ),
          ],
        ),
      ),
    );
  }
}
