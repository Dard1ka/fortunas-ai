import 'dart:math' as math;
import 'package:flutter/material.dart';

import '../theme/tokens.dart';

/// 28 staggered animated bars — voice activity indicator.
/// React equivalent: frontend/src/voice/Waveform.jsx
class Waveform extends StatefulWidget {
  final bool active;
  final Color color;
  final int count;

  const Waveform({
    super.key,
    this.active = true,
    this.color = FortunasColors.violet,
    this.count = 28,
  });

  @override
  State<Waveform> createState() => _WaveformState();
}

class _WaveformState extends State<Waveform> with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 80,
      child: AnimatedBuilder(
        animation: _ctrl,
        builder: (_, __) {
          return Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(widget.count, (i) {
              final seed = (math.sin(i * 1.27) + 1) * 0.5;
              final phaseShift = (i % 7) * 0.14 + seed * 0.3;
              final phase = (_ctrl.value + phaseShift) % 1.0;
              final scale = widget.active
                  ? (0.18 + (math.sin(phase * math.pi) * 0.82).abs()).clamp(0.18, 1.0)
                  : 0.35;
              final tall = 18.0 + math.sin(i * 0.7).abs() * 56.0;
              return Padding(
                padding: const EdgeInsets.symmetric(horizontal: 2.5),
                child: SizedBox(
                  width: 4,
                  height: tall,
                  child: FractionallySizedBox(
                    heightFactor: scale,
                    child: DecoratedBox(
                      decoration: BoxDecoration(
                        color: widget.color,
                        borderRadius: BorderRadius.circular(999),
                      ),
                    ),
                  ),
                ),
              );
            }),
          );
        },
      ),
    );
  }
}
