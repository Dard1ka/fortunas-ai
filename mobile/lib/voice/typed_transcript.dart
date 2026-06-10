import 'package:flutter/material.dart';
import '../theme/tokens.dart';

/// Live transcript display with a blinking caret.
/// React equivalent: frontend/src/voice/TypedTranscript.jsx
class TypedTranscript extends StatefulWidget {
  final String text;
  final String placeholder;

  const TypedTranscript({
    super.key,
    required this.text,
    this.placeholder = 'Sebut transaksi…',
  });

  @override
  State<TypedTranscript> createState() => _TypedTranscriptState();
}

class _TypedTranscriptState extends State<TypedTranscript>
    with SingleTickerProviderStateMixin {
  late final AnimationController _caret;

  @override
  void initState() {
    super.initState();
    _caret = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 1),
    )..repeat();
  }

  @override
  void dispose() {
    _caret.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final empty = widget.text.isEmpty;
    return ConstrainedBox(
      constraints: const BoxConstraints(minHeight: 84),
      child: AnimatedBuilder(
        animation: _caret,
        builder: (_, __) {
          // Toggle caret on/off every 0.5s (step function)
          final showCaret = _caret.value < 0.5;
          return Text.rich(
            TextSpan(
              children: [
                TextSpan(
                  text: empty ? widget.placeholder : widget.text,
                  style: display(
                    fontSize: 18,
                    weight: FontWeight.w500,
                    letterSpacing: -0.18,
                    height: 1.45,
                    color: empty ? FortunasColors.ink3 : FortunasColors.ink,
                  ),
                ),
                WidgetSpan(
                  alignment: PlaceholderAlignment.middle,
                  child: AnimatedOpacity(
                    opacity: showCaret ? 1.0 : 0.0,
                    duration: Duration.zero,
                    child: Container(
                      width: 2, height: 18,
                      margin: const EdgeInsets.only(left: 2),
                      color: FortunasColors.violet,
                    ),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}
