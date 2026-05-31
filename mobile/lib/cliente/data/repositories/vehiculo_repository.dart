import 'package:dio/dio.dart';

import '../../../core/constants/api_constants.dart';
import '../../domain/models/vehiculo_display.dart';
import '../../../core/network/api_error.dart';

typedef CatalogItem = ({int id, String nombre});
typedef ModeloRow = ({int id, int marcaId, String nombre});

/// Catálogos y vehículos del cliente (rutas `/app/cliente/...` autenticadas).
final class VehiculoRepository {
  VehiculoRepository(this._dio);

  final Dio _dio;

  Future<List<CatalogItem>> fetchMarcas() async {
    final res = await _dio.get<List<dynamic>>(ApiConstants.vehiculosMarcas);
    return _mapSimpleCatalog(res.data);
  }

  Future<List<ModeloRow>> fetchModelos({int? marcaId}) async {
    final res = await _dio.get<List<dynamic>>(ApiConstants.vehiculosModelos(marcaId: marcaId));
    if (res.data == null) return [];
    return [
      for (final e in res.data!)
        if (e is Map<String, dynamic>)
          (
            id: e['id'] as int,
            marcaId: e['marca_id'] as int,
            nombre: e['nombre'] as String,
          ),
    ];
  }

  Future<List<CatalogItem>> fetchTipos() async {
    final res = await _dio.get<List<dynamic>>(ApiConstants.vehiculosTipos);
    return _mapSimpleCatalog(res.data);
  }

  List<CatalogItem> _mapSimpleCatalog(List<dynamic>? raw) {
    if (raw == null) return [];
    return [
      for (final e in raw)
        if (e is Map<String, dynamic>)
          (id: e['id'] as int, nombre: e['nombre'] as String),
    ];
  }

  Future<List<VehiculoDisplay>> listMine() async {
    try {
      final marcas = {for (final m in await fetchMarcas()) m.id: m.nombre};
      final tipos = {for (final t in await fetchTipos()) t.id: t.nombre};
      final modelos = await fetchModelos();
      final modeloNombreById = {for (final m in modelos) m.id: m.nombre};

      final res = await _dio.get<List<dynamic>>(ApiConstants.appClienteMisVehiculos);
      final raw = res.data ?? [];
      return [
        for (final item in raw)
          if (item is Map<String, dynamic>)
            VehiculoDisplay(
              id: item['id'] as int,
              clienteId: item['cliente_id'] as int,
              placa: item['placa'] as String,
              marcaNombre: marcas[item['marca_id'] as int] ?? '—',
              modeloNombre: modeloNombreById[item['modelo_id'] as int] ?? '—',
              tipoNombre: tipos[item['tipo_vehiculo_id'] as int] ?? '—',
              anio: item['anio'] as int?,
              color: item['color'] as String?,
            ),
      ];
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }

  Future<VehiculoDisplay> fetchDisplay(int id) async {
    try {
      final marcas = {for (final m in await fetchMarcas()) m.id: m.nombre};
      final tipos = {for (final t in await fetchTipos()) t.id: t.nombre};
      final modelos = await fetchModelos();
      final modeloNombreById = {for (final m in modelos) m.id: m.nombre};

      final res = await _dio.get<Map<String, dynamic>>(ApiConstants.appClienteMisVehiculo(id));
      final item = res.data;
      if (item == null) throw Exception('Vehículo no encontrado');
      return VehiculoDisplay(
        id: item['id'] as int,
        clienteId: item['cliente_id'] as int,
        placa: item['placa'] as String,
        marcaNombre: marcas[item['marca_id'] as int] ?? '—',
        modeloNombre: modeloNombreById[item['modelo_id'] as int] ?? '—',
        tipoNombre: tipos[item['tipo_vehiculo_id'] as int] ?? '—',
        anio: item['anio'] as int?,
        color: item['color'] as String?,
      );
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }

  Future<void> create({
    required String placa,
    required int marcaId,
    required int modeloId,
    required int tipoVehiculoId,
    int? anio,
    String? color,
  }) async {
    try {
      await _dio.post<void>(
        ApiConstants.appClienteMisVehiculos,
        data: {
          'placa': placa.trim().toUpperCase(),
          'marca_id': marcaId,
          'modelo_id': modeloId,
          'tipo_vehiculo_id': tipoVehiculoId,
          if (anio != null) 'anio': anio,
          if (color != null && color.trim().isNotEmpty) 'color': color.trim(),
        },
      );
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }

  Future<void> update(
    int id, {
    String? placa,
    int? marcaId,
    int? modeloId,
    int? tipoVehiculoId,
    int? anio,
    String? color,
  }) async {
    try {
      await _dio.put<void>(
        ApiConstants.appClienteMisVehiculo(id),
        data: {
          if (placa != null) 'placa': placa.trim().toUpperCase(),
          if (marcaId != null) 'marca_id': marcaId,
          if (modeloId != null) 'modelo_id': modeloId,
          if (tipoVehiculoId != null) 'tipo_vehiculo_id': tipoVehiculoId,
          if (anio != null) 'anio': anio,
          if (color != null) 'color': color.trim(),
        },
      );
    } on DioException catch (e) {
      throw Exception(messageFromDio(e));
    }
  }
}
