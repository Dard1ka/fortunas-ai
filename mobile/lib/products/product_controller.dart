import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/client.dart';
import '../api/errors.dart';
import '../api/models.dart';

/// Controller katalog produk UMKM: list + create (gambar wajib).
/// Pola mengikuti customer_loyalty_controllers.dart.
class ProductState {
  final bool loading;
  final bool submitting;
  final List<ProductItem> products;
  final bool needsOnboarding;
  final String? errorMessage;

  const ProductState({
    this.loading = false,
    this.submitting = false,
    this.products = const [],
    this.needsOnboarding = false,
    this.errorMessage,
  });

  ProductState copyWith({
    bool? loading,
    bool? submitting,
    List<ProductItem>? products,
    bool? needsOnboarding,
    String? errorMessage,
    bool clearError = false,
  }) =>
      ProductState(
        loading: loading ?? this.loading,
        submitting: submitting ?? this.submitting,
        products: products ?? this.products,
        needsOnboarding: needsOnboarding ?? this.needsOnboarding,
        errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
      );
}

class ProductController extends AutoDisposeNotifier<ProductState> {
  @override
  ProductState build() => const ProductState();

  Future<void> load() async {
    state = state.copyWith(loading: true, clearError: true);
    try {
      final resp = await ref.read(apiProvider).listProducts();
      state = state.copyWith(
        loading: false,
        products: resp.products,
        needsOnboarding: resp.needsOnboarding,
      );
    } catch (e) {
      state = state.copyWith(loading: false, errorMessage: humanizeError(e));
    }
  }

  /// Return true bila produk berhasil dibuat.
  Future<bool> create({
    required String name,
    required String description,
    required List<int> imageBytes,
    required String imageFilename,
    int? stock,
  }) async {
    state = state.copyWith(submitting: true, clearError: true);
    try {
      await ref.read(apiProvider).createProduct(
            name: name,
            description: description,
            imageBytes: imageBytes,
            imageFilename: imageFilename,
            stock: stock,
          );
      state = state.copyWith(submitting: false);
      await load();
      return true;
    } catch (e) {
      state = state.copyWith(submitting: false, errorMessage: humanizeError(e));
      return false;
    }
  }

  Future<void> remove(int productId) async {
    try {
      await ref.read(apiProvider).deleteProduct(productId);
      await load();
    } catch (e) {
      state = state.copyWith(errorMessage: humanizeError(e));
    }
  }

  /// Set/restock stok produk. Return true bila berhasil.
  Future<bool> setStock(int productId, int? stock) async {
    state = state.copyWith(submitting: true, clearError: true);
    try {
      await ref.read(apiProvider).setStock(productId, stock);
      state = state.copyWith(submitting: false);
      await load();
      return true;
    } catch (e) {
      state = state.copyWith(submitting: false, errorMessage: humanizeError(e));
      return false;
    }
  }
}

final productControllerProvider =
    NotifierProvider.autoDispose<ProductController, ProductState>(ProductController.new);
