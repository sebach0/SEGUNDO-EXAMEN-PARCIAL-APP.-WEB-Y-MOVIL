import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/push/fcm_registration.dart';
import '../domain/models/cliente_mi_perfil.dart';
import 'client_auth_state.dart';
import 'cliente_injection.dart';
import 'vehiculos_providers.dart';

/// Orquesta login, logout, registro y restauración de sesión (Riverpod 3 Notifier).
final class ClientAuthNotifier extends Notifier<ClientAuthState> {
  @override
  ClientAuthState build() {
    Future.microtask(_bootstrap);
    return const ClientAuthState.checking();
  }

  Future<void> _bootstrap() async {
    final auth = ref.read(authRepositoryProvider);
    final token = await auth.readAccessToken();
    if (token == null || token.isEmpty) {
      state = const ClientAuthState(
        status: ClientAuthStatus.guest,
        infoMessage: null,
      );
      return;
    }
    try {
      final profile = await auth.fetchMiPerfil();
      state = ClientAuthState(
        status: ClientAuthStatus.authenticated,
        profile: profile,
      );
      unawaited(ref.read(fcmRegistrationProvider).onClienteSessionActive());
    } catch (_) {
      await auth.logout();
      state = const ClientAuthState(status: ClientAuthStatus.guest, infoMessage: null);
    }
  }

  Future<void> login({required String email, required String password}) async {
    state = state.copyWith(isLoggingIn: true, clearError: true, clearInfoMessage: true);
    final auth = ref.read(authRepositoryProvider);
    try {
      await auth.login(email: email, password: password);
      final profile = await auth.fetchMiPerfil();
      state = ClientAuthState(
        status: ClientAuthStatus.authenticated,
        profile: profile,
      );
      unawaited(ref.read(fcmRegistrationProvider).onClienteSessionActive());
    } catch (e) {
      state = ClientAuthState(
        status: ClientAuthStatus.guest,
        authError: e.toString().replaceFirst('Exception: ', ''),
        infoMessage: null,
        isLoggingIn: false,
      );
    }
  }

  Future<void> registerAndLogin({
    required String nombres,
    required String apellidos,
    required String email,
    required String telefono,
    required String password,
  }) async {
    state = state.copyWith(isLoggingIn: true, clearError: true, clearInfoMessage: true);
    final auth = ref.read(authRepositoryProvider);
    try {
      final profile = await auth.registerCliente(
        nombres: nombres,
        apellidos: apellidos,
        email: email,
        telefono: telefono,
        password: password,
      );
      if (profile.pendienteVerificacionEmail) {
        state = const ClientAuthState(
          status: ClientAuthStatus.guest,
          infoMessage:
              'Te enviamos un correo de verificación. Abre el enlace para activar la cuenta y luego inicia sesión.',
          isLoggingIn: false,
        );
        return;
      }
      await login(email: email, password: password);
    } catch (e) {
      state = ClientAuthState(
        status: ClientAuthStatus.guest,
        authError: e.toString().replaceFirst('Exception: ', ''),
        infoMessage: null,
        isLoggingIn: false,
      );
    }
  }

  Future<void> logout() async {
    await ref.read(fcmRegistrationProvider).beforeClienteLogout();
    final auth = ref.read(authRepositoryProvider);
    await auth.logout();
    ref.invalidate(vehiculosMineProvider);
    state = const ClientAuthState(status: ClientAuthStatus.guest, infoMessage: null);
  }

  void clearError() {
    state = state.copyWith(clearError: true, clearInfoMessage: true);
  }

  /// Solo limpia el aviso informativo (p. ej. tras navegar a login post-registro).
  void clearInfoMessage() {
    state = state.copyWith(clearInfoMessage: true);
  }

  void replaceProfileAfterUpdate(ClienteMiPerfil profile) {
    if (!state.isAuthenticated) return;
    state = ClientAuthState(
      status: ClientAuthStatus.authenticated,
      profile: profile,
    );
  }
}
