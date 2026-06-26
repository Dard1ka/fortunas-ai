import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/api/client.dart';
import 'package:fortunas_ai/api/models.dart';
import 'package:fortunas_ai/screens/customer_qr_screen.dart';

import '../support/fakes.dart';

QrSessionResponse _resp({int ttl = 90}) => QrSessionResponse(
      qrToken: 'qr-jwt-token-abc', nonce: 'n1',
      issuedAt: '2026-06-26T00:00:00Z', expiresAt: '2026-06-26T00:01:30Z',
      ttlSeconds: ttl,
    );

Future<void> _pump(WidgetTester tester, FakeApi api) async {
  await tester.pumpWidget(ProviderScope(
    overrides: [apiProvider.overrideWithValue(api)],
    child: const MaterialApp(home: CustomerQrScreen()),
  ));
  await tester.pump(); // let post-frame refresh() kick off
  await tester.pump(); // settle the fetch
}

void main() {
  testWidgets('renders QR after load', (tester) async {
    final api = FakeApi()..customerQrSessionResult = _resp();
    await _pump(tester, api);
    expect(find.byKey(const Key('cust_qr_image')), findsOneWidget);
    expect(api.customerQrSessionCallCount, 1);
    await tester.pumpWidget(const SizedBox()); // unmount → autoDispose cancels timer
  });

  testWidgets('shows error + retry when fetch fails', (tester) async {
    final api = FakeApi()..customerQrSessionError = Exception('503');
    await _pump(tester, api);
    expect(find.byKey(const Key('cust_qr_error')), findsOneWidget);
    expect(find.byKey(const Key('cust_qr_refresh')), findsOneWidget);
    expect(find.byKey(const Key('cust_qr_image')), findsNothing);
  });

  testWidgets('manual refresh re-fetches', (tester) async {
    final api = FakeApi()..customerQrSessionResult = _resp();
    await _pump(tester, api);
    expect(api.customerQrSessionCallCount, 1);
    await tester.tap(find.byKey(const Key('cust_qr_refresh')));
    await tester.pump();
    await tester.pump();
    expect(api.customerQrSessionCallCount, 2);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('auto-refresh fires before TTL expiry', (tester) async {
    final api = FakeApi()..customerQrSessionResult = _resp(ttl: 90);
    await _pump(tester, api);
    expect(api.customerQrSessionCallCount, 1);
    await tester.pump(const Duration(seconds: 86)); // lead = 90-5 = 85 < 86
    await tester.pump(); // settle the auto-fetch
    expect(api.customerQrSessionCallCount, 2);
    await tester.pumpWidget(const SizedBox()); // unmount → cancel pending timer
  });
}
