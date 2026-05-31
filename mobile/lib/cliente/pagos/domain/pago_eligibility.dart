import '../../emergencias/domain/solicitud_emergencia_models.dart';

/// Alineado con backend: solo en atención o finalizada se puede iniciar cobro.
bool solicitudPermitePago(EstadoSolicitudEmergencia estado) {
  return estado == EstadoSolicitudEmergencia.enAtencion ||
      estado == EstadoSolicitudEmergencia.finalizada;
}
