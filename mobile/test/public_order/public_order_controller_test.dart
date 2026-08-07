import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/api/client.dart';
import 'package:fortunas_ai/api/models.dart';
import 'package:fortunas_ai/public_order/public_order_controller.dart';

import '../support/fakes.dart';

ProviderContainer _container(FakeApi api) {
  final c = ProviderContainer(overrides: [apiProvider.overrideWithValue(api)]);
  addTearDown(c.dispose);
  return c;
}

const _umkm = PublicUmkm(code: 'KDS-001', name: 'Warung Uji', city: 'Kudus', products: [
  PublicMenuProduct(id: 1, name: 'Kopi Susu', price: 15000, stock: 3),
  PublicMenuProduct(id: 2, name: 'Teh Manis', price: 8000, stock: null),
  PublicMenuProduct(id: 3, name: 'Roti Habis', price: 5000, stock: 0),
  PublicMenuProduct(id: 4, name: 'Belum Dijual', price: null, stock: 10),
]);

void main() {
  test('loadMenu sukses → fase menu + umkm terisi', () async {
    final api = FakeApi()..publicUmkmResult = _umkm;
    final c = _container(api);
    await c.read(publicOrderControllerProvider.notifier).loadMenu('kds-001');
    final s = c.read(publicOrderControllerProvider);
    expect(api.lastPublicUmkmCode, 'kds-001');
    expect(s.phase, PublicOrderPhase.menu);
    expect(s.umkm?.name, 'Warung Uji');
    expect(s.errorMessage, isNull);
  });

  test('loadMenu kode kosong → error, tak memanggil API', () async {
    final api = FakeApi();
    final c = _container(api);
    await c.read(publicOrderControllerProvider.notifier).loadMenu('   ');
    expect(api.lastPublicUmkmCode, isNull);
    expect(c.read(publicOrderControllerProvider).errorMessage, isNotNull);
  });

  test('increment/decrement mengubah keranjang, total, & jumlah', () async {
    final api = FakeApi()..publicUmkmResult = _umkm;
    final c = _container(api);
    final ctrl = c.read(publicOrderControllerProvider.notifier);
    await ctrl.loadMenu('KDS-001');
    ctrl.increment(_umkm.products[0]); // Kopi 15000
    ctrl.increment(_umkm.products[0]); // 2x
    ctrl.increment(_umkm.products[1]); // Teh 8000
    var s = c.read(publicOrderControllerProvider);
    expect(s.qtyOf(1), 2);
    expect(s.itemCount, 3);
    expect(s.cartTotal, 15000 * 2 + 8000);
    ctrl.decrement(1);
    s = c.read(publicOrderControllerProvider);
    expect(s.qtyOf(1), 1);
    expect(s.cartTotal, 15000 + 8000);
  });

  test('increment dibatasi stok & produk tak-orderable', () async {
    final api = FakeApi()..publicUmkmResult = _umkm;
    final c = _container(api);
    final ctrl = c.read(publicOrderControllerProvider.notifier);
    await ctrl.loadMenu('KDS-001');
    // Stok Kopi = 3 → tak bisa lebih dari 3.
    for (var i = 0; i < 5; i++) {
      ctrl.increment(_umkm.products[0]);
    }
    expect(c.read(publicOrderControllerProvider).qtyOf(1), 3);
    // Roti habis (stock 0) & Belum Dijual (price null) → tak masuk keranjang.
    ctrl.increment(_umkm.products[2]);
    ctrl.increment(_umkm.products[3]);
    final s = c.read(publicOrderControllerProvider);
    expect(s.qtyOf(3), 0);
    expect(s.qtyOf(4), 0);
  });

  test('visibleProducts memfilter berdasarkan pencarian', () async {
    final api = FakeApi()..publicUmkmResult = _umkm;
    final c = _container(api);
    final ctrl = c.read(publicOrderControllerProvider.notifier);
    await ctrl.loadMenu('KDS-001');
    ctrl.setSearch('teh');
    final s = c.read(publicOrderControllerProvider);
    expect(s.visibleProducts.map((p) => p.id), [2]);
  });

  test('createOrder mengirim item keranjang & pindah ke fase order', () async {
    final api = FakeApi()
      ..publicUmkmResult = _umkm
      ..createPublicOrderResult = const PublicOrder(
          id: 5, status: 'pending_payment', paymentProvider: 'simulated',
          paymentOrderId: 'ORD-5-x', total: 30000);
    final c = _container(api);
    final ctrl = c.read(publicOrderControllerProvider.notifier);
    await ctrl.loadMenu('KDS-001');
    ctrl.increment(_umkm.products[0]);
    ctrl.increment(_umkm.products[0]);
    final ok = await ctrl.createOrder(customerName: 'Budi', customerPhone: '0812');
    expect(ok, true);
    final (code, name, phone, items) = api.lastCreatePublicOrder!;
    expect(code, 'KDS-001');
    expect(name, 'Budi');
    expect(phone, '0812');
    expect(items, [{'product_id': 1, 'qty': 2}]);
    final s = c.read(publicOrderControllerProvider);
    expect(s.phase, PublicOrderPhase.order);
    expect(s.order?.id, 5);
  });

  test('createOrder keranjang kosong → error tanpa memanggil API', () async {
    final api = FakeApi()..publicUmkmResult = _umkm;
    final c = _container(api);
    final ctrl = c.read(publicOrderControllerProvider.notifier);
    await ctrl.loadMenu('KDS-001');
    final ok = await ctrl.createOrder(customerName: 'Budi', customerPhone: '0812');
    expect(ok, false);
    expect(api.lastCreatePublicOrder, isNull);
    expect(c.read(publicOrderControllerProvider).errorMessage, isNotNull);
  });

  test('confirmPayment memanggil confirm-payment lalu menyegarkan status', () async {
    final api = FakeApi()
      ..publicUmkmResult = _umkm
      ..createPublicOrderResult = const PublicOrder(
          id: 5, status: 'pending_payment', paymentProvider: 'qris_static',
          paymentOrderId: 'ORD-5-x')
      ..publicOrderStatusResult = const PublicOrder(
          id: 5, status: 'paid', paymentProvider: 'qris_static',
          paymentOrderId: 'ORD-5-x');
    final c = _container(api);
    final ctrl = c.read(publicOrderControllerProvider.notifier);
    await ctrl.loadMenu('KDS-001');
    ctrl.increment(_umkm.products[0]);
    await ctrl.createOrder(customerName: 'Budi', customerPhone: '0812');
    await ctrl.confirmPayment();
    expect(api.lastConfirmPayPoid, 'ORD-5-x');
    expect(api.lastStatusPoid, 'ORD-5-x');
    expect(c.read(publicOrderControllerProvider).order?.status, 'paid');
  });

  test('backToMenu membuang pesanan & keranjang', () async {
    final api = FakeApi()
      ..publicUmkmResult = _umkm
      ..createPublicOrderResult =
          const PublicOrder(id: 5, paymentOrderId: 'ORD-5-x');
    final c = _container(api);
    final ctrl = c.read(publicOrderControllerProvider.notifier);
    await ctrl.loadMenu('KDS-001');
    ctrl.increment(_umkm.products[0]);
    await ctrl.createOrder(customerName: 'Budi', customerPhone: '0812');
    ctrl.backToMenu();
    final s = c.read(publicOrderControllerProvider);
    expect(s.phase, PublicOrderPhase.menu);
    expect(s.order, isNull);
    expect(s.itemCount, 0);
  });

}
