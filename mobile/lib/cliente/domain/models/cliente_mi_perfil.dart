/// Perfil cliente devuelto por `GET /app/cliente/mi-perfil` y `POST /app/cliente/registro`.
final class ClienteMiPerfil {
  const ClienteMiPerfil({
    required this.usuarioId,
    required this.clienteId,
    required this.nombres,
    required this.apellidos,
    required this.email,
    required this.telefono,
    required this.ciudad,
    required this.direccion,
    this.pendienteVerificacionEmail = false,
  });

  final int usuarioId;
  final int clienteId;
  final String nombres;
  final String apellidos;
  final String email;
  final String telefono;
  final String? ciudad;
  final String? direccion;
  final bool pendienteVerificacionEmail;

  String get nombreCompleto => '$nombres $apellidos'.trim();

  factory ClienteMiPerfil.fromJson(Map<String, dynamic> json) {
    return ClienteMiPerfil(
      usuarioId: json['usuario_id'] as int,
      clienteId: json['cliente_id'] as int,
      nombres: json['nombres'] as String,
      apellidos: json['apellidos'] as String,
      email: json['email'] as String,
      telefono: json['telefono'] as String,
      ciudad: json['ciudad'] as String?,
      direccion: json['direccion'] as String?,
      pendienteVerificacionEmail: json['pendiente_verificacion_email'] as bool? ?? false,
    );
  }

  Map<String, dynamic> toJson() => {
        'usuario_id': usuarioId,
        'cliente_id': clienteId,
        'nombres': nombres,
        'apellidos': apellidos,
        'email': email,
        'telefono': telefono,
        'ciudad': ciudad,
        'direccion': direccion,
        'pendiente_verificacion_email': pendienteVerificacionEmail,
      };
}
