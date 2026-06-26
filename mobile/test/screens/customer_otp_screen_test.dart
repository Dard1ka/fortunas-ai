import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:fortunas_ai/screens/customer_otp_screen.dart';

GoRouter _router() => GoRouter(routes: [
      GoRoute(path: '/',
          builder: (_, __) => const CustomerOtpScreen(phone: '08123456789')),
      GoRoute(path: '/customer/profile',
          builder: (_, __) => const Scaffold(body: Text('PROFILE_REACHED'))),
    ]);

Future<void> _pump(WidgetTester tester) async {
  await tester.pumpWidget(MaterialApp.router(routerConfig: _router()));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('non-6-digit shows error, no nav', (tester) async {
    await _pump(tester);
    await tester.enterText(find.byKey(const Key('cust_otp')), '123');
    await tester.tap(find.byKey(const Key('cust_otp_verify')));
    await tester.pumpAndSettle();
    expect(find.text('PROFILE_REACHED'), findsNothing);
    expect(find.text('Kode OTP harus 6 angka.'), findsOneWidget);
  });

  testWidgets('6-digit navigates to profile', (tester) async {
    await _pump(tester);
    await tester.enterText(find.byKey(const Key('cust_otp')), '123456');
    await tester.tap(find.byKey(const Key('cust_otp_verify')));
    await tester.pumpAndSettle();
    expect(find.text('PROFILE_REACHED'), findsOneWidget);
  });
}
