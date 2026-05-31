/// Vehículo enriquecido para UI (catálogos resueltos en repositorio).
final class VehiculoDisplay {
  const VehiculoDisplay({
    required this.id,
    required this.clienteId,
    required this.placa,
    required this.marcaNombre,
    required this.modeloNombre,
    required this.tipoNombre,
    required this.anio,
    required this.color,
  });

  final int id;
  final int clienteId;
  final String placa;
  final String marcaNombre;
  final String modeloNombre;
  final String tipoNombre;
  final int? anio;
  final String? color;
}
