import 'dart:math' as math;

import 'package:flutter/material.dart';

/// Lebar kolom untuk route phone-only di viewport lebar.
/// Nilai historis dari `PhoneFrame` — jangan diubah, layar customer
/// dirancang terhadap lebar ini.
const double kPhoneOnlyFrameWidth = 430.0;

/// Warna backdrop di sekitar kolom phone-only. Nilai historis.
const Color kPhoneOnlyBackdrop = Color(0xFFE9E4D8);

/// Ambang tier. Diukur dari lebar constraint logis, bukan pixel fisik.
const double kMediumMinWidth = 600.0;
const double kExpandedMinWidth = 1024.0;

/// Lebar baca maksimum per tier. Sengaja lebih sempit dari viewport supaya
/// satu kolom teks tidak jadi baris panjang yang melelahkan dibaca.
const double kMediumContentWidth = 720.0;
const double kExpandedContentWidth = 840.0;

/// Ruang bernapas minimum di kiri-kanan kolom konten.
const double kMediumGutter = 32.0;
const double kExpandedGutter = 48.0;

/// Tingkatan layout untuk permukaan UMKM.
enum ShellTier { compact, medium, expanded }

ShellTier shellTierFor(double width) {
  if (width >= kExpandedMinWidth) return ShellTier.expanded;
  if (width >= kMediumMinWidth) return ShellTier.medium;
  return ShellTier.compact;
}

double contentWidthFor(ShellTier tier) => switch (tier) {
      ShellTier.compact => double.infinity,
      ShellTier.medium => kMediumContentWidth,
      ShellTier.expanded => kExpandedContentWidth,
    };

double gutterFor(ShellTier tier) => switch (tier) {
      ShellTier.compact => 0.0,
      ShellTier.medium => kMediumGutter,
      ShellTier.expanded => kExpandedGutter,
    };

/// Route yang selalu dirender sebagai HP, berapa pun lebar viewport.
///
/// Alur customer dicapai dengan men-scan QR di warung — selalu dari HP
/// pelanggan sendiri, tidak pernah dari laptop. Membuatnya responsif hanya
/// menambah permukaan yang harus dirawat tanpa ada yang memakainya.
///
/// Lokasi kosong (mis. widget dirender di luar router) dianggap UMKM.
bool isPhoneOnlyRoute(String location) => location.startsWith('/customer/');

/// Membingkai konten sebuah route sesuai viewport.
///
/// Dua mode:
/// - `phoneOnly: true` — perilaku `PhoneFrame` lama dipertahankan apa adanya:
///   lebar penuh bila viewport <= 430, kalau tidak kolom 430 di tengah dengan
///   backdrop.
/// - `phoneOnly: false` — adaptif: `compact` identik lebar penuh; `medium` dan
///   `expanded` mengurung konten pada lebar baca dengan gutter terjamin.
///
/// Tinggi selalu dipaku ke `constraints.maxHeight`: tanpa itu `Scaffold` di
/// dalamnya kolaps dan bottom nav mengambang di tengah layar.
class AdaptiveShell extends StatelessWidget {
  final Widget child;
  final bool phoneOnly;

  const AdaptiveShell({
    super.key,
    required this.child,
    required this.phoneOnly,
  });

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (ctx, constraints) {
        final maxW = constraints.maxWidth;

        if (phoneOnly) {
          if (maxW <= kPhoneOnlyFrameWidth) return child;
          return _framed(constraints, kPhoneOnlyFrameWidth,
              backdrop: kPhoneOnlyBackdrop);
        }

        final tier = shellTierFor(maxW);
        if (tier == ShellTier.compact) return child;

        final gutter = gutterFor(tier);
        final available = math.max(maxW - gutter * 2, 0.0);
        final width = math.min(contentWidthFor(tier), available);
        return _framed(constraints, width);
      },
    );
  }

  Widget _framed(BoxConstraints constraints, double width, {Color? backdrop}) {
    final framed = Center(
      child: SizedBox(
        width: width,
        height: constraints.maxHeight,
        child: ClipRect(child: child),
      ),
    );
    if (backdrop == null) return framed;
    return ColoredBox(color: backdrop, child: framed);
  }
}
