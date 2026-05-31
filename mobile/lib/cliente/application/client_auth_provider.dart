import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'client_auth_notifier.dart';
import 'client_auth_state.dart';

/// Provider de sesión cliente (expone [ClientAuthNotifier] y [ClientAuthState]).
final clientAuthNotifierProvider =
    NotifierProvider<ClientAuthNotifier, ClientAuthState>(ClientAuthNotifier.new);
