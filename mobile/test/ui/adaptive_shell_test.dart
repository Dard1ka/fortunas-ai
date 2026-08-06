import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/ui/adaptive_shell.dart';

/// Setel viewport logis ke [width] x [height] untuk satu test.
void _setViewport(WidgetTester tester, double width, double height) {
  tester.view.devicePixelRatio = 1.0;
  tester.view.physicalSize = Size(width, height);
  addTearDown(tester.view.reset);
}

/// Lebar aktual yang diterima [child] di dalam shell.
///
/// Kunci `probe` HARUS berada di widget yang meregang (`SizedBox.expand`),
/// bukan di `Text` — `getSize` pada Text mengukur lebar glyph, bukan lebar
/// kolom yang diberikan shell.
Future<double> _renderedChildWidth(
  WidgetTester tester, {
  required bool phoneOnly,
}) async {
  await tester.pumpWidget(MaterialApp(
    home: AdaptiveShell(
      phoneOnly: phoneOnly,
      child: const SizedBox.expand(key: Key('probe')),
    ),
  ));
  await tester.pumpAndSettle();
  return tester.getSize(find.byKey(const Key('probe'))).width;
}

void main() {
  group('shellTierFor', () {
    test('batas compact/medium tepat di 600', () {
      expect(shellTierFor(599.9), ShellTier.compact);
      expect(shellTierFor(600.0), ShellTier.medium);
    });

    test('batas medium/expanded tepat di 1024', () {
      expect(shellTierFor(1023.9), ShellTier.medium);
      expect(shellTierFor(1024.0), ShellTier.expanded);
    });

    test('lebar HP tetap compact', () {
      expect(shellTierFor(390.0), ShellTier.compact);
    });
  });

  group('isPhoneOnlyRoute', () {
    test('semua route customer phone-only', () {
      for (final p in [
        '/customer/login',
        '/customer/otp',
        '/customer/profile',
        '/customer/home',
        '/customer/history',
        '/customer/qr',
        '/customer/points',
        '/customer/menu',
        '/customer/promo',
      ]) {
        expect(isPhoneOnlyRoute(p), isTrue, reason: p);
      }
    });

    test('route UMKM tidak phone-only', () {
      for (final p in ['/', '/briefing', '/result', '/history', '/me', '/dpa',
                       '/checkout', '/products', '/orders', '/scan', '/voice',
                       '/login', '/register', '/splash']) {
        expect(isPhoneOnlyRoute(p), isFalse, reason: p);
      }
    });

    test('lokasi kosong (di luar router) dianggap bukan phone-only', () {
      expect(isPhoneOnlyRoute(''), isFalse);
    });
  });

  group('AdaptiveShell adaptif (phoneOnly: false)', () {
    testWidgets('compact: child memakai lebar penuh', (tester) async {
      _setViewport(tester, 390, 844);
      expect(await _renderedChildWidth(tester, phoneOnly: false), 390.0);
    });

    testWidgets('medium: child dibatasi 720', (tester) async {
      _setViewport(tester, 900, 800);
      expect(await _renderedChildWidth(tester, phoneOnly: false),
          kMediumContentWidth);
    });

    testWidgets('expanded: child dibatasi 840', (tester) async {
      _setViewport(tester, 1440, 900);
      expect(await _renderedChildWidth(tester, phoneOnly: false),
          kExpandedContentWidth);
    });

    testWidgets('gutter dijamin saat viewport hanya sedikit di atas content',
        (tester) async {
      // 740 lebar: 720 content akan menyisakan 10px per sisi tanpa gutter.
      // Gutter 32 harus menang → child jadi 740 - 64 = 676.
      _setViewport(tester, 740, 800);
      expect(await _renderedChildWidth(tester, phoneOnly: false),
          740.0 - kMediumGutter * 2);
    });
  });

  group('AdaptiveShell phone-only (phoneOnly: true)', () {
    testWidgets('viewport lebar tetap dikurung 430', (tester) async {
      _setViewport(tester, 1440, 900);
      expect(await _renderedChildWidth(tester, phoneOnly: true),
          kPhoneOnlyFrameWidth);
    });

    testWidgets('viewport HP tetap lebar penuh (tanpa bingkai)', (tester) async {
      _setViewport(tester, 390, 844);
      expect(await _renderedChildWidth(tester, phoneOnly: true), 390.0);
    });
  });
}
