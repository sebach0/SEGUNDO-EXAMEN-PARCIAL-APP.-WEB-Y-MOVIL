import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/tecnico_api_client.dart';
import '../data/tecnico_auth_repository.dart';

final tecnicoDioProvider = Provider<Dio>((ref) {
  return TecnicoApiClient().dio;
});

final tecnicoAuthRepositoryProvider = Provider<TecnicoAuthRepository>((ref) {
  return TecnicoAuthRepository(ref.watch(tecnicoDioProvider));
});
