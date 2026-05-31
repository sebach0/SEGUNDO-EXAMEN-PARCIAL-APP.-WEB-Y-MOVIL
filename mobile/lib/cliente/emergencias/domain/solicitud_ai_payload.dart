// Modelo v1 alineado a `post_create` → `solicitud.ai_payload` (JSON).
import 'package:flutter/foundation.dart';

/// Payload opcional de IA devuelto por GET detalle / seguimiento.
@immutable
class SolicitudAiPayloadV1 {
  const SolicitudAiPayloadV1({
    required this.version,
    this.clasificacion,
    this.prioridad,
    this.resumenEstructurado,
    this.transcripcionAudio,
    this.hallazgosVision = const [],
    this.hallazgosVisionPorImagen = const [],
    this.sugerenciaAsignacion,
  });

  final int version;
  final ClasificacionIa? clasificacion;
  final PrioridadIa? prioridad;
  final ResumenEstructuradoIa? resumenEstructurado;
  final String? transcripcionAudio;
  final List<String> hallazgosVision;
  final List<List<String>> hallazgosVisionPorImagen;
  final Map<String, dynamic>? sugerenciaAsignacion;

  static SolicitudAiPayloadV1? tryParse(Object? raw) {
    if (raw == null) return null;
    if (raw is! Map) return null;
    final m = Map<String, dynamic>.from(raw);
    final v = m['version'];
    final version = v is int ? v : (v is num ? v.toInt() : 1);
    return SolicitudAiPayloadV1(
      version: version,
      clasificacion: ClasificacionIa.tryParse(m['clasificacion']),
      prioridad: PrioridadIa.tryParse(m['prioridad']),
      resumenEstructurado: ResumenEstructuradoIa.tryParse(m['resumen_estructurado']),
      transcripcionAudio: m['transcripcion_audio'] is String ? m['transcripcion_audio'] as String? : null,
      hallazgosVision: _stringList(m['hallazgos_vision']),
      hallazgosVisionPorImagen: _stringMatrix(m['hallazgos_vision_por_imagen']),
      sugerenciaAsignacion: m['sugerencia_asignacion'] is Map
          ? Map<String, dynamic>.from(m['sugerencia_asignacion'] as Map)
          : null,
    );
  }

  bool get tieneContenidoUtil =>
      resumenEstructurado != null ||
      clasificacion != null ||
      prioridad != null ||
      (transcripcionAudio != null && transcripcionAudio!.trim().isNotEmpty) ||
      hallazgosVision.isNotEmpty ||
      hallazgosVisionPorImagen.isNotEmpty ||
      sugerenciaAsignacion != null;
}

List<String> _stringList(Object? o) {
  if (o is! List) return const [];
  return [for (final e in o) if (e != null) e.toString()];

}

List<List<String>> _stringMatrix(Object? o) {
  if (o is! List) return const [];
  return [
    for (final row in o)
      if (row is List) [for (final cell in row) if (cell != null) cell.toString()],
  ];
}

/// Un daño inferido (backend `DamagePrediction`); no usar `.toString()` del Map en UI.
@immutable
class DanoIaV1 {
  const DanoIaV1({
    required this.label,
    this.confidence = 0,
    this.severity = '',
    this.reasons = const [],
    this.conflictHasConflict = false,
    this.conflictDetails = const [],
  });

  final String label;
  final double confidence;
  final String severity;
  final List<String> reasons;
  final bool conflictHasConflict;
  final List<String> conflictDetails;

  factory DanoIaV1.fromMap(Map<String, dynamic> m) {
    final c = m['conflict'];
    Map<String, dynamic>? cm;
    if (c is Map) {
      cm = Map<String, dynamic>.from(c);
    }
    return DanoIaV1(
      label: m['label'] as String? ?? '—',
      confidence: m['confidence'] is num ? (m['confidence'] as num).toDouble() : 0.0,
      severity: m['severity'] is String ? m['severity'] as String : '',
      reasons: _stringList(m['reasons']),
      conflictHasConflict: cm?['has_conflict'] == true,
      conflictDetails: cm != null ? _stringList(cm['details']) : const [],
    );
  }

  /// Línea principal para listados (evita el dump crudo del objeto).
  String get lineaPrincipal {
    final sev = severity.isNotEmpty ? ' · $severity' : '';
    final pct = confidence > 0 ? ' · ${(confidence * 100).toStringAsFixed(0)}%' : '';
    return '$label$sev$pct';
  }
}

List<DanoIaV1> _parseDanosIaList(Object? o) {
  if (o is! List) return const [];
  final out = <DanoIaV1>[];
  for (final e in o) {
    if (e is Map) {
      out.add(DanoIaV1.fromMap(Map<String, dynamic>.from(e)));
    } else if (e != null) {
      out.add(DanoIaV1(label: e.toString()));
    }
  }
  return out;
}

@immutable
class ClasificacionIa {
  const ClasificacionIa({
    required this.categoria,
    required this.confianza,
    this.fuentes = const [],
    this.damages = const [],
    this.requiresManualReview = false,
    this.conflictNotes = const [],
  });

  final String categoria;
  final double confianza;
  final List<String> fuentes;
  final List<DanoIaV1> damages;
  final bool requiresManualReview;
  final List<String> conflictNotes;

  static ClasificacionIa? tryParse(Object? o) {
    if (o is! Map) return null;
    final m = o as Map<String, dynamic>;
    final cat = m['categoria'];
    if (cat is! String) return null;
    final conf = m['confianza'];
    final c = conf is num ? conf.toDouble() : 0.0;
    return ClasificacionIa(
      categoria: cat,
      confianza: c.clamp(0.0, 1.0),
      fuentes: _stringList(m['fuentes']),
      damages: _parseDanosIaList(m['damages']),
      requiresManualReview: m['requires_manual_review'] as bool? ?? false,
      conflictNotes: _stringList(m['conflict_notes']),
    );
  }
}

@immutable
class PrioridadIa {
  const PrioridadIa({
    required this.nivelPrioridad,
    this.motivo = const [],
    this.score,
    this.damagesConsiderados = const [],
  });

  final String nivelPrioridad;
  final List<String> motivo;
  final double? score;
  final List<String> damagesConsiderados;

  static PrioridadIa? tryParse(Object? o) {
    if (o is! Map) return null;
    final m = o as Map<String, dynamic>;
    final n = m['nivel_prioridad'];
    if (n is! String) return null;
    final scoreRaw = m['score'];
    return PrioridadIa(
      nivelPrioridad: n,
      motivo: _stringList(m['motivo']),
      score: scoreRaw is num ? scoreRaw.toDouble() : null,
      damagesConsiderados: _stringList(m['damages_considerados']),
    );
  }
}

@immutable
class FichaIncidenteIa {
  const FichaIncidenteIa({
    required this.tipoProblema,
    required this.ubicacionValida,
    required this.evidenciaAudio,
    required this.evidenciaImagen,
    required this.incertidumbre,
  });

  final String tipoProblema;
  final bool ubicacionValida;
  final bool evidenciaAudio;
  final bool evidenciaImagen;
  final String incertidumbre;

  static FichaIncidenteIa? tryParse(Object? o) {
    if (o is! Map) return null;
    final m = o as Map<String, dynamic>;
    final t = m['tipo_problema'];
    if (t is! String) return null;
    return FichaIncidenteIa(
      tipoProblema: t,
      ubicacionValida: m['ubicacion_valida'] as bool? ?? false,
      evidenciaAudio: m['evidencia_audio'] as bool? ?? false,
      evidenciaImagen: m['evidencia_imagen'] as bool? ?? false,
      incertidumbre: m['incertidumbre'] as String? ?? 'MEDIA',
    );
  }
}

@immutable
class ResumenEstructuradoIa {
  const ResumenEstructuradoIa({
    required this.resumen,
    this.ficha,
    this.danosDetectados = const [],
  });

  final String resumen;
  final FichaIncidenteIa? ficha;
  final List<String> danosDetectados;

  static ResumenEstructuradoIa? tryParse(Object? o) {
    if (o is! Map) return null;
    final m = o as Map<String, dynamic>;
    final r = m['resumen'];
    if (r is! String) return null;
    return ResumenEstructuradoIa(
      resumen: r,
      ficha: FichaIncidenteIa.tryParse(m['ficha']),
      danosDetectados: _stringList(m['danos_detectados']),
    );
  }
}

/// Etiquetas cortas en español para enums del backend.
String etiquetaCategoriaIa(String categoria) {
  return switch (categoria.toUpperCase()) {
    'BATERIA' => 'Batería',
    'LLANTA' => 'Llanta / pinchazo',
    'CHOQUE' => 'Choque / colisión',
    'MOTOR' => 'Motor',
    'OTROS' => 'Otros',
    _ => categoria,
  };
}

String etiquetaPrioridadIa(String nivel) {
  return switch (nivel.toUpperCase()) {
    'ALTA' => 'Alta',
    'MEDIA' => 'Media',
    'BAJA' => 'Baja',
    'REVISION_MANUAL' => 'Revisión manual',
    _ => nivel,
  };
}
