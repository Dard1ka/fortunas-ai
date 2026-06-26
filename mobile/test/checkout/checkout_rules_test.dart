import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/api/models.dart';
import 'package:fortunas_ai/checkout/checkout_rules.dart';

void main() {
  group('parseLineItem', () {
    test('valid item parses with auto total', () {
      final r = parseLineItem('Kopi', '2', '15000');
      expect(r.error, isNull);
      expect(r.item!.product, 'Kopi');
      expect(r.item!.qty, 2);
      expect(r.item!.unitPrice, 15000);
      expect(r.item!.total, 30000);
    });
    test('empty product is rejected', () {
      expect(parseLineItem('   ', '1', '100').error, 'Nama produk wajib diisi.');
    });
    test('qty must be a positive int', () {
      expect(parseLineItem('Kopi', '0', '100').error, isNotNull);
      expect(parseLineItem('Kopi', '-1', '100').error, isNotNull);
      expect(parseLineItem('Kopi', 'x', '100').error, isNotNull);
    });
    test('price must be a non-negative int', () {
      expect(parseLineItem('Kopi', '1', '-5').error, isNotNull);
      expect(parseLineItem('Kopi', '1', 'abc').error, isNotNull);
    });
    test('price zero is valid', () {
      expect(parseLineItem('Bonus', '1', '0').error, isNull);
    });
    test('trims product name', () {
      expect(parseLineItem('  Kopi  ', '1', '100').item!.product, 'Kopi');
    });
  });

  test('canConfirm requires at least one item', () {
    expect(canConfirm(const []), false);
    expect(canConfirm([const CheckoutLineItem(product: 'a', qty: 1, unitPrice: 1)]), true);
  });

  test('grandTotal sums line totals', () {
    expect(grandTotal(const []), 0);
    expect(
      grandTotal([
        const CheckoutLineItem(product: 'a', qty: 2, unitPrice: 100), // 200
        const CheckoutLineItem(product: 'b', qty: 1, unitPrice: 50),  // 50
      ]),
      250,
    );
  });

  group('list ops', () {
    test('withItem appends without mutating the original', () {
      final base = [const CheckoutLineItem(product: 'a', qty: 1, unitPrice: 1)];
      final out = withItem(base, const CheckoutLineItem(product: 'b', qty: 1, unitPrice: 2));
      expect(out.length, 2);
      expect(base.length, 1);
    });
    test('withoutItemAt removes and guards out-of-range', () {
      final base = [const CheckoutLineItem(product: 'a', qty: 1, unitPrice: 1)];
      expect(withoutItemAt(base, 0), isEmpty);
      expect(withoutItemAt(base, 9), base);
      expect(base.length, 1);
    });
  });
}
