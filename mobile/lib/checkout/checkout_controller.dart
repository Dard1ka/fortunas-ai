import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/client.dart';
import '../api/errors.dart';
import '../api/models.dart';
import '../auth/auth_controller.dart';
import '../history/tx_store.dart';
import 'checkout_rules.dart';
import 'checkout_state.dart';

class CheckoutController extends Notifier<CheckoutState> {
  @override
  CheckoutState build() => const CheckoutState();

  FortunasApi get _api => ref.read(apiProvider);

  void addItem(CheckoutLineItem item) =>
      state = state.copyWith(items: withItem(state.items, item), clearError: true);

  void removeItemAt(int index) =>
      state = state.copyWith(items: withoutItemAt(state.items, index));

  Future<void> confirm(String customerName) async {
    if (!canConfirm(state.items)) return;
    state = state.copyWith(submitting: true, clearError: true);
    try {
      final items = state.items;
      final resp = await _api.checkoutConfirm(CheckoutConfirmRequest(
        items: items,
        customer: customerName.trim(),
      ));
      state = state.copyWith(submitting: false, result: resp);
      // Catat ke riwayat transaksi terpadu (metode: kasir manual), dipisah
      // per-UMKM lewat tenantId. Non-fatal.
      final tenantId = ref.read(authControllerProvider).account?.tenantId;
      await addTxRecord(tenantId: tenantId, TxRecord(
        invoice: resp.invoice ?? '',
        method: TxMethod.kasir,
        customer: customerName.trim(),
        total: resp.grandTotal,
        savedAt: DateTime.now(),
        items: [
          for (final it in items)
            TxItem(
              product: it.product,
              qty: it.qty,
              unitPrice: it.unitPrice,
              total: it.total,
            ),
        ],
      ));
    } catch (e) {
      state = state.copyWith(submitting: false, errorMessage: humanizeError(e));
    }
  }

  void reset() => state = const CheckoutState();
}

final checkoutControllerProvider =
    NotifierProvider<CheckoutController, CheckoutState>(CheckoutController.new);
