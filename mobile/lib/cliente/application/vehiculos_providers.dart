import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../domain/models/vehiculo_display.dart';
import 'cliente_injection.dart';

/// Listado de vehículos del cliente autenticado.
final vehiculosMineProvider =
    FutureProvider.autoDispose<List<VehiculoDisplay>>((ref) async {
  final repo = ref.watch(vehiculoRepositoryProvider);
  return repo.listMine();
});
