import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/push/fcm_registration.dart';
import '../data/tecnico_auth_repository.dart';
import '../domain/models/tecnico_perfil.dart';
import 'tecnico_auth_state.dart';
import 'tecnico_injection.dart';

/// Login, logout y restauración de sesión técnico (tokens separados del cliente).
final class TecnicoAuthNotifier extends Notifier<TecnicoAuthState> {
  @override
  TecnicoAuthState build() {
    Future.microtask(_bootstrap);
    return const TecnicoAuthState.checking();
  }

  Future<void> _bootstrap() async {
    final repo = ref.read(tecnicoAuthRepositoryProvider);
    final token = await repo.readAccessToken();
    if (token == null || token.isEmpty) {
      state = const TecnicoAuthState(status: TecnicoAuthStatus.guest);
      return;
    }
    try {
      final me = await repo.fetchMe();
      if (!TecnicoAuthRepository.rolesPermitidosTecnicoApp(me.roles)) {
        await repo.logoutLocal();
        state = const TecnicoAuthState(status: TecnicoAuthStatus.guest);
        return;
      }
      final perfil = await repo.fetchPerfilCompleto(me);
      state = TecnicoAuthState(status: TecnicoAuthStatus.authenticated, perfil: perfil);
      unawaited(ref.read(fcmRegistrationProvider).onTecnicoSessionActive());
    } catch (_) {
      await repo.logoutLocal();
      state = const TecnicoAuthState(status: TecnicoAuthStatus.guest);
    }
  }

  Future<void> login({required String email, required String password}) async {
    state = state.copyWith(isLoggingIn: true, clearError: true);
    final repo = ref.read(tecnicoAuthRepositoryProvider);
    try {
      final me = await repo.login(email: email, password: password);
      final perfil = await repo.fetchPerfilCompleto(me);
      state = TecnicoAuthState(
        status: TecnicoAuthStatus.authenticated,
        perfil: perfil,
      );
      unawaited(ref.read(fcmRegistrationProvider).onTecnicoSessionActive());
    } catch (e) {
      state = TecnicoAuthState(
        status: TecnicoAuthStatus.guest,
        authError: e.toString().replaceFirst('Exception: ', ''),
        isLoggingIn: false,
      );
    }
  }

  Future<void> logout() async {
    final repo = ref.read(tecnicoAuthRepositoryProvider);
    try {
      await ref
          .read(fcmRegistrationProvider)
          .beforeTecnicoLogout()
          .timeout(const Duration(seconds: 4));
    } catch (_) {}
    try {
      await repo.logout();
    } catch (_) {
      await repo.logoutLocal();
    }
    state = const TecnicoAuthState(status: TecnicoAuthStatus.guest);
  }

  void clearError() {
    state = state.copyWith(clearError: true);
  }

  void replacePerfil(TecnicoPerfil perfil) {
    if (!state.isAuthenticated) return;
    state = TecnicoAuthState(status: TecnicoAuthStatus.authenticated, perfil: perfil);
  }
}
