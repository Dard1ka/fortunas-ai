import 'package:flutter/material.dart';

import '../theme/tokens.dart';
import 'brand_mark.dart';

/// Sticky header: brand mark + wordmark + "AI online" pill (or custom right widget).
/// React equivalent: frontend/src/ui/ScreenHeader.jsx
class ScreenHeader extends StatelessWidget {
  final String subtitle;
  final bool online;
  final Widget? trailing;

  const ScreenHeader({
    super.key,
    this.subtitle = 'UMKM Analytics',
    this.online = true,
    this.trailing,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(18, 14, 18, 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          const BrandMark(size: 36),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text.rich(
                  TextSpan(
                    children: [
                      TextSpan(
                        text: 'Fortunas ',
                        style: display(
                          fontSize: 17,
                          letterSpacing: -0.4,
                          height: 1,
                        ),
                      ),
                      TextSpan(
                        text: 'AI',
                        style: display(
                          fontSize: 17,
                          letterSpacing: -0.4,
                          height: 1,
                          color: FortunasColors.violet,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  subtitle.toUpperCase(),
                  style: mono(fontSize: 9, color: FortunasColors.ink3),
                ),
              ],
            ),
          ),
          trailing ?? _OnlinePill(online: online),
        ],
      ),
    );
  }
}

class _OnlinePill extends StatelessWidget {
  final bool online;
  const _OnlinePill({required this.online});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: FortunasColors.surface,
        border: Border.all(color: FortunasColors.ink, width: 1.5),
        borderRadius: BorderRadius.circular(999),
        boxShadow: popShadow(offset: 2),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 6,
            height: 6,
            decoration: BoxDecoration(
              color: online ? FortunasColors.success : FortunasColors.ink4,
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 6),
          Text(
            'AI online',
            style: body(
              fontSize: 10,
              weight: FontWeight.w600,
              color: FortunasColors.ink,
            ),
          ),
        ],
      ),
    );
  }
}
