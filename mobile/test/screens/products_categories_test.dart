import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/api/client.dart';
import 'package:fortunas_ai/api/models.dart';
import 'package:fortunas_ai/products/product_controller.dart';
import 'package:fortunas_ai/screens/products_screen.dart';

import '../support/fakes.dart';

ProductItem _product({int? categoryId}) => ProductItem(
      id: 1,
      tenantId: 1,
      name: 'Kopi',
      stockCode: 'ko-001',
      stock: 12,
      categoryId: categoryId,
    );

Future<void> _pump(WidgetTester tester, FakeApi api) async {
  await tester.pumpWidget(ProviderScope(
    overrides: [apiProvider.overrideWithValue(api)],
    child: const MaterialApp(home: ProductsScreen()),
  ));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('form tambah produk punya dropdown kategori dengan opsi ter-seed',
      (tester) async {
    final api = FakeApi()
      ..listProductsResult = const ProductListResponse(products: [], count: 0)
      ..listCategoriesResult = const CategoryListResponse(
        categories: [Category(id: 1, tenantId: 1, name: 'Minuman')],
        count: 1,
      );
    await _pump(tester, api);

    await tester.tap(find.byKey(const Key('product_add_fab')));
    await tester.pumpAndSettle();

    final dropdown = find.byKey(const Key('product_category_dropdown'));
    expect(dropdown, findsOneWidget);

    // Default: opsi "Tanpa kategori" tampil sebagai nilai terpilih.
    expect(find.text('Tanpa kategori'), findsOneWidget);

    // Buka dropdown, pastikan kategori ter-seed muncul sebagai opsi.
    await tester.tap(dropdown);
    await tester.pumpAndSettle();
    expect(find.text('Minuman'), findsOneWidget);
  });

  test('ProductController.create meneruskan categoryId ke API', () async {
    final api = FakeApi()..createProductResult = _product(categoryId: 1);
    final container = ProviderContainer(overrides: [apiProvider.overrideWithValue(api)]);
    addTearDown(container.dispose);

    final ok = await container.read(productControllerProvider.notifier).create(
          name: 'Kopi',
          description: '',
          imageBytes: const [1, 2, 3],
          imageFilename: 'produk.jpg',
          categoryId: 1,
        );

    expect(ok, isTrue);
    expect(api.lastCreateCategoryIdOnProduct, 1);
  });

  testWidgets('kartu produk menampilkan label kategori dari categoryId', (tester) async {
    final api = FakeApi()
      ..listProductsResult =
          ProductListResponse(products: [_product(categoryId: 1)], count: 1)
      ..listCategoriesResult = const CategoryListResponse(
        categories: [Category(id: 1, tenantId: 1, name: 'Minuman')],
        count: 1,
      );
    await _pump(tester, api);

    final label = find.byKey(const Key('product_category_label'));
    expect(label, findsOneWidget);
    expect(find.descendant(of: label, matching: find.text('Minuman')), findsOneWidget);
  });

  testWidgets('kartu produk tanpa kategori tidak menampilkan label kategori',
      (tester) async {
    final api = FakeApi()
      ..listProductsResult =
          ProductListResponse(products: [_product(categoryId: null)], count: 1)
      ..listCategoriesResult = const CategoryListResponse(
        categories: [Category(id: 1, tenantId: 1, name: 'Minuman')],
        count: 1,
      );
    await _pump(tester, api);

    expect(find.byKey(const Key('product_category_label')), findsNothing);
  });
}
