// lib/core/constants/api_constants.dart
// =========================================================
// Rutas de la API — la base y timeouts vienen de mobile/.env (ver AppEnv).
// Prefijo de app móvil / web responsable: `/app/...` (antes `/portal/...`).
// =========================================================

import '../config/app_env.dart';

class ApiConstants {
  static String get baseUrl => AppEnv.apiBaseUrl;

  // Endpoints — auth
  static String get login => '${AppEnv.apiBaseUrl}/auth/login';
  static String get logout => '${AppEnv.apiBaseUrl}/auth/logout';
  static String get me => '${AppEnv.apiBaseUrl}/auth/me';
  static String get authSolicitarRecuperacionContrasena =>
      '${AppEnv.apiBaseUrl}/auth/solicitar-recuperacion-contrasena';

  /// App taller (responsable): taller y datos del responsable.
  static String get appTallerMiTaller => '${AppEnv.apiBaseUrl}/app/taller/mi-taller';

  /// App técnico — emergencias.
  static String get appTecnicoEmergenciasServiciosAsignados =>
      '${AppEnv.apiBaseUrl}/app/tecnico/emergencias/servicios-asignados';

  static String appTecnicoEmergenciaUbicacion(int solicitudId) =>
      '${AppEnv.apiBaseUrl}/app/tecnico/emergencias/solicitudes/$solicitudId/ubicacion';

  static String appTecnicoEmergenciaUbicacionTecnico(int solicitudId) =>
      '${AppEnv.apiBaseUrl}/app/tecnico/emergencias/solicitudes/$solicitudId/ubicacion-tecnico';

  static String appTecnicoEmergenciaEstado(int solicitudId) =>
      '${AppEnv.apiBaseUrl}/app/tecnico/emergencias/solicitudes/$solicitudId/estado';

  static String appTecnicoEmergenciaMensajes(int solicitudId) =>
      '${AppEnv.apiBaseUrl}/app/tecnico/emergencias/$solicitudId/mensajes';

  // App móvil cliente
  static String get appClienteRegistro => '${AppEnv.apiBaseUrl}/app/cliente/registro';
  static String get appClienteMiPerfil => '${AppEnv.apiBaseUrl}/app/cliente/mi-perfil';
  static String get appClienteMisVehiculos => '${AppEnv.apiBaseUrl}/app/cliente/mis-vehiculos';

  static String appClienteMisVehiculo(int id) =>
      '${AppEnv.apiBaseUrl}/app/cliente/mis-vehiculos/$id';

  /// Solicitudes de emergencia (cliente autenticado).
  static String get appClienteEmergencias => '${AppEnv.apiBaseUrl}/app/cliente/emergencias';

  static String appClienteEmergencia(int id) =>
      '${AppEnv.apiBaseUrl}/app/cliente/emergencias/$id';

  /// Seguimiento, taller, técnico y ETA.
  static String appClienteEmergenciaSeguimiento(int id) =>
      '${AppEnv.apiBaseUrl}/app/cliente/emergencias/$id/seguimiento';

  static String appClienteEmergenciaUbicacionTecnico(int id) =>
      '${AppEnv.apiBaseUrl}/app/cliente/emergencias/$id/ubicacion-tecnico';

  static String appClienteEmergenciaUbicaciones(int id) =>
      '${AppEnv.apiBaseUrl}/app/cliente/emergencias/$id/ubicaciones';

  static String appClienteEmergenciaEvidencias(int id) =>
      '${AppEnv.apiBaseUrl}/app/cliente/emergencias/$id/evidencias';

  static String appClienteEmergenciaEvidenciasArchivo(int id) =>
      '${AppEnv.apiBaseUrl}/app/cliente/emergencias/$id/evidencias/archivo';

  /// Notificaciones, mensajes y FCM.
  static String get appClienteNotificaciones =>
      '${AppEnv.apiBaseUrl}/app/cliente/notificaciones';

  static String appClienteNotificacionLeida(int id) =>
      '${AppEnv.apiBaseUrl}/app/cliente/notificaciones/$id/leida';

  static String appClienteEmergenciaMensajes(int solicitudId) =>
      '${AppEnv.apiBaseUrl}/app/cliente/emergencias/$solicitudId/mensajes';

  /// Pagos por solicitud.
  static String appClienteEmergenciaPagos(int solicitudId) =>
      '${AppEnv.apiBaseUrl}/app/cliente/emergencias/$solicitudId/pagos';

  static String appClienteEmergenciaPagoCompletarSimulado(int solicitudId, int pagoId) =>
      '${AppEnv.apiBaseUrl}/app/cliente/emergencias/$solicitudId/pagos/$pagoId/completar-simulado';

  static String appClienteEmergenciaPagoConfirmarStripe(int solicitudId, int pagoId) =>
      '${AppEnv.apiBaseUrl}/app/cliente/emergencias/$solicitudId/pagos/$pagoId/confirmar-stripe';

  static String get appClienteFcm => '${AppEnv.apiBaseUrl}/app/cliente/dispositivos/fcm';

  static String get appTecnicoFcm => '${AppEnv.apiBaseUrl}/app/tecnico/dispositivos/fcm';

  static String get usuarios => '${AppEnv.apiBaseUrl}/usuarios';
  static String get vehiculos => '${AppEnv.apiBaseUrl}/vehiculos';
  static String get vehiculosMarcas => '${AppEnv.apiBaseUrl}/vehiculos/marcas';
  static String vehiculosModelos({int? marcaId}) => marcaId != null
      ? '${AppEnv.apiBaseUrl}/vehiculos/modelos?marca_id=$marcaId'
      : '${AppEnv.apiBaseUrl}/vehiculos/modelos';
  static String get vehiculosTipos => '${AppEnv.apiBaseUrl}/vehiculos/tipos';
  static String get talleres => '${AppEnv.apiBaseUrl}/talleres';

  static String tallerById(int id) => '${AppEnv.apiBaseUrl}/talleres/$id';
  static String get tecnicos => '${AppEnv.apiBaseUrl}/tecnicos';
  static String get bitacora => '${AppEnv.apiBaseUrl}/bitacora';

  static Duration get connectTimeout => AppEnv.apiConnectTimeout;
  static Duration get receiveTimeout => AppEnv.apiReceiveTimeout;
}
