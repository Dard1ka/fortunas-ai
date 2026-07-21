import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/api/client.dart';
import 'package:fortunas_ai/api/models.dart';
import 'package:fortunas_ai/screens/products_screen.dart';

import '../support/fakes.dart';

ProductItem _product({required int id, int? categoryId}) => ProductItem(
      id: id,
      tenantId: 1,
      name: 'Produk $id',
      stockCode: 'pr-00$id',
      categoryId: categoryId,
    );

Category _category({int id = 1, String name = 'Minuman'}) =>
    Category(id: id, tenantId: 1, name: name);

Future<void> _pump(WidgetTester tester, FakeApi api) async {
  await tester.pumpWidget(ProviderScope(
    overrides: [apiProvider.overrideWithValue(api)],
    child: const MaterialApp(home: ProductsScreen()),
  ));
  await tester.pumpAndSettle();
}

Future<void> _openCategorySheet(WidgetTester tester) async {
  await tester.tap(find.byKey(const Key('products_manage_categories')));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('tambah kategori baru memanggil createCategory dengan nama yang diinput',
      (tester) async {
    final api = FakeApi()..createCategoryResult = _category(id: 2, name: 'Makanan');
    await _pump(tester, api);
    await _openCategorySheet(tester);

    await tester.enterText(find.byKey(const Key('category_add_field')), 'Makanan');
    await tester.tap(find.byKey(const Key('category_add_btn')));
    await tester.pumpAndSettle();

    expect(api.lastCreateCategoryName, 'Makanan');
  });

  testWidgets('sheet menampilkan daftar kategori yang sudah ada', (tester) async {
    final api = FakeApi()
      ..listCategoriesResult = CategoryListResponse(
          categories: [_category(id: 1, name: 'Minuman'), _category(id: 2, name: 'Makanan')],
          count: 2);
    await _pump(tester, api);
    await _openCategorySheet(tester);

    expect(find.text('Minuman'), findsOneWidget);
    expect(find.text('Makanan'), findsOneWidget);
  });

  testWidgets(
      'hapus kategori menampilkan dialog konfirmasi jumlah produk terdampak, '
      'konfirmasi memanggil deleteCategory', (tester) async {
    final api = FakeApi()
      ..listCategoriesResult =
          CategoryListResponse(categories: [_category(id: 1, name: 'Minuman')], count: 1)
      ..listProductsResult = ProductListResponse(
        products: [
          _product(id: 1, categoryId: 1),
          _product(id: 2, categoryId: 1),
          _product(id: 3, categoryId: null),
        ],
        count: 3,
      );
    await _pump(tester, api);
    await _openCategorySheet(tester);

    await tester.tap(find.byKey(const Key('category_delete_1')));
    await tester.pumpAndSettle();

    expect(find.textContaining('2 produk'), findsOneWidget);

    await tester.tap(find.byKey(const Key('category_delete_confirm')));
    await tester.pumpAndSettle();

    expect(api.lastDeleteCategoryId, 1);
  });

  testWidgets('hapus kategori: Batal tidak memanggil deleteCategory', (tester) async {
    final api = FakeApi()
      ..listCategoriesResult =
          CategoryListResponse(categories: [_category(id: 1, name: 'Minuman')], count: 1)
      ..listProductsResult =
          ProductListResponse(products: [_product(id: 1, categoryId: 1)], count: 1);
    await _pump(tester, api);
    await _openCategorySheet(tester);

    await tester.tap(find.byKey(const Key('category_delete_1')));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Batal'));
    await tester.pumpAndSettle();

    expect(api.lastDeleteCategoryId, isNull);
  });
}
