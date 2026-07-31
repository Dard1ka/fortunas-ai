import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/api/models.dart';

void main() {
  test('UmkmOrder.fromJson memetakan item dan total', () {
    final o = UmkmOrder.fromJson(const {
      'id': 7,
      'code': 'KDS-001',
      'customer_name': 'Budi',
      'customer_phone': '0812',
      'total': 30000,
      'status': 'paid',
      'paid_at': '2026-07-31T02:00:00+00:00',
      'items': [
        {'product_id': 3, 'name': 'Kopi Susu', 'qty': 2,
         'unit_price': 15000, 'subtotal': 30000},
      ],
    });
    expect(o.id, 7);
    expect(o.customerName, 'Budi');
    expect(o.status, 'paid');
    expect(o.paidAt, isNotNull);
    expect(o.items.single.name, 'Kopi Susu');
    expect(o.items.single.qty, 2);
    expect(o.items.single.subtotal, 30000);
    expect(o.total, 30000);
  });

  test('UmkmOrder.fromJson tahan field kosong', () {
    final o = UmkmOrder.fromJson(const {'id': 1});
    expect(o.items, isEmpty);
    expect(o.total, 0);
    expect(o.paidAt, isNull);
    expect(o.status, 'pending_payment');
    expect(o.paymentStatus, isNull);
    expect(o.code, '');
    expect(o.customerName, '');
    expect(o.customerPhone, '');
    expect(o.createdAt, '');
  });

  test('UmkmOrderListResponse.fromJson membaca count', () {
    final r = UmkmOrderListResponse.fromJson(const {
      'orders': [{'id': 1}, {'id': 2}],
      'count': 2,
    });
    expect(r.count, 2);
    expect(r.orders.length, 2);
  });

  group('UmkmOrder.isRefunded', () {
    test('true untuk refund', () {
      expect(const UmkmOrder(id: 1, paymentStatus: 'refund').isRefunded, isTrue);
    });

    test('true untuk REFUND (case-insensitive)', () {
      expect(const UmkmOrder(id: 1, paymentStatus: 'REFUND').isRefunded, isTrue);
    });

    test('true untuk partial_refund', () {
      expect(
          const UmkmOrder(id: 1, paymentStatus: 'partial_refund').isRefunded,
          isTrue);
    });

    test('true untuk chargeback', () {
      expect(
          const UmkmOrder(id: 1, paymentStatus: 'chargeback').isRefunded,
          isTrue);
    });

    test('false untuk paymentStatus null', () {
      expect(const UmkmOrder(id: 1).isRefunded, isFalse);
    });

    test('false untuk paid', () {
      expect(const UmkmOrder(id: 1, paymentStatus: 'paid').isRefunded, isFalse);
    });
  });
}
