// Resultado de POST /api/ai/audio/transcribe
final class AudioTranscribeResult {
  const AudioTranscribeResult({
    required this.transcripcion,
    required this.keywords,
    required this.confianza,
    this.tipoProblemaMencionado,
    this.urgenciaPercibida,
    this.contextoBreve,
  });

  final String transcripcion;
  final List<String> keywords;
  final double confianza;
  final String? tipoProblemaMencionado;
  final String? urgenciaPercibida;
  final String? contextoBreve;

  factory AudioTranscribeResult.fromJson(Map<String, dynamic> json) {
    final rawKw = json['keywords'];
    return AudioTranscribeResult(
      transcripcion: (json['transcripcion'] as String? ?? '').trim(),
      keywords: rawKw is List ? [for (final e in rawKw) e.toString()] : const [],
      confianza: (json['confianza'] as num?)?.toDouble() ?? 0,
      tipoProblemaMencionado: json['tipo_problema_mencionado'] as String?,
      urgenciaPercibida: json['urgencia_percibida'] as String?,
      contextoBreve: json['contexto_breve'] as String?,
    );
  }
}
