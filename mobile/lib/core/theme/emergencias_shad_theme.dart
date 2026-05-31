import 'package:flutter/material.dart';
import 'package:shadcn_ui/shadcn_ui.dart';

import 'app_theme.dart';

/// Tema Shadcn alineado con la marca EmergenciasViales (oscuro + acentos).
class EmergenciasShadTheme {
  EmergenciasShadTheme._();

  static ShadThemeData dark() {
    const indigo = Color(0xFF5C6BC0);
    const surface = Color(0xFF0B1020);
    const card = Color(0xFF141B2E);
    const border = Color(0xFF2A3658);

    return ShadThemeData(
      brightness: Brightness.dark,
      colorScheme: const ShadSlateColorScheme.dark(
        background: surface,
        foreground: Color(0xFFE8EAF6),
        card: card,
        cardForeground: Color(0xFFE8EAF6),
        popover: card,
        popoverForeground: Color(0xFFE8EAF6),
        primary: indigo,
        primaryForeground: Color(0xFFFFFFFF),
        secondary: Color(0xFF1E2740),
        secondaryForeground: AppTheme.secondaryColor,
        muted: Color(0xFF1E2740),
        mutedForeground: Color(0xFF9FA8DA),
        accent: AppTheme.secondaryColor,
        accentForeground: surface,
        border: border,
        input: border,
        ring: indigo,
      ),
    );
  }
}
