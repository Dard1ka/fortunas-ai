import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/api/client.dart';
import 'package:fortunas_ai/api/models.dart';
import 'package:fortunas_ai/orders/order_controller.dart';
import 'package:fortunas_ai/orders/orders_home_card.dart';

import '../support/fakes.dart';

void main() {
  test('pendingOrderCountProvider menghitung pesanan berstatus paid', () async {
    final api = FakeApi()
      ..listOrdersResult = const UmkmOrderListResponse(
          orders: [UmkmOrder(id: 1, status: 'paid')], count: 1);
    final c = ProviderContainer(overrides: [apiProvider.overrideWithValue(api)]);
    addTearDown(c.dispose);

    expect(await c.read(pendingOrderCountProvider.future), 1);
    expect(api.lastListOrdersStatus, 'paid');
  });

  testWidgets('kartu tampil tanpa badge saat tak ada pesanan', (tester) async {
    final api = FakeApi()..listOrdersResult = const UmkmOrderListResponse();
    await tester.pumpWidget(ProviderScope(
      overrides: [apiProvider.overrideWithValue(api)],
      child: const MaterialApp(home: Scaffold(body: OrdersHomeCard())),
    ));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('home_orders')), findsOneWidget);
    expect(find.text('Pesanan online dari pelanggan'), findsOneWidget);
  });

  testWidgets('badge menyebut jumlah pesanan menunggu', (tester) async {
    final api = FakeApi()
      ..listOrdersResult = const UmkmOrderListResponse(
          orders: [UmkmOrder(id: 1, status: 'paid'),
                   UmkmOrder(id: 2, status: 'paid')], count: 2);
    await tester.pumpWidget(ProviderScope(
      overrides: [apiProvider.overrideWithValue(api)],
      child: const MaterialApp(home: Scaffold(body: OrdersHomeCard())),
    ));
    await tester.pumpAndSettle();
    expect(find.text('2 pesanan menunggu diterima'), findsOneWidget);
  });
}
