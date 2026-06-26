import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:fortunas_ai/screens/customer_phone_screen.dart';

GoRouter _router() => GoRouter(routes: [
      GoRoute(path: '/', builder: (_, __) => const CustomerPhoneScreen()),
      GoRoute(path: '/customer/otp',
          builder: (_, __) => const Scaffold(body: Text('OTP_REACHED'))),
    ]);

Future<void> _pump(WidgetTester tester) async {
  await tester.pumpWidget(MaterialApp.router(routerConfig: _router()));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('short phone shows error, does not navigate', (tester) async {
    await _pump(tester);
    await tester.enterText(find.byKey(const Key('cust_phone')), '0812');
    await tester.tap(find.byKey(const Key('cust_phone_next')));
    await tester.pumpAndSettle();
    expect(find.text('OTP_REACHED'), findsNothing);
    expect(find.textContaining('tidak valid'), findsOneWidget);
  });

  testWidgets('valid phone navigates to OTP', (tester) async {
    await _pump(tester);
    await tester.enterText(find.byKey(const Key('cust_phone')), '08123456789');
    await tester.tap(find.byKey(const Key('cust_phone_next')));
    await tester.pumpAndSettle();
    expect(find.text('OTP_REACHED'), findsOneWidget);
  });
}
