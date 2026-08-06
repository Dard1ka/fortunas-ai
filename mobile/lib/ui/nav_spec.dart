import 'package:flutter/foundation.dart';

/// Satu slot navigasi utama UMKM.
///
/// Dipakai bersama oleh [FortunasBottomNav] (viewport compact) dan
/// [FortunasNavRail] (viewport lebar) supaya keduanya tidak bisa berbeda isi.
@immutable
class NavSpec {
  final String id;
  final String label;

  /// Nama ikon untuk `AppIcon` di `lib/ui/icon_set.dart`.
  final String icon;
  final String path;

  /// True untuk aksi utama (mic FAB violet) — dirender berbeda, bukan tab biasa.
  final bool primary;

  const NavSpec({
    required this.id,
    required this.label,
    required this.icon,
    required this.path,
    this.primary = false,
  });
}

/// 5 tab utama UMKM. Urutan = urutan tampil.
const List<NavSpec> kUmkmNavItems = <NavSpec>[
  NavSpec(id: 'home', label: 'Tanya', icon: 'chat', path: '/'),
  NavSpec(id: 'briefing', label: 'Briefing', icon: 'chart', path: '/briefing'),
  NavSpec(id: 'voice', label: 'Voice', icon: 'mic', path: '/voice', primary: true),
  NavSpec(id: 'history', label: 'Riwayat', icon: 'history', path: '/history'),
  NavSpec(id: 'me', label: 'Saya', icon: 'user', path: '/me'),
];

/// Apakah [itemPath] adalah tab aktif untuk lokasi [location] saat ini.
///
/// Tab `/` juga memiliki `/result`, karena hasil jawaban dirender sebagai
/// kelanjutan dari tab Tanya — bukan tab tersendiri.
bool navItemIsActive(String itemPath, String location) {
  if (itemPath == '/' && (location == '/' || location.startsWith('/result'))) {
    return true;
  }
  return itemPath == location;
}
