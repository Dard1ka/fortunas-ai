/// Fortunas AI design tokens. Direct port from frontend/src/theme/tokens.css
/// and the design hand-off artboard "08 · React → Flutter mapping" which
/// provides this exact color_tokens.dart shape.
library;
import 'package:flutter/material.dart';

/// Brand palette — neo-brutalist (cream + ink + violet + lime).
class FortunasColors {
  // Surfaces
  static const bg          = Color(0xFFFAF7F0);
  static const bgAlt       = Color(0xFFF3EFE4);
  static const surface     = Color(0xFFFFFFFF);
  static const surfaceSoft = Color(0xFFF7F4EC);
  static const surfaceHover= Color(0xFFF0ECDF);

  // Borders
  static const border      = Color(0xFF1A1A22);
  static const borderSoft  = Color(0xFFE5E0D2);
  static const borderHair  = Color(0x141A1A22); // rgba(26,26,34,0.08)

  // Accents
  static const violet      = Color(0xFF6D5EF7);
  static const violetDeep  = Color(0xFF4B3DD6);
  static const violetSoft  = Color(0xFFEDEAFE);
  static const lime        = Color(0xFFD4F56A);
  static const limeDeep    = Color(0xFFA8D939);
  static const peach       = Color(0xFFFFB4A2);
  static const peachSoft   = Color(0xFFFFE7DF);
  static const sky         = Color(0xFF9BD4FF);

  // Ink (text)
  static const ink   = Color(0xFF0E0E14);
  static const ink2  = Color(0xFF2A2A35);
  static const ink3  = Color(0xFF5C5C6A);
  static const ink4  = Color(0xFF8B8B98);

  // Semantic
  static const success = Color(0xFF1EB980);
  static const warning = Color(0xFFF5A623);
  static const error   = Color(0xFFEF4444);
}

class FortunasRadius {
  static const sm   = 8.0;
  static const md   = 14.0;
  static const lg   = 18.0;
  static const xl   = 24.0;
  static const pill = 999.0;
}

/// The neo-brutalist pop shadow.
/// CSS equivalent: `box-shadow: 4px 4px 0 var(--ink)`.
List<BoxShadow> popShadow({double offset = 4}) => [
  BoxShadow(
    color: FortunasColors.ink,
    offset: Offset(offset, offset),
    blurRadius: 0,
    spreadRadius: 0,
  ),
];

// ─── Typography helpers ───────────────────────────────────────────
// Fonts are BUNDLED as assets (variable TTFs) — see pubspec.yaml. No
// runtime network fetch, so the app renders offline and never hits the
// CanvasKit "null font bytes" crash that google_fonts could cause.

TextStyle display({
  double fontSize = 26,
  FontWeight weight = FontWeight.w700,
  double letterSpacing = -0.7,
  double height = 1.1,
  Color color = FortunasColors.ink,
}) => TextStyle(
  fontFamily: 'SpaceGrotesk',
  fontSize: fontSize,
  fontWeight: weight,
  letterSpacing: letterSpacing,
  height: height,
  color: color,
);

TextStyle body({
  double fontSize = 13,
  FontWeight weight = FontWeight.w400,
  double height = 1.5,
  Color color = FortunasColors.ink2,
}) => TextStyle(
  fontFamily: 'Inter',
  fontSize: fontSize,
  fontWeight: weight,
  height: height,
  color: color,
);

TextStyle mono({
  double fontSize = 10,
  FontWeight weight = FontWeight.w700,
  double letterSpacing = 0.8,
  Color color = FortunasColors.ink3,
}) => TextStyle(
  fontFamily: 'JetBrainsMono',
  fontSize: fontSize,
  fontWeight: weight,
  letterSpacing: letterSpacing,
  color: color,
);

ThemeData buildFortunasTheme() {
  return ThemeData(
    useMaterial3: true,
    scaffoldBackgroundColor: FortunasColors.bg,
    colorScheme: const ColorScheme.light(
      primary:     FortunasColors.violet,
      onPrimary:   Colors.white,
      secondary:   FortunasColors.lime,
      onSecondary: FortunasColors.ink,
      surface:     FortunasColors.surface,
      onSurface:   FortunasColors.ink,
      error:       FortunasColors.error,
      onError:     Colors.white,
    ),
    fontFamily: 'Inter',
    textTheme: const TextTheme().apply(
      bodyColor: FortunasColors.ink2,
      displayColor: FortunasColors.ink,
      fontFamily: 'Inter',
    ),
    splashFactory: InkRipple.splashFactory,
  );
}
