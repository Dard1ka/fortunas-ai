import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/api/client.dart';
import 'package:fortunas_ai/api/models.dart';
import 'package:fortunas_ai/screens/orders_screen.dart';
import 'package:go_router/go_router.dart';

import '../support/fakes.dart';

/// Router untuk test tombol kembali: `context.pop()` butuh GoRouter di widget
/// tree DAN sesuatu untuk di-pop. Pola mengikuti test layar lain
/// (home_screen_test.dart, customer_phone_screen_test.dart).
GoRouter _routerWithOrders() => GoRouter(routes: [
      GoRoute(path: '/', builder: (_, __) => const Scaffold(body: Text('HOME_REACHED'))),
      GoRoute(path: '/orders', builder: (_, __) => const OrdersScreen()),
    ]);

Future<void> _pump(WidgetTester tester, FakeApi api) async {
  await tester.pumpWidget(ProviderScope(
    overrides: [apiProvider.overrideWithValue(api)],
    child: const MaterialApp(home: OrdersScreen()),
  ));
  await tester.pumpAndSettle();
}

const _paid = UmkmOrder(
  id: 7, customerName: 'Budi', total: 30000, status: 'paid',
  items: [UmkmOrderItem(name: 'Kopi Susu', qty: 2, unitPrice: 15000, subtotal: 30000)],
);
const _accepted = UmkmOrder(id: 8, customerName: 'Siti', total: 5000, status: 'accepted');

void main() {
  testWidgets('pesanan lunas menampilkan tombol Terima & Tolak', (tester) async {
    final api = FakeApi()
      ..listOrdersResult = const UmkmOrderListResponse(orders: [_paid], count: 1);
    await _pump(tester, api);

    expect(find.text('Budi'), findsOneWidget);
    expect(find.textContaining('Kopi Susu'), findsOneWidget);
    expect(find.byKey(const Key('orders_accept_7')), findsOneWidget);
    expect(find.byKey(const Key('orders_reject_7')), findsOneWidget);
    expect(find.byKey(const Key('orders_complete_7')), findsNothing);
  });

  testWidgets('pesanan accepted menampilkan tombol Selesai saja', (tester) async {
    final api = FakeApi()
      ..listOrdersResult = const UmkmOrderListResponse(orders: [_accepted], count: 1);
    await _pump(tester, api);

    expect(find.byKey(const Key('orders_complete_8')), findsOneWidget);
    expect(find.byKey(const Key('orders_accept_8')), findsNothing);
  });

  testWidgets('tekan Terima mengirim aksi accept', (tester) async {
    final api = FakeApi()
      ..listOrdersResult = const UmkmOrderListResponse(orders: [_paid], count: 1)
      ..orderActionResult = const UmkmOrder(id: 7, status: 'accepted');
    await _pump(tester, api);

    await tester.tap(find.byKey(const Key('orders_accept_7')));
    await tester.pumpAndSettle();
    expect(api.lastOrderAction, (7, 'accept'));
  });

  testWidgets('Tolak minta konfirmasi dan menyebut uang dikembalikan manual',
      (tester) async {
    final api = FakeApi()
      ..listOrdersResult = const UmkmOrderListResponse(orders: [_paid], count: 1)
      ..orderActionResult = const UmkmOrder(id: 7, status: 'rejected');
    await _pump(tester, api);

    await tester.tap(find.byKey(const Key('orders_reject_7')));
    await tester.pumpAndSettle();
    expect(find.textContaining('manual'), findsOneWidget);
    expect(api.lastOrderAction, isNull, reason: 'belum dikonfirmasi');

    await tester.tap(find.text('Tolak Pesanan'));
    await tester.pumpAndSettle();
    expect(api.lastOrderAction, (7, 'reject'));
  });

  testWidgets('empty state saat tak ada pesanan', (tester) async {
    final api = FakeApi()..listOrdersResult = const UmkmOrderListResponse();
    await _pump(tester, api);
    expect(find.byKey(const Key('orders_empty')), findsOneWidget);
  });

  testWidgets('tombol Kembali mengembalikan ke layar sebelumnya', (tester) async {
    final api = FakeApi()..listOrdersResult = const UmkmOrderListResponse();
    final router = _routerWithOrders();
    await tester.pumpWidget(ProviderScope(
      overrides: [apiProvider.overrideWithValue(api)],
      child: MaterialApp.router(routerConfig: router),
    ));
    await tester.pumpAndSettle();
    router.push('/orders');
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('orders_back')), findsOneWidget);
    await tester.tap(find.byKey(const Key('orders_back')));
    await tester.pumpAndSettle();
    expect(find.text('HOME_REACHED'), findsOneWidget);
  });
}
