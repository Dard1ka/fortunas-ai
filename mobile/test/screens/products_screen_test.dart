import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/api/client.dart';
import 'package:fortunas_ai/api/models.dart';
import 'package:fortunas_ai/screens/products_screen.dart';

import '../support/fakes.dart';

ProductItem _product({required int? stock}) => ProductItem(
      id: 1,
      tenantId: 1,
      name: 'Kopi',
      stockCode: 'ko-001',
      stock: stock,
    );

Future<void> _pump(WidgetTester tester, FakeApi api) async {
  await tester.pumpWidget(ProviderScope(
    overrides: [apiProvider.overrideWithValue(api)],
    child: const MaterialApp(home: ProductsScreen()),
  ));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('form tambah produk punya field stok', (tester) async {
    final api = FakeApi()
      ..listProductsResult = ProductListResponse(products: [_product(stock: 12)], count: 1);
    await _pump(tester, api);
    await tester.tap(find.byKey(const Key('product_add_fab')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('product_stock')), findsOneWidget);
  });

  testWidgets('badge stok normal menampilkan Stok: N', (tester) async {
    final api = FakeApi()
      ..listProductsResult = ProductListResponse(products: [_product(stock: 12)], count: 1);
    await _pump(tester, api);
    expect(find.byKey(const Key('product_stock_badge')), findsOneWidget);
    expect(find.textContaining('Stok: 12'), findsOneWidget);
  });

  testWidgets('badge stok rendah menampilkan Menipis', (tester) async {
    final api = FakeApi()
      ..listProductsResult = ProductListResponse(products: [_product(stock: 3)], count: 1);
    await _pump(tester, api);
    expect(find.textContaining('Menipis'), findsOneWidget);
  });

  testWidgets('badge stok nol menampilkan Habis', (tester) async {
    final api = FakeApi()
      ..listProductsResult = ProductListResponse(products: [_product(stock: 0)], count: 1);
    await _pump(tester, api);
    expect(find.textContaining('Habis'), findsOneWidget);
  });

  testWidgets('badge stok null menampilkan Tak dilacak', (tester) async {
    final api = FakeApi()
      ..listProductsResult = ProductListResponse(products: [_product(stock: null)], count: 1);
    await _pump(tester, api);
    expect(find.textContaining('Tak dilacak'), findsOneWidget);
  });
}
