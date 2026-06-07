// Copia archivos de evidencia a almacenamiento persistente (no temp).
import 'dart:io';

import 'package:path_provider/path_provider.dart';

class OfflineEmergenciaStorage {
  static Future<Directory> _draftDir(String clientUuid) async {
    final base = await getApplicationDocumentsDirectory();
    final dir = Directory('${base.path}/offline_emergencias/$clientUuid');
    if (!await dir.exists()) {
      await dir.create(recursive: true);
    }
    return dir;
  }

  /// Copia [sourcePath] al directorio del borrador y devuelve la ruta persistente.
  static Future<String> copyEvidenceFile({
    required String clientUuid,
    required String sourcePath,
    required String filename,
  }) async {
    final dir = await _draftDir(clientUuid);
    final safeName = filename.replaceAll(RegExp(r'[^\w.\-]+'), '_');
    final dest = File('${dir.path}/$safeName');
    await File(sourcePath).copy(dest.path);
    return dest.path;
  }

  static Future<void> deleteDraft(String clientUuid) async {
    final base = await getApplicationDocumentsDirectory();
    final dir = Directory('${base.path}/offline_emergencias/$clientUuid');
    if (await dir.exists()) {
      await dir.delete(recursive: true);
    }
  }
}
