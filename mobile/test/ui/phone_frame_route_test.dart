import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/app.dart';
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
}
