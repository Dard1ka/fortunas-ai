import 'package:flutter/material.dart';
import '../theme/tokens.dart';

/// Pill toggle for primary tabs (Tanya / Briefing / Harian).
/// React equivalent: frontend/src/ui/ModeTabs.jsx
class ModeTabs extends StatelessWidget {
  final List<({String id, String label})> tabs;
  final String value;
  final ValueChanged<String> onChanged;

  const ModeTabs({
    super.key,
    required this.tabs,
    required this.value,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 18),
      child: Container(
        padding: const EdgeInsets.all(3),
        decoration: BoxDecoration(
          color: FortunasColors.surface,
          border: Border.all(color: FortunasColors.ink, width: 1.5),
          borderRadius: BorderRadius.circular(999),
          boxShadow: popShadow(offset: 2),
        ),
        child: IntrinsicHeight(
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              for (final t in tabs) _Tab(
                label: t.label,
                active: value == t.id,
                onTap: () => onChanged(t.id),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Tab extends StatelessWidget {
  final String label;
  final bool active;
  final VoidCallback onTap;
  const _Tab({required this.label, required this.active, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(999),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
          decoration: BoxDecoration(
            color: active ? FortunasColors.ink : Colors.transparent,
            borderRadius: BorderRadius.circular(999),
          ),
          child: Text(
            label,
            style: body(
              fontSize: 12,
              weight: FontWeight.w600,
              color: active ? FortunasColors.lime : FortunasColors.ink3,
            ),
          ),
        ),
      ),
    );
  }
}
