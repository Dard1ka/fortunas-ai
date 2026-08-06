import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../theme/tokens.dart';
import 'icon_set.dart';
import 'nav_spec.dart';

/// 5-slot pill bar with the violet mic FAB raised in the middle.
/// React equivalent: frontend/src/ui/BottomNav.jsx
class FortunasBottomNav extends StatelessWidget {
  final String currentLocation;
  const FortunasBottomNav({super.key, required this.currentLocation});

  static const _items = kUmkmNavItems;

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.of(context).padding.bottom;
    return Container(
      padding: EdgeInsets.fromLTRB(12, 8, 12, 8 + (bottomInset > 0 ? bottomInset : 8)),
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.bottomCenter,
          end: Alignment.topCenter,
          colors: [
            Color(0xFAFAF7F0),
            Color(0x00FAF7F0),
          ],
          stops: [0.6, 1.0],
        ),
      ),
      child: Container(
        decoration: BoxDecoration(
          color: FortunasColors.surface,
          border: Border.all(color: FortunasColors.ink, width: 1.5),
          borderRadius: BorderRadius.circular(24),
          boxShadow: popShadow(offset: 3),
        ),
        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 8),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            for (final item in _items)
              Expanded(
                child: item.primary
                    ? _MicFab(onTap: () => context.push(item.path))
                    : _NavItem(
                        item: item,
                        active: navItemIsActive(item.path, currentLocation),
                        onTap: () => context.go(item.path),
                      ),
              ),
          ],
        ),
      ),
    );
  }
}

class _NavItem extends StatelessWidget {
  final NavSpec item;
  final bool active;
  final VoidCallback onTap;

  const _NavItem({required this.item, required this.active, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final color = active ? FortunasColors.ink : FortunasColors.ink4;
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 6),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              AppIcon(name: item.icon, size: 20, color: color),
              const SizedBox(height: 3),
              Text(
                item.label,
                style: body(
                  fontSize: 10,
                  weight: active ? FontWeight.w700 : FontWeight.w500,
                  color: color,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _MicFab extends StatelessWidget {
  final VoidCallback onTap;
  const _MicFab({required this.onTap});

  @override
  Widget build(BuildContext context) {
    // heightFactor: 1 sizes this to the child's height instead of expanding
    // to fill the bar's (loose) max height — otherwise it stretches the
    // whole nav bar to full screen height.
    return Align(
      alignment: Alignment.center,
      heightFactor: 1,
      child: Transform.translate(
        offset: const Offset(0, -22),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: onTap,
            borderRadius: BorderRadius.circular(16),
            child: Container(
              width: 52,
              height: 52,
              decoration: BoxDecoration(
                color: FortunasColors.violet,
                border: Border.all(color: FortunasColors.ink, width: 1.5),
                borderRadius: BorderRadius.circular(16),
                boxShadow: popShadow(offset: 3),
              ),
              child: const Icon(Icons.mic, color: Colors.white, size: 24),
            ),
          ),
        ),
      ),
    );
  }
}
