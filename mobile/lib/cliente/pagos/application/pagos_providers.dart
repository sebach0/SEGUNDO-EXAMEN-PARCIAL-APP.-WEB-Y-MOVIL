import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../application/cliente_injection.dart';
import '../domain/pago_models.dart';

/// Pagos registrados para una solicitud (historial + detección de ya pagado).
final pagosSolicitudProvider =
    FutureProvider.autoDispose.family<List<PagoRead>, int>((ref, solicitudId) async {
  final repo = ref.watch(pagosRepositoryProvider);
  return repo.listarPorSolicitud(solicitudId);
});

bool tienePagoConfirmado(List<PagoRead> pagos) {
  return pagos.any((p) => p.estado == EstadoPago.pagado);
}
