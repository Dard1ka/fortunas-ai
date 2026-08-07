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

    testWidgets(
        'expanded: kExpandedGutter tidak pernah dites lewat viewport — '
        'kunci margin tersempit di ambang 1024', (tester) async {
      // Beda dari tier medium: di expanded, kExpandedContentWidth(840) +
      // 2*kExpandedGutter(96) = 936, LEBIH KECIL dari kExpandedMinWidth
      // (1024). Artinya begitu viewport masuk tier expanded, "available"
      // (viewport - 96) sudah >= 1024-96 = 928 > 840 — content SELALU
      // menang, tidak ada viewport dalam tier ini yang membuat gutter
      // menang. Test ini mengunci kasus margin tersempit yang bisa dicapai
      // (ambang tier itu sendiri, 1024): kalau kExpandedGutter naik lewat
      // ~92 (atau kExpandedContentWidth naik / kExpandedMinWidth turun),
      // "available" di titik ini akan turun di bawah 840 dan test ini
      // gagal — melindungi kExpandedGutter dari boleh diubah ke berapa pun
      // tanpa ketahuan, meski gutter belum pernah benar-benar "menang" di
      // rendering pada tier ini.
      _setViewport(tester, kExpandedMinWidth, 800);
      expect(await _renderedChildWidth(tester, phoneOnly: false),
          kExpandedContentWidth);
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

    testWidgets('backdrop di sekitar kolom pakai kPhoneOnlyBackdrop',
        (tester) async {
      _setViewport(tester, 1440, 900);
      await tester.pumpWidget(MaterialApp(
        home: AdaptiveShell(
          phoneOnly: true,
          child: const SizedBox.expand(key: Key('probe')),
        ),
      ));
      await tester.pumpAndSettle();
      final coloredBox = tester.widget<ColoredBox>(find.byType(ColoredBox));
      expect(coloredBox.color, kPhoneOnlyBackdrop);
    });
  });

  group('AdaptiveShell adaptif tidak punya backdrop', () {
    testWidgets('jalur adaptif (bukan phone-only) tidak merender ColoredBox',
        (tester) async {
      // Backdrop hanya milik jalur phone-only. Kalau suatu saat _framed
      // dipanggil dengan backdrop di jalur adaptif juga (regresi), test ini
      // akan menemukan sebuah ColoredBox yang seharusnya tidak ada.
      _setViewport(tester, 1440, 900);
      await tester.pumpWidget(MaterialApp(
        home: AdaptiveShell(
          phoneOnly: false,
          child: const SizedBox.expand(key: Key('probe')),
        ),
      ));
      await tester.pumpAndSettle();
      expect(find.byType(ColoredBox), findsNothing);
    });
  });

  group('AdaptiveShell mengunci tinggi (height: constraints.maxHeight)', () {
    testWidgets(
        'Scaffold + bottomNavigationBar tetap mengisi tinggi penuh viewport',
        (tester) async {
      // Scaffold nyatanya "greedy": RenderObject di baliknya
      // (RenderCustomMultiChildLayoutBox) memakai constraints.biggest untuk
      // ukuran dirinya sendiri, jadi ia akan selalu mengisi tinggi maksimum
      // yang tersedia — tight ATAU loose sama saja. Artinya baris
      // `height: constraints.maxHeight` di _framed TIDAK menjadi penentu
      // untuk kasus Scaffold spesifik ini (terverifikasi lewat percobaan
      // manual: menghapus baris itu tidak mengubah hasil test ini sama
      // sekali). Test ini tetap berguna sebagai regresi "Scaffold mengisi
      // shell", tapi baris yang benar-benar didokumentasikan sebagai
      // load-bearing (adaptive_shell.dart:64-66) baru diuji secara nyata
      // oleh test berikutnya, yang memakai child yang TIDAK greedy.
      _setViewport(tester, 1440, 900);
      await tester.pumpWidget(MaterialApp(
        home: AdaptiveShell(
          phoneOnly: false,
          child: Scaffold(
            key: const Key('probe_scaffold'),
            body: const SizedBox.shrink(),
            bottomNavigationBar: const SizedBox(height: 56),
          ),
        ),
      ));
      await tester.pumpAndSettle();
      expect(
        tester.getSize(find.byKey(const Key('probe_scaffold'))).height,
        900.0,
      );
    });

    testWidgets(
        'child yang tidak "greedy" tetap dipaku ke tinggi penuh, tidak '
        'mengambang di tengah viewport', (tester) async {
      // Ini reproduksi nyata dari cerita di dokumentasi kelas: tanpa
      // `height: constraints.maxHeight`, Center di _framed akan
      // MEMUSATKAN child yang menyusut ke tinggi isinya sendiri —
      // persis "bottom nav mengambang di tengah layar". Column dengan
      // mainAxisSize.min (bukan Scaffold — Scaffold terbukti kebal, lihat
      // test di atas) adalah child yang benar-benar menyusut kalau
      // constraint tinggi yang masuk cuma loose, sehingga baris yang
      // didokumentasikan itu benar-benar teruji di sini.
      _setViewport(tester, 1440, 900);
      await tester.pumpWidget(MaterialApp(
        home: AdaptiveShell(
          phoneOnly: false,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: const [
              SizedBox(key: Key('probe_bar'), height: 56, width: 100),
            ],
          ),
        ),
      ));
      await tester.pumpAndSettle();
      // Kalau tinggi dipaku penuh (900), "bar" 56px ini duduk di paling
      // atas kolom yang sama-sama 900 tinggi → topLeft.dy == 0. Kalau
      // kolaps (baris dihapus), kolom cuma 56 tinggi dan DIPUSATKAN oleh
      // Center dalam viewport 900 → topLeft.dy == (900 - 56) / 2 == 422.
      final topLeft = tester.getTopLeft(find.byKey(const Key('probe_bar')));
      expect(topLeft.dy, 0.0);
    });
  });
}
