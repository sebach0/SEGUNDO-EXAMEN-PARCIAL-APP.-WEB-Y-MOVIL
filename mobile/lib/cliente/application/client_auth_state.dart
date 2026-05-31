import 'package:flutter/foundation.dart';

import '../domain/models/cliente_mi_perfil.dart';

/// Estado de sesión del cliente móvil.
enum ClientAuthStatus {
  /// Restaurando token / perfil al arranque.
  checking,

  /// Sin sesión válida.
  guest,

  /// Token válido y perfil cliente cargado.
  authenticated,
}

@immutable
final class ClientAuthState {
  const ClientAuthState({
    required this.status,
    this.profile,
    this.authError,
    this.infoMessage,
    this.isLoggingIn = false,
  });

  const ClientAuthState.checking()
      : status = ClientAuthStatus.checking,
        profile = null,
        authError = null,
        infoMessage = null,
        isLoggingIn = false;

  final ClientAuthStatus status;
  final ClienteMiPerfil? profile;
  final String? authError;
  /// Mensaje informativo (p. ej. registro con verificación por correo).
  final String? infoMessage;
  final bool isLoggingIn;

  bool get isAuthenticated => status == ClientAuthStatus.authenticated && profile != null;

  ClientAuthState copyWith({
    ClientAuthStatus? status,
    ClienteMiPerfil? profile,
    String? authError,
    String? infoMessage,
    bool clearError = false,
    bool clearInfoMessage = false,
    bool? isLoggingIn,
  }) {
    return ClientAuthState(
      status: status ?? this.status,
      profile: profile ?? this.profile,
      authError: clearError ? null : (authError ?? this.authError),
      infoMessage: clearInfoMessage ? null : (infoMessage ?? this.infoMessage),
      isLoggingIn: isLoggingIn ?? this.isLoggingIn,
    );
  }
}
