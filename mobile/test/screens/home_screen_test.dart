import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/api/client.dart';
import 'package:fortunas_ai/screens/home_screen.dart';
import 'package:go_router/go_router.dart';

import '../support/fakes.dart';

GoRouter _router() => GoRouter(routes: [
      GoRoute(
        path: '/',
        builder: (_, __) => const Scaffold(body: HomeScreen()),
      ),
      GoRoute(
        path: '/scan',
        builder: (_, __) => const Scaffold(body: Text('SCAN_REACHED')),
      ),
    ]);

void main() {
  testWidgets('home has Scan QR entry that navigates to /scan', (tester) async {
    // HomeScreen kini memuat OrdersHomeCard (ConsumerWidget) — butuh
    // ProviderScope. FakeApi supaya listOrders tak menyentuh jaringan asli.
    await tester.pumpWidget(ProviderScope(
      overrides: [apiProvider.overrideWithValue(FakeApi())],
      child: MaterialApp.router(routerConfig: _router()),
    ));
    await tester.pumpAndSettle();
    final entry = find.byKey(const Key('home_scan'));
    await tester.ensureVisible(entry);
    await tester.pumpAndSettle();
    await tester.tap(entry);
    await tester.pumpAndSettle();
    expect(find.text('SCAN_REACHED'), findsOneWidget);
  });
}
