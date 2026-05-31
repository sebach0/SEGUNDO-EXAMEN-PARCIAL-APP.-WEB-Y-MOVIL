import 'package:flutter/material.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

/// Campo de texto + enviar (CU21).
class ChatComposer extends StatefulWidget {
  const ChatComposer({
    super.key,
    required this.onEnviar,
    this.habilitado = true,
    this.enviando = false,
  });

  final Future<void> Function(String texto) onEnviar;
  final bool habilitado;
  final bool enviando;

  @override
  State<ChatComposer> createState() => _ChatComposerState();
}

class _ChatComposerState extends State<ChatComposer> {
  final _controller = TextEditingController();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final t = _controller.text.trim();
    if (t.isEmpty || !widget.habilitado || widget.enviando) return;
    await widget.onEnviar(t);
    if (mounted) _controller.clear();
  }

  @override
  Widget build(BuildContext context) {
    final theme = ShadTheme.of(context);

    return SafeArea(
      top: false,
      child: Material(
        elevation: 8,
        color: theme.colorScheme.background,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(12, 8, 12, 8),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Expanded(
                child: ShadInput(
                  controller: _controller,
                  placeholder: const Text('Escribí un mensaje…'),
                  maxLines: 4,
                  minLines: 1,
                  enabled: widget.habilitado && !widget.enviando,
                  textInputAction: TextInputAction.send,
                ),
              ),
              const SizedBox(width: 8),
              ShadButton(
                onPressed: widget.habilitado && !widget.enviando ? _submit : null,
                child: widget.enviando
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.send_rounded, size: 20),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
