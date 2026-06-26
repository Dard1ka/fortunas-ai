import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:fortunas_ai/api/client.dart';
import 'package:fortunas_ai/api/models.dart';
import 'package:fortunas_ai/screens/customer_profile_screen.dart';

import '../support/fakes.dart';

CustomerBootstrapResponse _resp() => const CustomerBootstrapResponse(
      accessToken: 'cust-jwt', role: 'customer', isNewUser: true,
      profile: CustomerProfile(
          customerUserId: 'C1', username: 'Sari', phoneNumber: '628123456'),
    );

GoRouter _router() => GoRouter(routes: [
      GoRoute(path: '/',
          builder: (_, __) => const CustomerProfileScreen(phone: '08123456789')),
      GoRoute(path: '/login', builder: (_, __) => const Scaffold(body: Text('LOGIN_REACHED'))),
      GoRoute(path: '/customer/qr',
          builder: (_, __) => const Scaffold(body: Text('QR_REACHED'))),
    ]);

Future<void> _pump(WidgetTester tester, FakeApi api) async {
  await tester.pumpWidget(ProviderScope(
    overrides: [apiProvider.overrideWithValue(api)],
    child: MaterialApp.router(routerConfig: _router()),
  ));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('blank username shows error, no bootstrap', (tester) async {
    final api = FakeApi()..customerBootstrapResult = _resp();
    await _pump(tester, api);
    await tester.tap(find.byKey(const Key('cust_submit')));
    await tester.pumpAndSettle();
    expect(find.textContaining('Nama wajib'), findsOneWidget);
    expect(api.lastCustomerBootstrap, isNull);
  });

  testWidgets('valid submit bootstraps then shows logged-in profile', (tester) async {
    final api = FakeApi()..customerBootstrapResult = _resp();
    await _pump(tester, api);
    await tester.enterText(find.byKey(const Key('cust_username')), 'Sari');
    await tester.tap(find.byKey(const Key('cust_submit')));
    await tester.pumpAndSettle();
    expect(find.text('Sari'), findsWidgets);            // logged-in view shows name
    expect(find.byKey(const Key('cust_logout')), findsOneWidget);
    expect(api.lastCustomerBootstrap?.firebaseIdToken, 'dev:08123456789:08123456789');
  });

  testWidgets('logout returns to login', (tester) async {
    final api = FakeApi()..customerBootstrapResult = _resp();
    await _pump(tester, api);
    await tester.enterText(find.byKey(const Key('cust_username')), 'Sari');
    await tester.tap(find.byKey(const Key('cust_submit')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('cust_logout')));
    await tester.pumpAndSettle();
    expect(find.text('LOGIN_REACHED'), findsOneWidget);
  });

  testWidgets('logged-in shows Tampilkan QR entry that navigates', (tester) async {
    final api = FakeApi()..customerBootstrapResult = _resp();
    await _pump(tester, api); // existing helper pumps CustomerProfileScreen in a router
    await tester.enterText(find.byKey(const Key('cust_username')), 'Sari');
    await tester.tap(find.byKey(const Key('cust_submit')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('cust_show_qr')), findsOneWidget);
    await tester.tap(find.byKey(const Key('cust_show_qr')));
    await tester.pumpAndSettle();
    expect(find.text('QR_REACHED'), findsOneWidget);
  });
}
