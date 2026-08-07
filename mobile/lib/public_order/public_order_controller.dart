import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/client.dart';
import '../api/errors.dart';
import '../api/models.dart';

/// Fase alur pesan-publik pelanggan (tanpa akun).
enum PublicOrderPhase {
  code,     // input KODE UMKM
  menu,     // jelajah menu + keranjang
  order,    // pesanan dibuat → bayar (simulasi) + pantau status
}

/// State alur pesan-publik. Keranjang = map productId → qty; jumlah & total
/// dihitung dari `umkm.products` supaya harga selalu dari sumber server, bukan
/// disalin ke keranjang (harga bisa berubah antara buka menu dan checkout).
class PublicOrderState {
  final PublicOrderPhase phase;
  final bool loading;         // memuat menu / membuat pesanan / bayar
  final bool polling;         // refresh status pesanan
  final String? errorMessage;
  final PublicUmkm? umkm;
  final String search;        // filter menu client-side
  final Map<int, int> cart;   // productId → qty
  final PublicOrder? order;

  const PublicOrderState({
    this.phase = PublicOrderPhase.code,
    this.loading = false,
    this.polling = false,
    this.errorMessage,
    this.umkm,
    this.search = '',
    this.cart = const {},
    this.order,
  });

  PublicOrderState copyWith({
    PublicOrderPhase? phase,
    bool? loading,
    bool? polling,
    String? errorMessage,
    bool clearError = false,
    PublicUmkm? umkm,
    String? search,
    Map<int, int>? cart,
    PublicOrder? order,
    bool clearOrder = false,
  }) =>
      PublicOrderState(
        phase: phase ?? this.phase,
        loading: loading ?? this.loading,
        polling: polling ?? this.polling,
        errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
        umkm: umkm ?? this.umkm,
        search: search ?? this.search,
        cart: cart ?? this.cart,
        order: clearOrder ? null : (order ?? this.order),
      );

  /// Produk menu yang lolos filter pencarian (nama, case-insensitive).
  List<PublicMenuProduct> get visibleProducts {
    final all = umkm?.products ?? const <PublicMenuProduct>[];
    final q = search.trim().toLowerCase();
    if (q.isEmpty) return all;
    return all.where((p) => p.name.toLowerCase().contains(q)).toList();
  }

  int qtyOf(int productId) => cart[productId] ?? 0;

  int get itemCount => cart.values.fold(0, (a, b) => a + b);

  /// Total Rupiah keranjang, dihitung dari harga produk di menu (server).
  int get cartTotal {
    final byId = {
      for (final p in (umkm?.products ?? const <PublicMenuProduct>[])) p.id: p
    };
    var sum = 0;
    cart.forEach((pid, qty) {
      final price = byId[pid]?.price;
      if (price != null) sum += price * qty;
    });
    return sum;
  }
}

class PublicOrderController extends AutoDisposeNotifier<PublicOrderState> {
  @override
  PublicOrderState build() => const PublicOrderState();

  /// Ambil menu untuk sebuah kode UMKM → pindah ke fase `menu`.
  Future<void> loadMenu(String code) async {
    final trimmed = code.trim();
    if (trimmed.isEmpty) {
      state = state.copyWith(errorMessage: 'Masukkan kode UMKM dulu.');
      return;
    }
    state = state.copyWith(loading: true, clearError: true);
    try {
      final umkm = await ref.read(apiProvider).getPublicUmkm(trimmed);
      state = state.copyWith(
        loading: false,
        umkm: umkm,
        phase: PublicOrderPhase.menu,
        cart: const {},
        search: '',
      );
    } catch (e) {
      state = state.copyWith(loading: false, errorMessage: humanizeError(e));
    }
  }

  void setSearch(String q) => state = state.copyWith(search: q);

  /// Tambah 1. Dihalangi bila produk tak bisa dipesan atau melebihi stok
  /// yang dilacak (backend tetap validasi ulang; ini cuma cegah dini di UI).
  void increment(PublicMenuProduct p) {
    if (!p.orderable) return;
    final current = state.qtyOf(p.id);
    if (p.stock != null && current >= p.stock!) return;
    final next = Map<int, int>.from(state.cart)..[p.id] = current + 1;
    state = state.copyWith(cart: next, clearError: true);
  }

  void decrement(int productId) {
    final current = state.qtyOf(productId);
    if (current <= 0) return;
    final next = Map<int, int>.from(state.cart);
    if (current == 1) {
      next.remove(productId);
    } else {
      next[productId] = current - 1;
    }
    state = state.copyWith(cart: next);
  }

  void clearCart() => state = state.copyWith(cart: const {});

  /// Buat pesanan dari keranjang → fase `order`. Return true bila sukses.
  Future<bool> createOrder(
      {required String customerName, required String customerPhone}) async {
    if (state.cart.isEmpty) {
      state = state.copyWith(errorMessage: 'Keranjang masih kosong.');
      return false;
    }
    final code = state.umkm?.code ?? '';
    final items = state.cart.entries
        .map((e) => {'product_id': e.key, 'qty': e.value})
        .toList();
    state = state.copyWith(loading: true, clearError: true);
    try {
      final order = await ref.read(apiProvider).createPublicOrder(
            code,
            customerName: customerName.trim(),
            customerPhone: customerPhone.trim(),
            items: items,
          );
      state = state.copyWith(
          loading: false, order: order, phase: PublicOrderPhase.order);
      return true;
    } catch (e) {
      state = state.copyWith(loading: false, errorMessage: humanizeError(e));
      return false;
    }
  }

  /// Konfirmasi pembayaran QRIS statis ("Saya sudah bayar"), lalu segarkan status.
  Future<void> confirmPayment() async {
    final poid = state.order?.paymentOrderId;
    if (poid == null || poid.isEmpty) return;
    state = state.copyWith(loading: true, clearError: true);
    try {
      await ref.read(apiProvider).confirmPublicOrderPayment(poid);
      final fresh = await ref.read(apiProvider).getPublicOrderStatus(poid);
      state = state.copyWith(loading: false, order: fresh);
    } catch (e) {
      state = state.copyWith(loading: false, errorMessage: humanizeError(e));
    }
  }

  /// Poll status terkini (tombol "Perbarui status" / setelah bayar).
  Future<void> refreshStatus() async {
    final poid = state.order?.paymentOrderId;
    if (poid == null || poid.isEmpty) return;
    state = state.copyWith(polling: true, clearError: true);
    try {
      final fresh = await ref.read(apiProvider).getPublicOrderStatus(poid);
      state = state.copyWith(polling: false, order: fresh);
    } catch (e) {
      state = state.copyWith(polling: false, errorMessage: humanizeError(e));
    }
  }

  /// Kembali ke menu (tetap di UMKM yang sama), buang pesanan & keranjang.
  void backToMenu() => state = state.copyWith(
      phase: PublicOrderPhase.menu, clearOrder: true, cart: const {}, clearError: true);

  /// Reset penuh ke input kode (mis. mau pesan ke UMKM lain).
  void reset() => state = const PublicOrderState();
}

final publicOrderControllerProvider =
    NotifierProvider.autoDispose<PublicOrderController, PublicOrderState>(
        PublicOrderController.new);
