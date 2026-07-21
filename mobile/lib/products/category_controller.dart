import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../api/client.dart';
import '../api/errors.dart';
import '../api/models.dart';

class CategoryState {
  final bool loading;
  final List<Category> categories;
  final String? errorMessage;
  const CategoryState({this.loading = false, this.categories = const [], this.errorMessage});
  CategoryState copyWith({bool? loading, List<Category>? categories, String? errorMessage, bool clearError = false}) =>
      CategoryState(
        loading: loading ?? this.loading,
        categories: categories ?? this.categories,
        errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
      );
}

class CategoryController extends AutoDisposeNotifier<CategoryState> {
  @override
  CategoryState build() => const CategoryState();

  Future<void> load() async {
    state = state.copyWith(loading: true, clearError: true);
    try {
      final resp = await ref.read(apiProvider).listCategories();
      state = state.copyWith(loading: false, categories: resp.categories);
    } catch (e) {
      state = state.copyWith(loading: false, errorMessage: humanizeError(e));
    }
  }

  Future<bool> create(String name) async {
    state = state.copyWith(clearError: true);
    try {
      await ref.read(apiProvider).createCategory(name);
      await load();
      return true;
    } catch (e) {
      state = state.copyWith(errorMessage: humanizeError(e));
      return false;
    }
  }

  Future<void> remove(int categoryId) async {
    try {
      await ref.read(apiProvider).deleteCategory(categoryId);
      await load();
    } catch (e) {
      state = state.copyWith(errorMessage: humanizeError(e));
    }
  }
}

final categoryControllerProvider =
    NotifierProvider.autoDispose<CategoryController, CategoryState>(CategoryController.new);
