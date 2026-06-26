import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/api/client.dart';
import 'package:fortunas_ai/api/models.dart';
import 'package:fortunas_ai/checkout/checkout_controller.dart';

import '../support/fakes.dart';

CheckoutLineItem _item(String p, int q, int up) =>
    CheckoutLineItem(product: p, qty: q, unitPrice: up);

ProviderContainer _container(FakeApi api) {
  final c = ProviderContainer(overrides: [apiProvider.overrideWithValue(api)]);
  addTearDown(c.dispose);
  return c;
}

void main() {
  test('addItem appends; removeItemAt removes', () {
    final c = _container(FakeApi());
    final ctrl = c.read(checkoutControllerProvider.notifier);
    ctrl.addItem(_item('Kopi', 2, 15000));
    ctrl.addItem(_item('Teh', 1, 8000));
    expect(c.read(checkoutControllerProvider).items.length, 2);
    ctrl.removeItemAt(0);
    final items = c.read(checkoutControllerProvider).items;
    expect(items.length, 1);
    expect(items.first.product, 'Teh');
  });

  test('confirm success sets result, submitting false, trims customer, qr null', () async {
    final api = FakeApi()
      ..checkoutResult = const CheckoutConfirmResponse(
          ok: true, status: 'recorded', reply: 'ok',
          invoice: 'INV-1', itemCount: 1, grandTotal: 15000);
    final c = _container(api);
    final ctrl = c.read(checkoutControllerProvider.notifier);
    ctrl.addItem(_item('Kopi', 1, 15000));
    await ctrl.confirm('  Bu Sari  ');
    final st = c.read(checkoutControllerProvider);
    expect(st.result?.invoice, 'INV-1');
    expect(st.submitting, false);
    expect(api.lastCheckout?.customer, 'Bu Sari');
    expect(api.lastCheckout?.customerQrToken, isNull);
  });

  test('confirm error sets errorMessage, keeps items, submitting false', () async {
    final api = FakeApi()..checkoutError = Exception('boom');
    final c = _container(api);
    final ctrl = c.read(checkoutControllerProvider.notifier);
    ctrl.addItem(_item('Kopi', 1, 15000));
    await ctrl.confirm('');
    final st = c.read(checkoutControllerProvider);
    expect(st.errorMessage, isNotNull);
    expect(st.result, isNull);
    expect(st.items.length, 1);
    expect(st.submitting, false);
  });

  test('confirm is a no-op when there are no items', () async {
    final api = FakeApi();
    final c = _container(api);
    await c.read(checkoutControllerProvider.notifier).confirm('x');
    expect(api.lastCheckout, isNull);
    expect(c.read(checkoutControllerProvider).result, isNull);
  });

  test('reset clears items, result and error', () async {
    final api = FakeApi()
      ..checkoutResult = const CheckoutConfirmResponse(
          ok: true, status: 'recorded', reply: 'ok',
          invoice: 'INV', itemCount: 1, grandTotal: 1);
    final c = _container(api);
    final ctrl = c.read(checkoutControllerProvider.notifier);
    ctrl.addItem(_item('Kopi', 1, 15000));
    await ctrl.confirm('x');
    ctrl.reset();
    final st = c.read(checkoutControllerProvider);
    expect(st.items, isEmpty);
    expect(st.result, isNull);
    expect(st.errorMessage, isNull);
  });
}
