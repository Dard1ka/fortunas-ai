import 'package:flutter/material.dart';
import '../theme/tokens.dart';

/// Pill badge with 1.5px ink border. Used for status chips, kicker labels.
/// React equivalent: frontend/src/ui/Pill.jsx
class Pill extends StatelessWidget {
  final Widget child;
  final Color background;
  final Color foreground;
  final bool small;

  const Pill({
    super.key,
    required this.child,
    this.background = FortunasColors.lime,
    this.foreground = FortunasColors.ink,
    this.small = false,
  });

  /// Convenience constructor for text-only pills.
  factory Pill.text(
    String text, {
    Color background = FortunasColors.lime,
    Color foreground = FortunasColors.ink,
    bool small = false,
    bool monoFont = false,
  }) {
    final style = monoFont
        ? mono(
            fontSize: small ? 10 : 11,
            color: foreground,
            weight: FontWeight.w600,
            letterSpacing: 0.4,
          )
        : body(
            fontSize: small ? 10 : 11,
            weight: FontWeight.w600,
            color: foreground,
          );
    return Pill(
      background: background,
      foreground: foreground,
      small: small,
      child: Text(text, style: style),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: small ? 8 : 10,
        vertical: small ? 3 : 4,
      ),
      decoration: BoxDecoration(
        color: background,
        border: Border.all(color: FortunasColors.ink, width: 1.5),
        borderRadius: BorderRadius.circular(999),
      ),
      child: child,
    );
  }
}
