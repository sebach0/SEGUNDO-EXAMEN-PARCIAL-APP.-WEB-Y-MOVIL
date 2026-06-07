// Transcripción de audio vía servicio IA del backend.
import 'package:dio/dio.dart';
import 'package:http_parser/http_parser.dart';

import '../../../core/constants/api_constants.dart';
import '../../../core/network/api_error.dart';
import '../domain/audio_transcribe_models.dart';

final class AiTranscribeRepository {
  AiTranscribeRepository(this._dio);

  final Dio _dio;

  Future<AudioTranscribeResult> transcribeFile({
    required String filePath,
    required String filename,
    String? mimeType,
  }) async {
    try {
      final form = FormData.fromMap({
        'file': await MultipartFile.fromFile(
          filePath,
          filename: filename,
          contentType: mimeType != null && mimeType.isNotEmpty
              ? MediaType.parse(mimeType)
              : null,
        ),
      });
      final res = await _dio.post<Map<String, dynamic>>(
        ApiConstants.aiAudioTranscribe,
        data: form,
        options: Options(
          sendTimeout: ApiConstants.uploadTimeout,
          receiveTimeout: ApiConstants.uploadTimeout,
        ),
      );
      final m = res.data;
      if (m == null) throw Exception('Respuesta vacía de transcripción');
      return AudioTranscribeResult.fromJson(m);
    } on DioException catch (e) {
      if (isNetworkFailure(e)) rethrow;
      throw Exception(messageFromDio(e));
    }
  }
}
