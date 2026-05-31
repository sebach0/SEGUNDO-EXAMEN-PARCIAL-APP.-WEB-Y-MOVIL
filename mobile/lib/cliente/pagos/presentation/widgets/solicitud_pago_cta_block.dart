import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../../emergencias/domain/solicitud_emergencia_models.dart';
import '../../application/pagos_providers.dart';
import '../../domain/pago_eligibility.dart';

/// Cierre del flujo CU20: botones contextualizados según estado y pagos existentes.
class SolicitudPagoCtaBlock extends ConsumerWidget {
  const SolicitudPagoCtaBlock({
    super.key,
    required this.solicitudId,
    required this.estado,
  });

  final int solicitudId;
  final EstadoSolicitudEmergencia estado;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (!solicitudPermitePago(estado)) {
      return const SizedBox.shrink();
    }

    final pagosAsync = ref.watch(pagosSolicitudProvider(solicitudId));

    return pagosAsync.when(
      loading: () => const Padding(
        padding: EdgeInsets.symmetric(vertical: 8),
        child: LinearProgressIndicator(minHeight: 2),
      ),
      error: (_, __) => const SizedBox.shrink(),
      data: (pagos) {
        final yaPagado = tienePagoConfirmado(pagos);
        if (yaPagado) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              ShadCard(
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Row(
                    children: [
                      Icon(Icons.verified_rounded, color: Theme.of(context).colorScheme.primary),
                      const SizedBox(width: 12),
                      const Expanded(
                        child: Text('Servicio con pago registrado. Podés ver el comprobante en el historial.'),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 10),
              ShadButton.outline(
                onPressed: () => context.push('/cliente/app/emergencias/solicitudes/$solicitudId/pagos'),
                child: const Text('Ver pagos'),
              ),
            ],
          );
        }

        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            ShadButton(
              onPressed: () => context.push('/cliente/app/emergencias/solicitudes/$solicitudId/pago/resumen'),
              leading: const Icon(Icons.payment_rounded, size: 20),
              child: const Text('Pagar servicio'),
            ),
            const SizedBox(height: 8),
            ShadButton.outline(
              onPressed: () => context.push('/cliente/app/emergencias/solicitudes/$solicitudId/pagos'),
              child: const Text('Historial de pagos'),
            ),
          ],
        );
      },
    );
  }
}
