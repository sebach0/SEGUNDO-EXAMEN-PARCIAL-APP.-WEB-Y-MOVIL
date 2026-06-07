import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import '../../application/client_auth_provider.dart';
import '../../application/cliente_injection.dart';

class ClientePerfilScreen extends ConsumerStatefulWidget {
  const ClientePerfilScreen({super.key});

  @override
  ConsumerState<ClientePerfilScreen> createState() => _ClientePerfilScreenState();
}

class _ClientePerfilScreenState extends ConsumerState<ClientePerfilScreen> {
  final _nombres = TextEditingController();
  final _apellidos = TextEditingController();
  final _telefono = TextEditingController();
  final _ciudad = TextEditingController();
  final _direccion = TextEditingController();

  bool _saving = false;
  String? _error;
  String? _ok;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _syncFromProfile());
  }

  void _syncFromProfile() {
    final p = ref.read(clientAuthNotifierProvider).profile;
    if (p == null) return;
    _nombres.text = p.nombres;
    _apellidos.text = p.apellidos;
    _telefono.text = p.telefono;
    _ciudad.text = p.ciudad ?? '';
    _direccion.text = p.direccion ?? '';
    setState(() {});
  }

  @override
  void dispose() {
    _nombres.dispose();
    _apellidos.dispose();
    _telefono.dispose();
    _ciudad.dispose();
    _direccion.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    setState(() {
      _saving = true;
      _error = null;
      _ok = null;
    });
    final authRepo = ref.read(authRepositoryProvider);
    try {
      final updated = await authRepo.updateMiPerfil(
        nombres: _nombres.text.trim(),
        apellidos: _apellidos.text.trim(),
        telefono: _telefono.text.trim(),
        ciudad: _ciudad.text.trim(),
        direccion: _direccion.text.trim(),
      );
      ref.read(clientAuthNotifierProvider.notifier).replaceProfileAfterUpdate(updated);
      setState(() => _ok = 'Cambios guardados.');
    } catch (e) {
      setState(() => _error = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  bool _loggingOut = false;

  Future<void> _confirmLogout() async {
    if (_loggingOut) return;
    final ok = await showDialog<bool>(
      context: context,
      useRootNavigator: true,
      barrierDismissible: true,
      builder: (ctx) => AlertDialog(
        title: const Text('Cerrar sesión'),
        content: const Text('¿Seguro que deseas salir de la aplicación?'),
        actions: [
          TextButton(onPressed: () => Navigator.of(ctx, rootNavigator: true).pop(false), child: const Text('Cancelar')),
          FilledButton(
            onPressed: () => Navigator.of(ctx, rootNavigator: true).pop(true),
            child: const Text('Cerrar sesión'),
          ),
        ],
      ),
    );
    if (ok != true || !mounted) return;
    setState(() => _loggingOut = true);
    try {
      await ref.read(clientAuthNotifierProvider.notifier).logout();
      if (mounted) context.go('/cliente/login');
    } finally {
      if (mounted) setState(() => _loggingOut = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final profile = ref.watch(clientAuthNotifierProvider).profile;
    return Scaffold(
      appBar: AppBar(title: const Text('Perfil')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          if (profile != null)
            Text(profile.email, style: Theme.of(context).textTheme.labelLarge),
          const SizedBox(height: 16),
          Text('Nombres', style: Theme.of(context).textTheme.labelLarge),
          ShadInput(controller: _nombres),
          const SizedBox(height: 12),
          Text('Apellidos', style: Theme.of(context).textTheme.labelLarge),
          ShadInput(controller: _apellidos),
          const SizedBox(height: 12),
          Text('Teléfono', style: Theme.of(context).textTheme.labelLarge),
          ShadInput(controller: _telefono, keyboardType: TextInputType.phone),
          const SizedBox(height: 12),
          Text('Ciudad', style: Theme.of(context).textTheme.labelLarge),
          ShadInput(controller: _ciudad, placeholder: const Text('Opcional')),
          const SizedBox(height: 12),
          Text('Dirección', style: Theme.of(context).textTheme.labelLarge),
          ShadInput(controller: _direccion, placeholder: const Text('Opcional'), maxLines: 3),
          if (_error != null) ...[
            const SizedBox(height: 12),
            Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
          ],
          if (_ok != null) ...[
            const SizedBox(height: 12),
            Text(_ok!, style: TextStyle(color: Theme.of(context).colorScheme.secondary)),
          ],
          const SizedBox(height: 20),
          ShadButton(
            onPressed: _saving ? null : _save,
            child: _saving
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Text('Guardar cambios'),
          ),
          const SizedBox(height: 24),
          OutlinedButton(
            onPressed: _loggingOut ? null : _confirmLogout,
            child: _loggingOut
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Text('Cerrar sesión'),
          ),
        ],
      ),
    );
  }
}
