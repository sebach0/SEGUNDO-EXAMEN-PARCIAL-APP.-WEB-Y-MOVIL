import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../application/cliente_injection.dart';
import '../../application/vehiculos_providers.dart';
import '../../data/repositories/vehiculo_repository.dart';
import '../../domain/models/vehiculo_display.dart';

class ClienteVehiculosListScreen extends ConsumerWidget {
  const ClienteVehiculosListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(vehiculosMineProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Mis vehículos'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            tooltip: 'Registrar',
            onPressed: () => context.push('/cliente/app/vehiculos/nuevo'),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(vehiculosMineProvider),
        child: async.when(
          loading: () => ListView(
                children: const [
                  SizedBox(height: 120),
                  Center(child: CircularProgressIndicator()),
                ],
              ),
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
                  Icon(Icons.directions_car_outlined, size: 56, color: Theme.of(context).colorScheme.outline),
                  const SizedBox(height: 16),
                  Text(
                    'Aún no tienes vehículos',
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Registra tu primer vehículo con placa, marca y modelo.',
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
            return ListView.separated(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.all(16),
              itemCount: items.length,
              separatorBuilder: (_, __) => const SizedBox(height: 10),
              itemBuilder: (context, i) {
                final v = items[i];
                return ShadCard(
                  child: Padding(
                    padding: const EdgeInsets.all(14),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                v.placa,
                                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                      fontWeight: FontWeight.bold,
                                      letterSpacing: 1.1,
                                    ),
                              ),
                            ),
                            Text(v.tipoNombre, style: Theme.of(context).textTheme.labelMedium),
                          ],
                        ),
                        const SizedBox(height: 6),
                        Text('${v.marcaNombre} · ${v.modeloNombre}', style: Theme.of(context).textTheme.bodyMedium),
                        if (v.anio != null || (v.color != null && v.color!.isNotEmpty))
                          Text(
                            [
                              if (v.anio != null) 'Año ${v.anio}',
                              if (v.color != null && v.color!.isNotEmpty) v.color!,
                            ].join(' · '),
                            style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant, fontSize: 12),
                          ),
                        const SizedBox(height: 12),
                        Row(
                          children: [
                            TextButton(
                              onPressed: () => context.push('/cliente/app/vehiculos/${v.id}'),
                              child: const Text('Ver'),
                            ),
                            TextButton(
                              onPressed: () => context.push('/cliente/app/vehiculos/${v.id}/editar'),
                              child: const Text('Editar'),
                            ),
                            TextButton(
                              onPressed: () => _confirmDeletePlaceholder(context),
                              child: const Text('Eliminar'),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                );
              },
            );
          },
        ),
      ),
    );
  }

  void _confirmDeletePlaceholder(BuildContext context) {
    showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Eliminar vehículo'),
        content: const Text(
          'La eliminación desde la app se habilitará cuando el backend exponga el endpoint. '
          'Por ahora puedes editar los datos del vehículo.',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cerrar')),
        ],
      ),
    );
  }
}

class ClienteVehiculoDetailScreen extends ConsumerStatefulWidget {
  const ClienteVehiculoDetailScreen({super.key, required this.vehiculoId});

  final int vehiculoId;

  @override
  ConsumerState<ClienteVehiculoDetailScreen> createState() => _ClienteVehiculoDetailScreenState();
}

class _ClienteVehiculoDetailScreenState extends ConsumerState<ClienteVehiculoDetailScreen> {
  late Future<VehiculoDisplay> _future;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() {
    _future = ref.read(vehiculoRepositoryProvider).fetchDisplay(widget.vehiculoId);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Detalle vehículo'),
        actions: [
          IconButton(
            icon: const Icon(Icons.edit),
            onPressed: () => context.push('/cliente/app/vehiculos/${widget.vehiculoId}/editar'),
          ),
        ],
      ),
      body: FutureBuilder<VehiculoDisplay>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snap.hasError) {
            return Center(child: Text(snap.error.toString()));
          }
          final v = snap.data!;
          return ListView(
            padding: const EdgeInsets.all(20),
            children: [
              Text(v.placa, style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold)),
              const SizedBox(height: 16),
              _row('Marca', v.marcaNombre),
              _row('Modelo', v.modeloNombre),
              _row('Tipo', v.tipoNombre),
              if (v.anio != null) _row('Año', '${v.anio}'),
              if (v.color != null && v.color!.isNotEmpty) _row('Color', v.color!),
              const SizedBox(height: 24),
              ShadButton(
                onPressed: () => context.push('/cliente/app/vehiculos/${widget.vehiculoId}/editar'),
                child: const Text('Editar'),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _row(String k, String v) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(width: 88, child: Text(k, style: const TextStyle(fontWeight: FontWeight.w600))),
          Expanded(child: Text(v)),
        ],
      ),
    );
  }
}

class ClienteVehiculoFormScreen extends ConsumerStatefulWidget {
  const ClienteVehiculoFormScreen({super.key, this.vehiculoId});

  final int? vehiculoId;

  @override
  ConsumerState<ClienteVehiculoFormScreen> createState() => _ClienteVehiculoFormScreenState();
}

class _ClienteVehiculoFormScreenState extends ConsumerState<ClienteVehiculoFormScreen> {
  final _placa = TextEditingController();
  final _anio = TextEditingController();
  final _color = TextEditingController();

  List<CatalogItem> _marcas = [];
  List<ModeloRow> _modelos = [];
  List<CatalogItem> _tipos = [];

  int? _marcaId;
  int? _modeloId;
  int? _tipoId;
  bool _loading = true;
  String? _error;

  bool get _isEdit => widget.vehiculoId != null;

  @override
  void initState() {
    super.initState();
    _init();
  }

  Future<void> _init() async {
    final repo = ref.read(vehiculoRepositoryProvider);
    try {
      final marcas = await repo.fetchMarcas();
      final tipos = await repo.fetchTipos();
      _marcas = marcas;
      _tipos = tipos;

      if (_isEdit) {
        final v = await repo.fetchDisplay(widget.vehiculoId!);
        _placa.text = v.placa;
        if (v.anio != null) _anio.text = '${v.anio}';
        _color.text = v.color ?? '';

        final marcaMatch = marcas.where((m) => m.nombre == v.marcaNombre).toList();
        if (marcaMatch.isNotEmpty) {
          _marcaId = marcaMatch.first.id;
          _modelos = await repo.fetchModelos(marcaId: _marcaId);
          final modeloMatch = _modelos.where((m) => m.nombre == v.modeloNombre).toList();
          if (modeloMatch.isNotEmpty) _modeloId = modeloMatch.first.id;
        }
        final tipoMatch = tipos.where((t) => t.nombre == v.tipoNombre).toList();
        if (tipoMatch.isNotEmpty) _tipoId = tipoMatch.first.id;
      }
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  void dispose() {
    _placa.dispose();
    _anio.dispose();
    _color.dispose();
    super.dispose();
  }

  Future<void> _onMarcaChanged(int? id) async {
    setState(() {
      _marcaId = id;
      _modeloId = null;
      _modelos = [];
    });
    if (id == null) return;
    final repo = ref.read(vehiculoRepositoryProvider);
    final m = await repo.fetchModelos(marcaId: id);
    setState(() => _modelos = m);
  }

  Future<void> _save() async {
    setState(() => _error = null);
    if (_marcaId == null || _modeloId == null || _tipoId == null || _placa.text.trim().isEmpty) {
      setState(() => _error = 'Completa placa, marca, modelo y tipo.');
      return;
    }
    int? anio;
    if (_anio.text.trim().isNotEmpty) {
      anio = int.tryParse(_anio.text.trim());
      if (anio == null) {
        setState(() => _error = 'Año inválido.');
        return;
      }
    }
    final repo = ref.read(vehiculoRepositoryProvider);
    try {
      if (_isEdit) {
        await repo.update(
          widget.vehiculoId!,
          placa: _placa.text,
          marcaId: _marcaId,
          modeloId: _modeloId,
          tipoVehiculoId: _tipoId,
          anio: anio,
          color: _color.text.trim().isEmpty ? null : _color.text.trim(),
        );
      } else {
        await repo.create(
          placa: _placa.text,
          marcaId: _marcaId!,
          modeloId: _modeloId!,
          tipoVehiculoId: _tipoId!,
          anio: anio,
          color: _color.text.trim().isEmpty ? null : _color.text.trim(),
        );
      }
      ref.invalidate(vehiculosMineProvider);
      if (mounted) context.pop();
    } catch (e) {
      setState(() => _error = e.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    return Scaffold(
      appBar: AppBar(title: Text(_isEdit ? 'Editar vehículo' : 'Registrar vehículo')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Text('Placa', style: Theme.of(context).textTheme.labelLarge),
          const SizedBox(height: 6),
          ShadInput(controller: _placa, placeholder: const Text('ABC1234')),
          const SizedBox(height: 14),
          Text('Marca', style: Theme.of(context).textTheme.labelLarge),
          DropdownButtonFormField<int>(
            // ignore: deprecated_member_use
            value: _marcaId,
            items: [
              for (final m in _marcas) DropdownMenuItem(value: m.id, child: Text(m.nombre)),
            ],
            onChanged: _onMarcaChanged,
            decoration: const InputDecoration(),
          ),
          const SizedBox(height: 14),
          Text('Modelo', style: Theme.of(context).textTheme.labelLarge),
          DropdownButtonFormField<int>(
            // ignore: deprecated_member_use
            value: _modeloId,
            items: [
              for (final m in _modelos) DropdownMenuItem(value: m.id, child: Text(m.nombre)),
            ],
            onChanged: (v) => setState(() => _modeloId = v),
            decoration: const InputDecoration(),
          ),
          const SizedBox(height: 14),
          Text('Tipo de vehículo', style: Theme.of(context).textTheme.labelLarge),
          DropdownButtonFormField<int>(
            // ignore: deprecated_member_use
            value: _tipoId,
            items: [
              for (final t in _tipos) DropdownMenuItem(value: t.id, child: Text(t.nombre)),
            ],
            onChanged: (v) => setState(() => _tipoId = v),
            decoration: const InputDecoration(),
          ),
          const SizedBox(height: 14),
          Text('Año (opcional)', style: Theme.of(context).textTheme.labelLarge),
          ShadInput(controller: _anio, placeholder: const Text('2020'), keyboardType: TextInputType.number),
          const SizedBox(height: 14),
          Text('Color (opcional)', style: Theme.of(context).textTheme.labelLarge),
          ShadInput(controller: _color, placeholder: const Text('Blanco')),
          if (_error != null) ...[
            const SizedBox(height: 12),
            Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
          ],
          const SizedBox(height: 24),
          ShadButton(onPressed: _save, child: Text(_isEdit ? 'Guardar cambios' : 'Guardar')),
        ],
      ),
    );
  }
}
