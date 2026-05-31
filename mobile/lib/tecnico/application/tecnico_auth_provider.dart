import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'tecnico_auth_notifier.dart';
import 'tecnico_auth_state.dart';

final tecnicoAuthNotifierProvider =
    NotifierProvider<TecnicoAuthNotifier, TecnicoAuthState>(TecnicoAuthNotifier.new);
