import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fortunas_ai/api/client.dart';
import 'package:fortunas_ai/api/models.dart';
import 'package:fortunas_ai/products/category_controller.dart';
import 'package:flutter_test/flutter_test.dart';
import '../support/fakes.dart';

ProviderContainer _c(FakeApi api) => ProviderContainer(overrides: [apiProvider.overrideWithValue(api)]);

void main() {
  test('load populates categories', () async {
    final api = FakeApi()..listCategoriesResult = const CategoryListResponse(
        categories: [Category(id: 1, tenantId: 1, name: 'Minuman')], count: 1);
    final c = _c(api);
    await c.read(categoryControllerProvider.notifier).load();
    expect(c.read(categoryControllerProvider).categories.first.name, 'Minuman');
  });

  test('create then reload', () async {
    final api = FakeApi()
      ..createCategoryResult = const Category(id: 2, tenantId: 1, name: 'Nasi')
      ..listCategoriesResult = const CategoryListResponse(
          categories: [Category(id: 2, tenantId: 1, name: 'Nasi')], count: 1);
    final c = _c(api);
    final ok = await c.read(categoryControllerProvider.notifier).create('Nasi');
    expect(ok, true);
    expect(api.lastCreateCategoryName, 'Nasi');
  });

  test('create error surfaces message', () async {
    final api = FakeApi()..createCategoryError = Exception('dup');
    final c = _c(api);
    final ok = await c.read(categoryControllerProvider.notifier).create('X');
    expect(ok, false);
    expect(c.read(categoryControllerProvider).errorMessage, isNotNull);
  });
}
