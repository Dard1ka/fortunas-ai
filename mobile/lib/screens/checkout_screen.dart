import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../api/models.dart';
import '../checkout/checkout_controller.dart';
import '../checkout/checkout_rules.dart';
import '../checkout/checkout_state.dart';
import '../theme/tokens.dart';
import '../ui/pill.dart';
import '../ui/screen_header.dart';

/// CheckoutScreen — manual multi-item "kasir" flow over POST /checkout/confirm.
/// Form mode collects line items; success mode shows the recorded invoice.
class CheckoutScreen extends ConsumerStatefulWidget {
  const CheckoutScreen({super.key});
  @override
  ConsumerState<CheckoutScreen> createState() => _CheckoutScreenState();
}

class _CheckoutScreenState extends ConsumerState<CheckoutScreen> {
  static final _rp =
      NumberFormat.currency(locale: 'id_ID', symbol: 'Rp ', decimalDigits: 0);

  final _customer = TextEditingController();
  final _product = TextEditingController();
  final _qty = TextEditingController();
  final _price = TextEditingController();
  String? _itemError;

  @override
  void initState() {
    super.initState();
    // Notifier is app-lifetime; clear any stale state from a previous visit.
    Future.microtask(() => ref.read(checkoutControllerProvider.notifier).reset());
  }

  @override
  void dispose() {
    _customer.dispose();
    _product.dispose();
    _qty.dispose();
    _price.dispose();
    super.dispose();
  }

  void _add() {
    final parsed = parseLineItem(_product.text, _qty.text, _price.text);
    if (parsed.error != null) {
      setState(() => _itemError = parsed.error);
      return;
    }
    ref.read(checkoutControllerProvider.notifier).addItem(parsed.item!);
    _product.clear();
    _qty.clear();
    _price.clear();
    setState(() => _itemError = null);
  }

  void _newTransaction() {
    ref.read(checkoutControllerProvider.notifier).reset();
    _customer.clear();
    _product.clear();
    _qty.clear();
    _price.clear();
    setState(() => _itemError = null);
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(checkoutControllerProvider);
    return Scaffold(
      backgroundColor: FortunasColors.bg,
      body: SafeArea(
        child: state.result != null
            ? _SuccessView(result: state.result!, rp: _rp, onNew: _newTransaction, onBack: () => context.pop())
            : _buildForm(state),
      ),
    );
  }

  Widget _buildForm(CheckoutState state) {
    final items = state.items;
    return Column(
      children: [
        // Scrollable content
        Expanded(
          child: ListView(
            padding: const EdgeInsets.only(bottom: 8),
            children: [
              const ScreenHeader(),
              Padding(
                padding: const EdgeInsets.fromLTRB(18, 4, 18, 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Pill.text('KASIR · CHECKOUT', monoFont: true),
                    const SizedBox(height: 10),
                    Text('Catat penjualan',
                        style: display(fontSize: 22, letterSpacing: -0.4, height: 1.2)),
                    const SizedBox(height: 4),
                    Text('Tambah item satu per satu, lalu konfirmasi.',
                        style: body(fontSize: 12.5, color: FortunasColors.ink3)),
                  ],
                ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(18, 0, 18, 12),
                child: _Field(
                  fieldKey: const Key('checkout_customer'),
                  label: 'NAMA PELANGGAN (OPSIONAL)',
                  controller: _customer,
                  hint: 'mis. Bu Sari',
                ),
              ),
              // New-item input card
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 18),
                child: Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: FortunasColors.surface,
                    border: Border.all(color: FortunasColors.ink, width: 1.5),
                    borderRadius: BorderRadius.circular(16),
                    boxShadow: popShadow(offset: 2),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _Field(
                        fieldKey: const Key('checkout_product'),
                        label: 'PRODUK',
                        controller: _product,
                        hint: 'mis. Kopi susu',
                      ),
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          Expanded(
                            child: _Field(
                              fieldKey: const Key('checkout_qty'),
                              label: 'QTY',
                              controller: _qty,
                              hint: '1',
                              keyboardType: TextInputType.number,
                            ),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: _Field(
                              fieldKey: const Key('checkout_price'),
                              label: 'HARGA SATUAN',
                              controller: _price,
                              hint: '15000',
                              keyboardType: TextInputType.number,
                            ),
                          ),
                        ],
                      ),
                      if (_itemError != null) ...[
                        const SizedBox(height: 8),
                        Text(_itemError!, style: body(fontSize: 12, color: FortunasColors.error)),
                      ],
                      const SizedBox(height: 10),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton(
                          key: const Key('checkout_add'),
                          onPressed: _add,
                          child: const Text('Tambah item'),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              if (items.isNotEmpty) ...[
                const SizedBox(height: 14),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 18),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('ITEM (${items.length})',
                          style: mono(fontSize: 10, color: FortunasColors.ink3, letterSpacing: 0.8)),
                      const SizedBox(height: 8),
                      for (var i = 0; i < items.length; i++) ...[
                        _ItemRow(
                          item: items[i],
                          rp: _rp,
                          removeKey: Key('checkout_remove_$i'),
                          onRemove: () =>
                              ref.read(checkoutControllerProvider.notifier).removeItemAt(i),
                        ),
                        const SizedBox(height: 8),
                      ],
                    ],
                  ),
                ),
              ],
              if (state.errorMessage != null)
                Padding(
                  padding: const EdgeInsets.fromLTRB(18, 6, 18, 0),
                  child: _Banner(message: state.errorMessage!),
                ),
            ],
          ),
        ),
        // Pinned total + confirm bar
        Padding(
          padding: const EdgeInsets.fromLTRB(18, 8, 18, 16),
          child: Column(
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('TOTAL',
                      style: mono(fontSize: 11, color: FortunasColors.ink3, letterSpacing: 0.8)),
                  Text(_rp.format(grandTotal(items)),
                      style: display(fontSize: 22, weight: FontWeight.w700, letterSpacing: -0.5)),
                ],
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  key: const Key('checkout_confirm'),
                  onPressed: (!canConfirm(items) || state.submitting)
                      ? null
                      : () => ref
                          .read(checkoutControllerProvider.notifier)
                          .confirm(_customer.text),
                  child: Text(state.submitting ? 'Menyimpan…' : 'Konfirmasi'),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _Field extends StatelessWidget {
  final Key fieldKey;
  final String label;
  final TextEditingController controller;
  final String hint;
  final TextInputType? keyboardType;
  const _Field({
    required this.fieldKey,
    required this.label,
    required this.controller,
    required this.hint,
    this.keyboardType,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: mono(fontSize: 9.5, color: FortunasColors.ink3, letterSpacing: 0.6)),
        const SizedBox(height: 4),
        TextField(
          key: fieldKey,
          controller: controller,
          keyboardType: keyboardType,
          style: body(fontSize: 14, color: FortunasColors.ink),
          decoration: InputDecoration(
            hintText: hint,
            isDense: true,
            filled: true,
            fillColor: FortunasColors.surfaceSoft,
            contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: const BorderSide(color: FortunasColors.borderHair),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: const BorderSide(color: FortunasColors.borderHair),
            ),
          ),
        ),
      ],
    );
  }
}

class _ItemRow extends StatelessWidget {
  final CheckoutLineItem item;
  final NumberFormat rp;
  final Key removeKey;
  final VoidCallback onRemove;
  const _ItemRow({required this.item, required this.rp, required this.removeKey, required this.onRemove});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: FortunasColors.surface,
        border: Border.all(color: FortunasColors.borderHair),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(item.product, style: display(fontSize: 14, letterSpacing: -0.2)),
                const SizedBox(height: 2),
                Text('${item.qty} × ${rp.format(item.unitPrice)}',
                    style: body(fontSize: 12, color: FortunasColors.ink3)),
              ],
            ),
          ),
          Text(rp.format(item.total),
              style: display(fontSize: 14, weight: FontWeight.w600, letterSpacing: -0.2)),
          const SizedBox(width: 6),
          IconButton(
            key: removeKey,
            onPressed: onRemove,
            icon: const Icon(Icons.delete_outline, size: 20, color: FortunasColors.ink3),
            visualDensity: VisualDensity.compact,
          ),
        ],
      ),
    );
  }
}

class _Banner extends StatelessWidget {
  final String message;
  const _Banner({required this.message});
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: FortunasColors.peachSoft,
        border: Border.all(color: FortunasColors.ink, width: 1.5),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Text(message, style: body(fontSize: 13)),
    );
  }
}

class _SuccessView extends StatelessWidget {
  final CheckoutConfirmResponse result;
  final NumberFormat rp;
  final VoidCallback onNew;
  final VoidCallback onBack;
  const _SuccessView({required this.result, required this.rp, required this.onNew, required this.onBack});

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.only(bottom: 40),
      children: [
        const ScreenHeader(),
        Padding(
          padding: const EdgeInsets.fromLTRB(18, 8, 18, 12),
          child: Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              color: FortunasColors.ink,
              borderRadius: BorderRadius.circular(20),
              boxShadow: popShadow(),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(children: [
                  const Icon(Icons.check_circle, color: FortunasColors.lime, size: 22),
                  const SizedBox(width: 8),
                  Text('TRANSAKSI TERCATAT',
                      style: mono(fontSize: 11, color: FortunasColors.lime, letterSpacing: 0.8)),
                ]),
                const SizedBox(height: 12),
                if (result.invoice != null)
                  Text(result.invoice!,
                      style: display(fontSize: 20, color: Colors.white, letterSpacing: -0.4)),
                const SizedBox(height: 4),
                Text('${result.itemCount} item · ${rp.format(result.grandTotal)}',
                    style: body(fontSize: 13, color: const Color(0xCCFFFFFF))),
                if (result.reply.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  Text(result.reply,
                      style: body(fontSize: 13, color: const Color(0xE6FFFFFF), height: 1.5)),
                ],
              ],
            ),
          ),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(18, 4, 18, 0),
          child: Column(
            children: [
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  key: const Key('checkout_new'),
                  onPressed: onNew,
                  child: const Text('Transaksi Baru'),
                ),
              ),
              const SizedBox(height: 10),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton(onPressed: onBack, child: const Text('Kembali')),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
