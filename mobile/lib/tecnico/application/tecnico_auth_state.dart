import 'package:flutter/foundation.dart';

import '../domain/models/tecnico_perfil.dart';

/// Estado de sesión del flujo técnico/mecánico.
enum TecnicoAuthStatus {
  checking,
  guest,
  authenticated,
}

@immutable
final class TecnicoAuthState {
  const TecnicoAuthState({
    required this.status,
    this.perfil,
    this.authError,
    this.isLoggingIn = false,
  });

  const TecnicoAuthState.checking()
      : status = TecnicoAuthStatus.checking,
        perfil = null,
        authError = null,
        isLoggingIn = false;

  final TecnicoAuthStatus status;
  final TecnicoPerfil? perfil;
  final String? authError;
  final bool isLoggingIn;

  bool get isAuthenticated => status == TecnicoAuthStatus.authenticated && perfil != null;

  TecnicoAuthState copyWith({
    TecnicoAuthStatus? status,
    TecnicoPerfil? perfil,
    String? authError,
    bool clearError = false,
    bool? isLoggingIn,
  }) {
    return TecnicoAuthState(
      status: status ?? this.status,
      perfil: perfil ?? this.perfil,
      authError: clearError ? null : (authError ?? this.authError),
      isLoggingIn: isLoggingIn ?? this.isLoggingIn,
    );
  }
}
