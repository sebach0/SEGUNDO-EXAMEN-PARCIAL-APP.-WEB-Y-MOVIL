import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_client.dart';
import '../comunicacion/data/comunicacion_repository.dart';
import '../pagos/data/pagos_repository.dart';
import '../data/repositories/auth_repository.dart';
import '../data/repositories/vehiculo_repository.dart';

final dioProvider = Provider<Dio>((ref) {
  return ApiClient().dio;
});

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository(ref.watch(dioProvider));
});

final vehiculoRepositoryProvider = Provider<VehiculoRepository>((ref) {
  return VehiculoRepository(ref.watch(dioProvider));
});

final comunicacionRepositoryProvider = Provider<ComunicacionRepository>((ref) {
  return ComunicacionRepository(ref.watch(dioProvider));
});

final pagosRepositoryProvider = Provider<PagosRepository>((ref) {
  return PagosRepository(ref.watch(dioProvider));
});
