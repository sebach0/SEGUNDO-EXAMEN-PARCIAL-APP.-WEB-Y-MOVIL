import 'package:flutter/foundation.dart';
import '../../../core/utils/api_datetime.dart';

/// Estados alineados con API `estado_pago`.
enum EstadoPago {
  pendiente('PENDIENTE'),
  pagado('PAGADO'),
  fallido('FALLIDO'),
  anulado('ANULADO');

  const EstadoPago(this.apiValue);
  final String apiValue;

  static EstadoPago parse(String s) {
    return EstadoPago.values.firstWhere(
      (e) => e.apiValue == s,
      orElse: () => EstadoPago.pendiente,
    );
  }
}

/// Métodos alineados con API `metodo_pago`.
enum MetodoPago {
  qr('QR'),
  tarjeta('TARJETA'),
  transferencia('TRANSFERENCIA'),
  efectivo('EFECTIVO'),
  otro('OTRO');

  const MetodoPago(this.apiValue);
  final String apiValue;

  String get etiquetaUi => switch (this) {
        MetodoPago.qr => 'QR',
        MetodoPago.tarjeta => 'Tarjeta',
        MetodoPago.transferencia => 'Transferencia',
        MetodoPago.efectivo => 'Efectivo',
        MetodoPago.otro => 'Otro',
      };

  static MetodoPago parse(String s) {
    return MetodoPago.values.firstWhere(
      (e) => e.apiValue == s,
      orElse: () => MetodoPago.otro,
    );
  }
}

DateTime _asDateTime(Object? v) {
  return parseApiDateTime(v);
}

double _asDouble(Object? v) {
  if (v is num) return v.toDouble();
  if (v is String) return double.parse(v);
  throw FormatException('No es número: $v');
}

@immutable
final class PagoRead {
  const PagoRead({
    required this.id,
    required this.solicitudId,
    required this.clienteId,
    required this.monto,
    required this.moneda,
    required this.metodo,
    required this.estado,
    this.referenciaExterna,
    required this.proveedor,
    this.metadataJson,
    this.conciliadoAt,
    required this.createdAt,
    this.pagadoAt,
    this.stripeClientSecret,
    this.stripePublishableKey,
  });

  final int id;
  final int solicitudId;
  final int clienteId;
  final double monto;
  final String moneda;
  final MetodoPago metodo;
  final EstadoPago estado;
  final String? referenciaExterna;
  final String proveedor;
  final Map<String, dynamic>? metadataJson;
  final DateTime? conciliadoAt;
  final DateTime createdAt;
  final DateTime? pagadoAt;
  /// Solo en respuesta de `POST .../pagos` cuando el backend usa Stripe.
  final String? stripeClientSecret;
  final String? stripePublishableKey;

  /// PaymentSheet de Stripe aplica **solo a tarjeta**; el backend no debe devolver `client_secret` para otros métodos.
  bool requiereStripePaymentSheet(MetodoPago metodo) =>
      metodo == MetodoPago.tarjeta &&
      stripeClientSecret != null &&
      stripeClientSecret!.isNotEmpty &&
      estado == EstadoPago.pendiente;

  /// Id de PaymentIntent para `POST .../confirmar-stripe` (referencia, metadata o prefijo del client_secret).
  String? get stripePaymentIntentId {
    final ref = referenciaExterna?.trim();
    if (ref != null && ref.isNotEmpty) return ref;
    final mid = metadataJson?['payment_intent_id'];
    if (mid is String && mid.trim().isNotEmpty) return mid.trim();
    final cs = stripeClientSecret?.trim();
    if (cs != null && cs.startsWith('pi_')) {
      final i = cs.indexOf('_secret_');
      if (i > 0) return cs.substring(0, i);
    }
    return null;
  }

  factory PagoRead.fromJson(Map<String, dynamic> j) {
    return PagoRead(
      id: j['id'] as int,
      solicitudId: j['solicitud_id'] as int,
      clienteId: j['cliente_id'] as int,
      monto: _asDouble(j['monto']),
      moneda: j['moneda'] as String,
      metodo: MetodoPago.parse(j['metodo'] as String),
      estado: EstadoPago.parse(j['estado'] as String),
      referenciaExterna: j['referencia_externa'] as String?,
      proveedor: j['proveedor'] as String? ?? 'SIMULADO',
      metadataJson: j['metadata_json'] is Map<String, dynamic>
          ? j['metadata_json'] as Map<String, dynamic>
          : null,
      conciliadoAt: j['conciliado_at'] != null ? _asDateTime(j['conciliado_at']) : null,
      createdAt: _asDateTime(j['created_at']),
      pagadoAt: j['pagado_at'] != null ? _asDateTime(j['pagado_at']) : null,
      stripeClientSecret: j['stripe_client_secret'] as String?,
      stripePublishableKey: j['stripe_publishable_key'] as String?,
    );
  }
}

/// Datos del asistente de pago entre pantallas (go_router `extra`).
@immutable
final class PagoDraft {
  const PagoDraft({
    required this.solicitudId,
    required this.montoTexto,
    this.metodo,
    this.pagoIniciado,
  });

  final int solicitudId;
  final String montoTexto;
  final MetodoPago? metodo;
  /// Resultado de `POST .../pagos` al salir de método de pago; evita duplicar intentos y falta de PI en confirm.
  final PagoRead? pagoIniciado;

  PagoDraft copyWith({
    MetodoPago? metodo,
    PagoRead? pagoIniciado,
  }) {
    return PagoDraft(
      solicitudId: solicitudId,
      montoTexto: montoTexto,
      metodo: metodo ?? this.metodo,
      pagoIniciado: pagoIniciado ?? this.pagoIniciado,
    );
  }

  bool get puedeConfirmar =>
      metodo != null && montoTexto.trim().isNotEmpty && double.tryParse(montoTexto.replaceAll(',', '.')) != null;
}
