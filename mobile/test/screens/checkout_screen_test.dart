import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/api/client.dart';
import 'package:fortunas_ai/api/models.dart';
import 'package:fortunas_ai/screens/checkout_screen.dart';

import '../support/fakes.dart';

CheckoutConfirmResponse _okResp() => const CheckoutConfirmResponse(
      ok: true, status: 'recorded', reply: 'Sip! Transaksi tercatat ya.',
      invoice: 'INV-00123', itemCount: 1, grandTotal: 15000,
    );

Future<void> _pump(WidgetTester tester, FakeApi api) async {
  await tester.pumpWidget(ProviderScope(
    overrides: [apiProvider.overrideWithValue(api)],
    child: const MaterialApp(home: CheckoutScreen()),
  ));
  await tester.pumpAndSettle();
}

Future<void> _addItem(WidgetTester tester,
    {String product = 'Kopi', String qty = '1', String price = '15000'}) async {
  await tester.enterText(find.byKey(const Key('checkout_product')), product);
  await tester.enterText(find.byKey(const Key('checkout_qty')), qty);
  await tester.enterText(find.byKey(const Key('checkout_price')), price);
  await tester.tap(find.byKey(const Key('checkout_add')));
  await tester.pump();
}

void main() {
  testWidgets('Konfirmasi disabled with no items', (tester) async {
    await _pump(tester, FakeApi()..checkoutResult = _okResp());
    final btn = tester.widget<ElevatedButton>(find.byKey(const Key('checkout_confirm')));
    expect(btn.onPressed, isNull);
  });

  testWidgets('Tambah adds item, updates total, enables Konfirmasi', (tester) async {
    await _pump(tester, FakeApi()..checkoutResult = _okResp());
    await _addItem(tester, product: 'Kopi susu', qty: '2', price: '15000');
    expect(find.text('Kopi susu'), findsOneWidget);
    expect(find.textContaining('30.000'), findsWidgets); // subtotal + grand total
    final btn = tester.widget<ElevatedButton>(find.byKey(const Key('checkout_confirm')));
    expect(btn.onPressed, isNotNull);
  });

  testWidgets('invalid item shows inline error and is not added', (tester) async {
    await _pump(tester, FakeApi()..checkoutResult = _okResp());
    await tester.tap(find.byKey(const Key('checkout_add'))); // all empty
    await tester.pump();
    expect(find.text('Nama produk wajib diisi.'), findsOneWidget);
    final btn = tester.widget<ElevatedButton>(find.byKey(const Key('checkout_confirm')));
    expect(btn.onPressed, isNull);
  });

  testWidgets('confirm success shows invoice + reply; Transaksi Baru resets', (tester) async {
    final api = FakeApi()..checkoutResult = _okResp();
    await _pump(tester, api);
    await _addItem(tester);
    await tester.tap(find.byKey(const Key('checkout_confirm')));
    await tester.pumpAndSettle();
    expect(find.text('INV-00123'), findsOneWidget);
    expect(find.textContaining('Sip!'), findsOneWidget);
    expect(api.lastCheckout?.customerQrToken, isNull);
    await tester.tap(find.byKey(const Key('checkout_new')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('checkout_confirm')), findsOneWidget); // back to form
    expect(find.text('INV-00123'), findsNothing);
  });

  testWidgets('confirm failure shows error, keeps item + stays in form', (tester) async {
    final api = FakeApi()..checkoutError = Exception('gagal jaringan');
    await _pump(tester, api);
    await _addItem(tester);
    await tester.tap(find.byKey(const Key('checkout_confirm')));
    await tester.pumpAndSettle();
    expect(find.text('Kopi'), findsOneWidget); // item kept
    expect(find.byKey(const Key('checkout_confirm')), findsOneWidget); // still form mode
    expect(find.text('INV-00123'), findsNothing);
  });
}
