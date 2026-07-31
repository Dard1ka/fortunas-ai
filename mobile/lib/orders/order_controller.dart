import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/client.dart';
import '../api/errors.dart';
import '../api/models.dart';

/// Controller inbox pesanan UMKM: list + aksi accept/reject/complete.
/// Pola mengikuti products/product_controller.dart.
class OrderInboxState {
  final bool loading;

  /// id pesanan yang aksinya sedang diproses — bukan bool, supaya hanya tombol
  /// di kartu ITU yang dinonaktifkan, bukan seluruh layar.
  final int? submittingId;
  final List<UmkmOrder> orders;
  final String? errorMessage;

  const OrderInboxState({
    this.loading = false,
    this.submittingId,
    this.orders = const [],
    this.errorMessage,
  });

  OrderInboxState copyWith({
    bool? loading,
    int? submittingId,
    bool clearSubmitting = false,
    List<UmkmOrder>? orders,
    String? errorMessage,
    bool clearError = false,
  }) =>
      OrderInboxState(
        loading: loading ?? this.loading,
        submittingId:
            clearSubmitting ? null : (submittingId ?? this.submittingId),
        orders: orders ?? this.orders,
        errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
      );
}

class OrderController extends AutoDisposeNotifier<OrderInboxState> {
  @override
  OrderInboxState build() => const OrderInboxState();

  /// status null → backend memberi yang butuh tindakan (paid + accepted).
  Future<void> load({String? status}) async {
    state = state.copyWith(loading: true, clearError: true);
    try {
      final resp = await ref.read(apiProvider).listOrders(status: status);
      state = state.copyWith(loading: false, orders: resp.orders);
    } catch (e) {
      state = state.copyWith(loading: false, errorMessage: humanizeError(e));
    }
  }

  Future<bool> accept(int orderId) => _run(orderId, (api) => api.acceptOrder(orderId));
  Future<bool> reject(int orderId) => _run(orderId, (api) => api.rejectOrder(orderId));
  Future<bool> complete(int orderId) =>
      _run(orderId, (api) => api.completeOrder(orderId));

  /// Aksi TIDAK optimistis: setelah sukses, daftar dimuat ulang dari server.
  /// Status pesanan bisa berubah di belakang layar lewat webhook gateway, jadi
  /// layar tak boleh menampilkan status hasil asumsi klien.
  Future<bool> _run(
      int orderId, Future<UmkmOrder> Function(FortunasApi api) action) async {
    state = state.copyWith(submittingId: orderId, clearError: true);
    try {
      await action(ref.read(apiProvider));
      state = state.copyWith(clearSubmitting: true);
      await load();
      return true;
    } catch (e) {
      state = state.copyWith(
          clearSubmitting: true, errorMessage: humanizeError(e));
      return false;
    }
  }
}

final orderControllerProvider =
    NotifierProvider.autoDispose<OrderController, OrderInboxState>(
        OrderController.new);
