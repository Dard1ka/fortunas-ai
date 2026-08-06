import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/app.dart';
import 'package:fortunas_ai/theme/tokens.dart';
import 'package:fortunas_ai/ui/adaptive_shell.dart';
import 'package:go_router/go_router.dart';

/// Router minimal: dua route memakai PhoneFrame, satu UMKM satu customer.
GoRouter _router(String initial) => GoRouter(
      initialLocation: initial,
      routes: [
        GoRoute(
          path: '/products',
          builder: (_, __) =>
              const PhoneFrame(child: SizedBox.expand(key: Key('probe'))),
        ),
        GoRoute(
          path: '/customer/qr',
          builder: (_, __) =>
              const PhoneFrame(child: SizedBox.expand(key: Key('probe'))),
        ),
      ],
    );

/// Router dua route dengan call-site `PhoneFrame` yang **TIDAK `const`**.
///
/// Ini bukan gaya, ini inti test-nya. `PhoneFrame` membaca lokasi route-nya
/// sendiri; kalau ia salah membaca **puncak stack** (`GoRouter.state`) alih-alih
/// state route-nya sendiri (`GoRouterState.of`), kesalahan itu hanya terlihat
/// pada call-site yang bisa dibangun ulang. Widget `const` tidak pernah
/// dibangun ulang oleh Flutter, jadi call-site `const` **menyembunyikan** bug
/// ini. Route yang membawa nilai runtime (`state.extra`, path/query param)
/// tidak bisa `const` — jadi bentuk inilah yang harus dijaga.
GoRouter _pushStackRouter() => GoRouter(
      initialLocation: '/products',
      routes: [
        GoRoute(
          path: '/products',
          builder: (_, __) => PhoneFrame(
            child: SizedBox.expand(key: const Key('umkm_probe')),
          ),
        ),
        GoRoute(
          path: '/customer/login',
          builder: (_, __) => PhoneFrame(
            child: SizedBox.expand(key: const Key('cust_probe')),
          ),
        ),
      ],
    );

/// Kunci `probe` ada di `SizedBox.expand` — lihat catatan di
/// `adaptive_shell_test.dart`: mengukur `Text` memberi lebar glyph, bukan
/// lebar kolom.
Future<double> _widthAt(WidgetTester tester, String location) async {
  tester.view.devicePixelRatio = 1.0;
  tester.view.physicalSize = const Size(1440, 900);
  addTearDown(tester.view.reset);
  await tester.pumpWidget(MaterialApp.router(routerConfig: _router(location)));
  await tester.pumpAndSettle();
  return tester.getSize(find.byKey(const Key('probe'))).width;
}

void main() {
  testWidgets('route UMKM di 1440 jadi adaptif (840), bukan strip 430',
      (tester) async {
    expect(await _widthAt(tester, '/products'), kExpandedContentWidth);
  });

  testWidgets('route customer di 1440 tetap dikurung 430', (tester) async {
    expect(await _widthAt(tester, '/customer/qr'), kPhoneOnlyFrameWidth);
  });

  testWidgets(
      'route UMKM di 1440 mengecat backdrop FortunasColors.bg di luar kolom framed',
      (tester) async {
    // Bug yang ditemukan review: jalur adaptif AdaptiveShell sengaja tidak
    // punya backdrop (lihat adaptive_shell_test.dart, "tidak punya
    // backdrop"). Itu benar untuk shell tab UMKM (Scaffold luarnya sendiri
    // yang mengecat), tapi untuk 9 route yang lewat PhoneFrame langsung
    // (/splash, /login, /register, /voice, /dpa, /checkout, /products,
    // /orders, /scan) tidak ada apa pun lagi yang mengecat gutter di luar
    // kolom 840px. PhoneFrame sendiri harus jadi yang mengecatnya.
    await _widthAt(tester, '/products');
    final backdrop = tester.widget<ColoredBox>(
      find.ancestor(
        of: find.byKey(const Key('probe')),
        matching: find.byType(ColoredBox),
      ),
    );
    expect(backdrop.color, FortunasColors.bg);
  });

  testWidgets('PhoneFrame tanpa router tidak crash — anggap UMKM',
      (tester) async {
    tester.view.devicePixelRatio = 1.0;
    tester.view.physicalSize = const Size(1440, 900);
    addTearDown(tester.view.reset);
    await tester.pumpWidget(const MaterialApp(
      home: PhoneFrame(child: SizedBox.expand(key: Key('probe'))),
    ));
    await tester.pumpAndSettle();
    expect(tester.getSize(find.byKey(const Key('probe'))).width,
        kExpandedContentWidth);
  });

  group('stack dua-dalam: tiap PhoneFrame membingkai route-nya SENDIRI', () {
    // `login_screen.dart:97` melakukan `context.push('/customer/login')` dari
    // layar login UMKM, jadi stack lintas-audiens (UMKM di bawah, customer di
    // atas) nyata ada di app ini — bukan skenario karangan.
    //
    // Kenapa diukur SAAT animasi push berjalan, bukan setelah settle: begitu
    // transisi selesai, Overlay tidak lagi me-layout route di bawah route opaque
    // di atasnya, jadi `getSize` pada probe UMKM tidak mungkin lagi (probe-nya
    // hilang dari tree). Jendela saat animasi berjalan adalah satu-satunya saat
    // route bawah SEKALIGUS masih ter-layout DAN sudah dibangun ulang oleh
    // GoRouter — persis jendela di mana pembacaan puncak-stack yang salah
    // menampakkan dirinya (dan persis yang dilihat pengguna: layar UMKM di
    // belakang menyusut 840→430 selama transisi).
    testWidgets(
        'route UMKM di bawah route customer yang di-push tetap 840, bukan 430',
        (tester) async {
      tester.view.devicePixelRatio = 1.0;
      tester.view.physicalSize = const Size(1440, 900);
      addTearDown(tester.view.reset);
      final router = _pushStackRouter();
      addTearDown(router.dispose);

      await tester.pumpWidget(MaterialApp.router(routerConfig: router));
      await tester.pumpAndSettle();
      expect(tester.getSize(find.byKey(const Key('umkm_probe'))).width,
          kExpandedContentWidth,
          reason: 'sebelum push, route UMKM harus adaptif 840');

      router.push('/customer/login');

      // Frame pertama setelah push: GoRouter sudah membangun ulang halaman.
      await tester.pump();
      expect(tester.getSize(find.byKey(const Key('umkm_probe'))).width,
          kExpandedContentWidth,
          reason: 'frame pertama setelah push: route UMKM masih route UMKM');

      // Pertengahan animasi transisi (durasi default MaterialPageRoute 300ms).
      await tester.pump(const Duration(milliseconds: 100));
      expect(tester.getSize(find.byKey(const Key('umkm_probe'))).width,
          kExpandedContentWidth,
          reason: 'PhoneFrame bawah membaca puncak stack (/customer/login) '
              'kalau lokasinya diambil dari GoRouter.state, bukan '
              'GoRouterState.of(context)');
    });

    testWidgets('route customer yang di-push tetap dikurung 430',
        (tester) async {
      tester.view.devicePixelRatio = 1.0;
      tester.view.physicalSize = const Size(1440, 900);
      addTearDown(tester.view.reset);
      final router = _pushStackRouter();
      addTearDown(router.dispose);

      await tester.pumpWidget(MaterialApp.router(routerConfig: router));
      await tester.pumpAndSettle();
      router.push('/customer/login');
      await tester.pumpAndSettle();
      expect(tester.getSize(find.byKey(const Key('cust_probe'))).width,
          kPhoneOnlyFrameWidth);
    });
  });
}
