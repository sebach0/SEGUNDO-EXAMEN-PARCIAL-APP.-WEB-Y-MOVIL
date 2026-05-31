/// Respuesta de `GET /auth/me` (campos usados por el módulo técnico).
final class AuthMe {
  const AuthMe({
    required this.id,
    required this.nombres,
    required this.apellidos,
    required this.email,
    required this.roles,
  });

  final int id;
  final String nombres;
  final String apellidos;
  final String email;
  final List<String> roles;

  factory AuthMe.fromJson(Map<String, dynamic> j) {
    final rolesRaw = j['roles'];
    return AuthMe(
      id: j['id'] as int,
      nombres: j['nombres'] as String? ?? '',
      apellidos: j['apellidos'] as String? ?? '',
      email: j['email'] as String? ?? '',
      roles: rolesRaw is List ? rolesRaw.map((e) => e.toString()).toList() : const [],
    );
  }
}
