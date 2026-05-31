import 'package:flutter/material.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../../../core/utils/bolivia_time.dart';
import '../../domain/notificacion_models.dart';

class NotificacionListItem extends StatelessWidget {
  const NotificacionListItem({
    super.key,
    required this.notificacion,
    required this.onTap,
  });

  final NotificacionRead notificacion;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = ShadTheme.of(context);
    final fecha = BoliviaTime.formatWithZone(notificacion.createdAt);

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 4),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 10,
                height: 10,
                margin: const EdgeInsets.only(top: 5, right: 12),
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: notificacion.leida
                      ? theme.colorScheme.mutedForeground.withValues(alpha: 0.35)
                      : theme.colorScheme.primary,
                ),
              ),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      notificacion.titulo,
                      style: theme.textTheme.p.copyWith(
                        fontWeight: notificacion.leida ? FontWeight.w500 : FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      notificacion.mensaje,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: theme.textTheme.muted,
                    ),
                    const SizedBox(height: 6),
                    Text(fecha, style: theme.textTheme.small),
                  ],
                ),
              ),
              Icon(Icons.chevron_right, color: theme.colorScheme.mutedForeground),
            ],
          ),
        ),
      ),
    );
  }
}
