import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fortunas_ai/api/client.dart';
import 'package:fortunas_ai/api/models.dart';
import 'package:fortunas_ai/products/product_controller.dart';
import 'package:flutter_test/flutter_test.dart';

import '../support/fakes.dart';

ProductItem _p(int id, String name, {int? stock}) => ProductItem(
    id: id, tenantId: 1, name: name, stockCode: 'ko-00$id', stock: stock);

ProviderContainer _c(FakeApi api) =>
    ProviderContainer(overrides: [apiProvider.overrideWithValue(api)]);

void main() {
  test('create passes stock through to api', () async {
    final api = FakeApi()
      ..listProductsResult = const ProductListResponse(products: [], count: 0)
      ..createProductResult = _p(1, 'Es Teh', stock: 25);
    final c = _c(api);
    final ok = await c.read(productControllerProvider.notifier).create(
        name: 'Es Teh', description: '', imageBytes: [1], imageFilename: 'f.png', stock: 25);
    expect(ok, true);
    expect(api.lastCreateStock, 25);
  });

  test('setStock success reloads and clears error', () async {
    final api = FakeApi()
      ..listProductsResult = ProductListResponse(products: [_p(1, 'Kopi', stock: 40)], count: 1)
      ..setStockResult = _p(1, 'Kopi', stock: 40);
    final c = _c(api);
    final ok = await c.read(productControllerProvider.notifier).setStock(1, 40);
    expect(ok, true);
    expect(api.lastSetStock, (1, 40));
    expect(c.read(productControllerProvider).products.first.stock, 40);
  });

  test('setStock error surfaces message, returns false', () async {
    final api = FakeApi()..setStockError = Exception('boom');
    final c = _c(api);
    final ok = await c.read(productControllerProvider.notifier).setStock(1, 5);
    expect(ok, false);
    expect(c.read(productControllerProvider).errorMessage, isNotNull);
  });
}
