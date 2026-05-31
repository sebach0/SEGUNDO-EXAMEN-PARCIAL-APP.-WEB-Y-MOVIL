import 'auth_me.dart';

/// Perfil agregado para UI técnico/responsable.
final class TecnicoPerfil {
  const TecnicoPerfil({
    required this.usuarioId,
    required this.nombres,
    required this.apellidos,
    required this.email,
    required this.roles,
    this.telefono,
    this.especialidadNombre,
    this.estadoEtiqueta,
    this.disponibilidad,
    this.tallerNombre,
    required this.esResponsableTaller,
  });

  final int usuarioId;
  final String nombres;
  final String apellidos;
  final String email;
  final List<String> roles;
  final String? telefono;
  final String? especialidadNombre;
  final String? estadoEtiqueta;
  final String? disponibilidad;
  final String? tallerNombre;
  final bool esResponsableTaller;

  String get nombreCompleto => ('$nombres $apellidos').trim();

  factory TecnicoPerfil.fromMiTaller({
    required AuthMe me,
    required Map<String, dynamic> tallerJson,
  }) {
    return TecnicoPerfil(
      usuarioId: me.id,
      nombres: tallerJson['responsable_nombres'] as String? ?? me.nombres,
      apellidos: tallerJson['responsable_apellidos'] as String? ?? me.apellidos,
      email: tallerJson['responsable_email'] as String? ?? me.email,
      roles: me.roles,
      telefono: tallerJson['responsable_telefono'] as String?,
      especialidadNombre: 'Responsable de taller',
      estadoEtiqueta: (tallerJson['estado'] ?? '').toString(),
      disponibilidad: null,
      tallerNombre: tallerJson['nombre_comercial'] as String?,
      esResponsableTaller: true,
    );
  }

  factory TecnicoPerfil.fromTecnicoRow({
    required AuthMe me,
    required Map<String, dynamic> tecnicoJson,
    String? tallerNombre,
  }) {
    final esp = tecnicoJson['especialidad_nombre'] as String?;
    return TecnicoPerfil(
      usuarioId: me.id,
      nombres: me.nombres,
      apellidos: me.apellidos,
      email: me.email,
      roles: me.roles,
      telefono: null,
      especialidadNombre: esp,
      estadoEtiqueta: (tecnicoJson['estado'] ?? '').toString(),
      disponibilidad: tecnicoJson['disponibilidad'] as String?,
      tallerNombre: tallerNombre,
      esResponsableTaller: false,
    );
  }

  factory TecnicoPerfil.minimal(AuthMe me) {
    return TecnicoPerfil(
      usuarioId: me.id,
      nombres: me.nombres,
      apellidos: me.apellidos,
      email: me.email,
      roles: me.roles,
      telefono: null,
      especialidadNombre: null,
      estadoEtiqueta: null,
      disponibilidad: null,
      tallerNombre: null,
      esResponsableTaller: me.roles.contains('TALLER_RESPONSABLE'),
    );
  }
}
