import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../theme/tokens.dart';
import 'icon_set.dart';
import 'nav_spec.dart';

/// Lebar rail saat ikon saja (tier medium).
const double kNavRailWidth = 76.0;

/// Lebar rail saat ikon + label (tier expanded).
const double kNavRailExtendedWidth = 200.0;

/// Navigasi utama UMKM versi vertikal, untuk viewport lebar.
///
/// Isi slotnya berasal dari [kUmkmNavItems] — sumber yang sama dengan
/// [FortunasBottomNav], jadi keduanya tidak bisa berbeda. Mic FAB violet tetap
/// aksi utama dan diletakkan di puncak rail.
class FortunasNavRail extends StatelessWidget {
  final String currentLocation;

  /// Tampilkan label teks di samping ikon (tier expanded).
  final bool extended;

  const FortunasNavRail({
    super.key,
    required this.currentLocation,
    this.extended = false,
  });

  @override
  Widget build(BuildContext context) {
    final tabs = kUmkmNavItems.where((i) => !i.primary);
    final fab = kUmkmNavItems.firstWhere((i) => i.primary);

    return Container(
      key: const Key('nav_rail'),
      width: extended ? kNavRailExtendedWidth : kNavRailWidth,
      decoration: const BoxDecoration(
        color: FortunasColors.surface,
        border: Border(
          right: BorderSide(color: FortunasColors.ink, width: 1.5),
        ),
      ),
      child: SafeArea(
        right: false,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const SizedBox(height: 16),
            _RailFab(item: fab, extended: extended),
            const SizedBox(height: 20),
            for (final item in tabs)
              _RailItem(
                item: item,
                active: navItemIsActive(item.path, currentLocation),
                extended: extended,
              ),
          ],
        ),
      ),
    );
  }
}

class _RailFab extends StatelessWidget {
  final NavSpec item;
  final bool extended;
  const _RailFab({required this.item, required this.extended});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          key: Key('rail_${item.id}'),
          onTap: () => context.push(item.path),
          borderRadius: BorderRadius.circular(16),
          child: Container(
            key: const Key('rail_voice_fab'),
            height: 52,
            decoration: BoxDecoration(
              color: FortunasColors.violet,
              border: Border.all(color: FortunasColors.ink, width: 1.5),
              borderRadius: BorderRadius.circular(16),
              boxShadow: popShadow(offset: 3),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.mic, color: Colors.white, size: 24),
                if (extended) ...[
                  const SizedBox(width: 8),
                  Text(item.label,
                      style: body(
                          fontSize: 13,
                          weight: FontWeight.w700,
                          color: Colors.white)),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _RailItem extends StatelessWidget {
  final NavSpec item;
  final bool active;
  final bool extended;
  const _RailItem({
    required this.item,
    required this.active,
    required this.extended,
  });

  @override
  Widget build(BuildContext context) {
    final color = active ? FortunasColors.ink : FortunasColors.ink4;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      child: Material(
        color: active ? FortunasColors.violetSoft : Colors.transparent,
        borderRadius: BorderRadius.circular(12),
        child: InkWell(
          key: Key('rail_${item.id}'),
          onTap: () => context.go(item.path),
          borderRadius: BorderRadius.circular(12),
          child: Padding(
            padding: EdgeInsets.symmetric(
                horizontal: extended ? 12 : 0, vertical: 10),
            child: extended
                ? Row(children: [
                    AppIcon(name: item.icon, size: 20, color: color),
                    const SizedBox(width: 12),
                    Text(item.label,
                        style: body(
                          fontSize: 13,
                          weight: active ? FontWeight.w700 : FontWeight.w500,
                          color: color,
                        )),
                  ])
                : Center(
                    child: AppIcon(name: item.icon, size: 20, color: color)),
          ),
        ),
      ),
    );
  }
}
