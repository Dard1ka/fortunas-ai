import 'package:flutter/material.dart';
import '../theme/tokens.dart';

/// Tappable suggestion chip — pop-shadow brutalist style.
/// React equivalent: frontend/src/ui/ExampleChip.jsx
class ExampleChip extends StatelessWidget {
  final String text;
  final VoidCallback? onTap;

  const ExampleChip({super.key, required this.text, this.onTap});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(FortunasRadius.md),
        child: Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          decoration: BoxDecoration(
            color: FortunasColors.surface,
            border: Border.all(color: FortunasColors.ink, width: 1.5),
            borderRadius: BorderRadius.circular(FortunasRadius.md),
            boxShadow: popShadow(offset: 2),
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Icon(Icons.arrow_forward, size: 15, color: FortunasColors.ink4),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  text,
                  style: body(
                    fontSize: 13,
                    weight: FontWeight.w500,
                    color: FortunasColors.ink,
                    height: 1.4,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
