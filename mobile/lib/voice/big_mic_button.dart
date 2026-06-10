import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../theme/tokens.dart';

/// Big mic button. Pulses while listening (3 ring expansion).
/// React equivalent: frontend/src/voice/BigMicButton.jsx
class BigMicButton extends StatefulWidget {
  /// 'idle' | 'listening'
  final String state;
  final VoidCallback? onTap;
  final String? ariaLabel;

  const BigMicButton({
    super.key,
    this.state = 'idle',
    this.onTap,
    this.ariaLabel,
  });

  @override
  State<BigMicButton> createState() => _BigMicButtonState();
}

class _BigMicButtonState extends State<BigMicButton>
    with TickerProviderStateMixin {
  late final AnimationController _pulse;

  @override
  void initState() {
    super.initState();
    _pulse = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1800),
    )..repeat();
  }

  @override
  void dispose() {
    _pulse.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isListening = widget.state == 'listening';
    final size = isListening ? 120.0 : 104.0;
    final bg = isListening ? FortunasColors.ink : FortunasColors.violet;
    final ringColor = isListening ? FortunasColors.violet : FortunasColors.lime;
    final iconColor = isListening ? FortunasColors.lime : Colors.white;

    return SizedBox(
      width: 160,
      height: 160,
      child: Stack(
        alignment: Alignment.center,
        children: [
          // Pulse rings while listening
          if (isListening) ..._buildPulseRings(ringColor),

          // The button itself
          Semantics(
            button: true,
            label: widget.ariaLabel ?? (isListening
                ? 'Berhenti mendengar'
                : 'Mulai mendengar'),
            child: Material(
              color: Colors.transparent,
              child: InkWell(
                onTap: () {
                  HapticFeedback.mediumImpact();
                  widget.onTap?.call();
                },
                borderRadius: BorderRadius.circular(size / 2),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 250),
                  width: size,
                  height: size,
                  decoration: BoxDecoration(
                    color: bg,
                    shape: BoxShape.circle,
                    border: Border.all(color: FortunasColors.ink, width: 2),
                    boxShadow: popShadow(offset: 4),
                  ),
                  child: Center(
                    child: Icon(Icons.mic, color: iconColor, size: size * 0.42),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  List<Widget> _buildPulseRings(Color color) {
    return List.generate(3, (i) {
      final delayFrac = i * 0.33;
      return AnimatedBuilder(
        animation: _pulse,
        builder: (_, __) {
          final t = ((_pulse.value + delayFrac) % 1.0);
          final scale = 1.0 + t * 0.7;
          final opacity = (1.0 - t).clamp(0.0, 1.0);
          return Opacity(
            opacity: opacity * 0.65,
            child: Transform.scale(
              scale: scale,
              child: Container(
                width: 120, height: 120,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(color: color, width: 2),
                ),
              ),
            ),
          );
        },
      );
    });
  }
}
