import '../api/models.dart';

/// Pure helpers for the Checkout (Kasir) screen — no Flutter/Riverpod deps so
/// they are unit-testable directly.

/// Parse + validate the new-item input row into a [CheckoutLineItem].
/// Returns `(item: null, error: <pesan id>)` when invalid, else the item.
({CheckoutLineItem? item, String? error}) parseLineItem(
    String product, String qtyText, String priceText) {
  final name = product.trim();
  if (name.isEmpty) {
    return (item: null, error: 'Nama produk wajib diisi.');
  }
  final qty = int.tryParse(qtyText.trim());
  if (qty == null || qty <= 0) {
    return (item: null, error: 'Qty harus angka lebih dari 0.');
  }
  final price = int.tryParse(priceText.trim());
  if (price == null || price < 0) {
    return (item: null, error: 'Harga harus angka 0 atau lebih.');
  }
  return (
    item: CheckoutLineItem(product: name, qty: qty, unitPrice: price),
    error: null,
  );
}

bool canConfirm(List<CheckoutLineItem> items) => items.isNotEmpty;

int grandTotal(List<CheckoutLineItem> items) =>
    items.fold(0, (sum, it) => sum + it.total);

List<CheckoutLineItem> withItem(
        List<CheckoutLineItem> items, CheckoutLineItem item) =>
    [...items, item];

List<CheckoutLineItem> withoutItemAt(List<CheckoutLineItem> items, int index) {
  if (index < 0 || index >= items.length) return items;
  final copy = [...items];
  copy.removeAt(index);
  return copy;
}
