import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/api/client.dart';
import 'package:fortunas_ai/api/models.dart';
import 'package:fortunas_ai/orders/order_controller.dart';

import '../support/fakes.dart';

ProviderContainer _container(FakeApi api) {
  final c = ProviderContainer(overrides: [apiProvider.overrideWithValue(api)]);
  addTearDown(c.dispose);
  return c;
}

const _order = UmkmOrder(id: 7, customerName: 'Budi', total: 30000, status: 'paid');

void main() {
  test('load mengisi daftar pesanan', () async {
    final api = FakeApi()
      ..listOrdersResult = const UmkmOrderListResponse(orders: [_order], count: 1);
    final c = _container(api);
    await c.read(orderControllerProvider.notifier).load();
    final s = c.read(orderControllerProvider);
    expect(s.loading, false);
    expect(s.orders.single.id, 7);
    expect(s.errorMessage, isNull);
  });

  test('accept memanggil API lalu memuat ulang dari server', () async {
    final api = FakeApi()
      ..listOrdersResult = const UmkmOrderListResponse(orders: [_order], count: 1)
      ..orderActionResult = const UmkmOrder(id: 7, status: 'accepted');
    final c = _container(api);
    final ok = await c.read(orderControllerProvider.notifier).accept(7);
    expect(ok, true);
    expect(api.lastOrderAction, (7, 'accept'));
    expect(c.read(orderControllerProvider).submittingId, isNull);
  });

  test('reject meneruskan aksi yang benar', () async {
    final api = FakeApi()
      ..listOrdersResult = const UmkmOrderListResponse()
      ..orderActionResult = const UmkmOrder(id: 9, status: 'rejected');
    final c = _container(api);
    await c.read(orderControllerProvider.notifier).reject(9);
    expect(api.lastOrderAction, (9, 'reject'));
  });

  test('kegagalan aksi memunculkan pesanan error dan melepas submittingId', () async {
    final api = FakeApi()
      ..listOrdersResult = const UmkmOrderListResponse()
      ..orderActionError = Exception('gagal');
    final c = _container(api);
    final ok = await c.read(orderControllerProvider.notifier).complete(3);
    expect(ok, false);
    final s = c.read(orderControllerProvider);
    expect(s.errorMessage, isNotNull);
    expect(s.submittingId, isNull);
  });

  test('load meneruskan filter status ke API', () async {
    final api = FakeApi()..listOrdersResult = const UmkmOrderListResponse();
    final c = _container(api);
    await c.read(orderControllerProvider.notifier).load(status: 'all');
    expect(api.lastListOrdersStatus, 'all');
  });
}
