import 'package:flutter/material.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../../../core/utils/bolivia_time.dart';

class ChatBubble extends StatelessWidget {
  const ChatBubble({
    super.key,
    required this.texto,
    required this.hora,
    required this.esMio,
  });

  final String texto;
  final DateTime hora;
  final bool esMio;

  @override
  Widget build(BuildContext context) {
    final theme = ShadTheme.of(context);
    final horaStr = BoliviaTime.formatWithZone(hora, pattern: 'HH:mm');

    return Align(
      alignment: esMio ? Alignment.centerRight : Alignment.centerLeft,
      child: ConstrainedBox(
        constraints: BoxConstraints(maxWidth: MediaQuery.sizeOf(context).width * 0.82),
        child: DecoratedBox(
          decoration: BoxDecoration(
            color: esMio
                ? theme.colorScheme.primary.withValues(alpha: 0.15)
                : theme.colorScheme.muted,
            borderRadius: BorderRadius.only(
              topLeft: const Radius.circular(14),
              topRight: const Radius.circular(14),
              bottomLeft: Radius.circular(esMio ? 14 : 4),
              bottomRight: Radius.circular(esMio ? 4 : 14),
            ),
            border: Border.all(color: theme.colorScheme.border),
          ),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            child: Column(
              crossAxisAlignment: esMio ? CrossAxisAlignment.end : CrossAxisAlignment.start,
              children: [
                Text(texto, style: theme.textTheme.p),
                const SizedBox(height: 4),
                Text(horaStr, style: theme.textTheme.small),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
