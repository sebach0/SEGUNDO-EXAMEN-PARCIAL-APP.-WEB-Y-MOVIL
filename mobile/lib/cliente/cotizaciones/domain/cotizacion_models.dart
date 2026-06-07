// Modelos de dominio — cotizaciones (API /cotizaciones/solicitudes/{id})
import '../../../core/utils/api_datetime.dart';

// ── Enums ────────────────────────────────────────────────────────────────────

enum EstadoCotizacion {
  enviada('ENVIADA'),
  aceptada('ACEPTADA'),
  rechazada('RECHAZADA'),
  expirada('EXPIRADA');

  const EstadoCotizacion(this.apiValue);
  final String apiValue;

  static EstadoCotizacion parse(String s) {
    return EstadoCotizacion.values.firstWhere(
      (e) => e.apiValue == s,
      orElse: () => EstadoCotizacion.enviada,
    );
  }

  String get etiqueta => switch (this) {
        EstadoCotizacion.enviada   => 'Enviada',
        EstadoCotizacion.aceptada  => 'Aceptada',
        EstadoCotizacion.rechazada => 'Rechazada',
        EstadoCotizacion.expirada  => 'Expirada',
      };

  bool get isActive => this == EstadoCotizacion.enviada;
  bool get isSelected => this == EstadoCotizacion.aceptada;
}

// ── Ítem de cotización ────────────────────────────────────────────────────────

final class CotizacionItem {
  const CotizacionItem({
    required this.id,
    required this.cotizacionId,
    required this.descripcion,
    required this.cantidad,
    required this.precioUnitario,
    required this.subtotal,
  });

  final int id;
  final int cotizacionId;
  final String descripcion;
  final double cantidad;
  final double precioUnitario;
  final double subtotal;

  factory CotizacionItem.fromJson(Map<String, dynamic> m) => CotizacionItem(
        id: m['id'] as int,
        cotizacionId: m['cotizacion_id'] as int,
        descripcion: m['descripcion'] as String,
        cantidad: _asDouble(m['cantidad']),
        precioUnitario: _asDouble(m['precio_unitario']),
        subtotal: _asDouble(m['subtotal']),
      );
}

// ── Servicios ofrecidos en cotización ─────────────────────────────────────────

final class ServicioOfrecido {
  const ServicioOfrecido({
    required this.id,
    required this.nombre,
    required this.codigo,
  });

  final int id;
  final String nombre;
  final String codigo;

  factory ServicioOfrecido.fromJson(Map<String, dynamic> m) => ServicioOfrecido(
        id: m['id'] as int,
        nombre: m['nombre'] as String? ?? '',
        codigo: m['codigo'] as String? ?? '',
      );
}

// ── Cotización ────────────────────────────────────────────────────────────────

final class Cotizacion {
  const Cotizacion({
    required this.id,
    required this.solicitudId,
    required this.tallerId,
    required this.tallerNombre,
    required this.estado,
    required this.descripcionDanio,
    required this.detalleServicio,
    required this.montoTotal,
    this.tiempoEstimadoLlegadaMin,
    this.tiempoEstimadoReparacionMin,
    required this.incluyeGrua,
    this.garantiaDescripcion,
    this.comentarios,
    this.distanciaKm,
    this.serviciosOfrecidos = const [],
    this.seleccionadaAt,
    required this.creadoAt,
    required this.items,
  });

  final int id;
  final int solicitudId;
  final int tallerId;
  final String? tallerNombre;
  final EstadoCotizacion estado;
  final String descripcionDanio;
  final String detalleServicio;
  final double montoTotal;
  final int? tiempoEstimadoLlegadaMin;
  final int? tiempoEstimadoReparacionMin;
  final bool incluyeGrua;
  final String? garantiaDescripcion;
  final String? comentarios;
  final double? distanciaKm;
  final List<ServicioOfrecido> serviciosOfrecidos;
  final DateTime? seleccionadaAt;
  final DateTime creadoAt;
  final List<CotizacionItem> items;

  factory Cotizacion.fromJson(Map<String, dynamic> m) => Cotizacion(
        id: m['id'] as int,
        solicitudId: m['solicitud_id'] as int,
        tallerId: m['taller_id'] as int,
        tallerNombre: m['taller_nombre'] as String?,
        estado: EstadoCotizacion.parse(m['estado'] as String),
        descripcionDanio: m['descripcion_danio'] as String,
        detalleServicio: m['detalle_servicio'] as String,
        montoTotal: _asDouble(m['monto_total']),
        tiempoEstimadoLlegadaMin: m['tiempo_estimado_llegada_min'] as int?,
        tiempoEstimadoReparacionMin: m['tiempo_estimado_reparacion_min'] as int?,
        incluyeGrua: m['incluye_grua'] as bool? ?? false,
        garantiaDescripcion: m['garantia_descripcion'] as String?,
        comentarios: m['comentarios'] as String?,
        distanciaKm: m['distancia_km'] != null ? _asDouble(m['distancia_km']) : null,
        serviciosOfrecidos: [
          for (final e in (m['servicios_ofrecidos'] as List<dynamic>? ?? []))
            if (e is Map<String, dynamic>) ServicioOfrecido.fromJson(e),
        ],
        seleccionadaAt: m['seleccionada_at'] != null
            ? parseApiDateTime(m['seleccionada_at'])
            : null,
        creadoAt: parseApiDateTime(m['creado_at']),
        items: [
          for (final e in (m['items'] as List<dynamic>? ?? []))
            if (e is Map<String, dynamic>) CotizacionItem.fromJson(e),
        ],
      );

  /// Ítem automático de traslado del técnico (5 Bs/km en backend).
  CotizacionItem? get itemTraslado {
    for (final i in items) {
      if (_esItemTraslado(i.descripcion)) return i;
    }
    return null;
  }

  double get costoTraslado => itemTraslado?.subtotal ?? 0;

  double get montoServicio => montoTotal - costoTraslado;
}

bool _esItemTraslado(String descripcion) {
  final d = descripcion.toLowerCase();
  return d.contains('traslado') && (d.contains('técnico') || d.contains('tecnico'));
}

// ── Helper ────────────────────────────────────────────────────────────────────
double _asDouble(Object? v) {
  if (v is num) return v.toDouble();
  if (v is String) return double.parse(v);
  throw FormatException('No es número: $v');
}
