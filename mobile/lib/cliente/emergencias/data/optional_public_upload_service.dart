// Subida opcional a FILE_UPLOAD_URL (CDN propio; el asistente de emergencias usa el API directamente).
import 'package:dio/dio.dart';
import 'package:http_parser/http_parser.dart';

import '../../../core/config/app_env.dart';

/// Contrato mínimo: POST multipart campo `file`, respuesta JSON `{"url":"https://..."}`.
final class OptionalPublicUploadService {
  OptionalPublicUploadService() : _dio = Dio();

  final Dio _dio;

  Future<String> uploadFile({
    required String filePath,
    required String filename,
    required String mimeType,
  }) async {
    final endpoint = AppEnv.fileUploadUrl;
    if (endpoint == null) {
      throw StateError(
        'No hay FILE_UPLOAD_URL en .env. Podés pegar un enlace HTTPS manualmente o configurar un servicio de subida.',
      );
    }
    final form = FormData.fromMap({
      'file': await MultipartFile.fromFile(
        filePath,
        filename: filename,
        contentType: MediaType.parse(mimeType),
      ),
    });
    final res = await _dio.post<Map<String, dynamic>>(endpoint, data: form);
    final data = res.data;
    final url = data?['url'] as String?;
    if (url == null || !url.toLowerCase().startsWith('https://')) {
      throw const FormatException('La respuesta de subida no incluyó url HTTPS válida.');
    }
    return url.trim();
  }
}
