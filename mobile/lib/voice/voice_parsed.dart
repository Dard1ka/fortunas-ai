import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../api/models.dart';
import '../theme/tokens.dart';
import '../ui/pill.dart';

/// VoiceParsed — editable confirmation card supporting MULTIPLE line items.
/// React equivalent: frontend/src/voice/VoiceParsed.jsx
class VoiceParsed extends StatefulWidget {
  final ParsedTransaction tx;
  final bool submitting;
  final String? error;
  final ValueChanged<ParsedTransaction> onChange;
  final VoidCallback onRetry;
  final VoidCallback onConfirm;

  const VoiceParsed({
    super.key,
    required this.tx,
    required this.submitting,
    required this.error,
    required this.onChange,
    required this.onRetry,
    required this.onConfirm,
  });

  @override
  State<VoiceParsed> createState() => _VoiceParsedState();
}

class _VoiceParsedState extends State<VoiceParsed> {
  static final _rp =
      NumberFormat.currency(locale: 'id_ID', symbol: 'Rp ', decimalDigits: 0);

  void _removeItem(int index) {
    final next = [...widget.tx.items]..removeAt(index);
    widget.onChange(widget.tx.copyWith(items: next));
  }

  void _updateItem(int index, LineItem item) {
    final next = [...widget.tx.items];
    next[index] = item;
    widget.onChange(widget.tx.copyWith(items: next));
  }

  @override
  Widget build(BuildContext context) {
    final tx = widget.tx;
    final n = tx.itemCount;

    return ListView(
      padding: const EdgeInsets.fromLTRB(18, 14, 18, 100),
      children: [
        // Summary line: "AI menangkap N barang …"
        Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: Text.rich(
            TextSpan(
              children: [
                TextSpan(text: 'AI menangkap ', style: body(fontSize: 13, color: FortunasColors.ink2)),
                TextSpan(
                  text: '$n barang',
                  style: body(fontSize: 13, weight: FontWeight.w700, color: FortunasColors.ink2),
                ),
                TextSpan(text: ' dalam 1 transaksi. Periksa lalu konfirmasi.', style: body(fontSize: 13, color: FortunasColors.ink2)),
              ],
            ),
          ),
        ),

        // Invoice + customer header chip
        Container(
          padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
          decoration: BoxDecoration(
            color: FortunasColors.violet,
            border: Border.all(color: FortunasColors.ink, width: 1.5),
            borderRadius: BorderRadius.circular(14),
            boxShadow: popShadow(offset: 2),
          ),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text('INVOICE',
                        style: mono(fontSize: 10, color: const Color(0xCCFFFFFF), letterSpacing: 0.6)),
                    const SizedBox(height: 2),
                    Text(tx.invoice,
                        style: display(fontSize: 18, weight: FontWeight.w700, color: Colors.white, height: 1.1)),
                  ],
                ),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text('PELANGGAN',
                      style: mono(fontSize: 9, color: const Color(0xB3FFFFFF), letterSpacing: 0.6)),
                  const SizedBox(height: 2),
                  Text(tx.customer.isEmpty ? '—' : tx.customer,
                      style: body(fontSize: 13, weight: FontWeight.w600, color: Colors.white)),
                ],
              ),
            ],
          ),
        ),

        const SizedBox(height: 12),

        // ── Line items ──────────────────────────────────────────
        for (int i = 0; i < tx.items.length; i++) ...[
          _ItemCard(
            index: i,
            item: tx.items[i],
            rp: _rp,
            canRemove: tx.items.length > 1,
            onChanged: (it) => _updateItem(i, it),
            onRemove: () => _removeItem(i),
          ),
          const SizedBox(height: 10),
        ],

        const SizedBox(height: 4),

        // ── Grand total ─────────────────────────────────────────
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          decoration: BoxDecoration(
            color: FortunasColors.ink,
            borderRadius: BorderRadius.circular(14),
            boxShadow: popShadow(offset: 3),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text('TOTAL ${tx.totalQty} ITEM',
                      style: mono(fontSize: 10, color: const Color(0xCCFFFFFF), letterSpacing: 0.6)),
                  const SizedBox(height: 2),
                  Text('$n produk berbeda',
                      style: body(fontSize: 11, color: const Color(0x99FFFFFF))),
                ],
              ),
              Text(_rp.format(tx.grandTotal),
                  style: display(fontSize: 22, weight: FontWeight.w700, color: FortunasColors.lime, letterSpacing: -0.5)),
            ],
          ),
        ),

        const SizedBox(height: 14),
        Wrap(
          spacing: 8, runSpacing: 8,
          crossAxisAlignment: WrapCrossAlignment.center,
          children: [
            Text('AKAN DISIMPAN KE:',
                style: mono(fontSize: 10, color: FortunasColors.ink3, letterSpacing: 0.6)),
            Pill.text('Google Sheets', small: true, monoFont: true, background: FortunasColors.surface),
            Pill.text('BigQuery', small: true, monoFont: true, background: FortunasColors.surface),
          ],
        ),

        if (widget.error != null) ...[
          const SizedBox(height: 14),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
            decoration: BoxDecoration(
              color: FortunasColors.peachSoft,
              border: Border.all(color: FortunasColors.ink, width: 1.5),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Text(widget.error!, style: body(fontSize: 12.5, color: FortunasColors.ink2)),
          ),
        ],

        const SizedBox(height: 18),
        Row(
          children: [
            Expanded(
              flex: 1,
              child: _ActionButton(
                disabled: widget.submitting,
                onTap: widget.onRetry,
                bg: FortunasColors.surface,
                fg: FortunasColors.ink,
                label: 'Ulangi',
                icon: Icons.mic_outlined,
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              flex: 2,
              child: _ActionButton(
                disabled: widget.submitting,
                onTap: widget.submitting ? null : widget.onConfirm,
                bg: FortunasColors.ink,
                fg: FortunasColors.lime,
                label: widget.submitting ? 'Menyimpan…' : 'Konfirmasi & Simpan',
                icon: widget.submitting ? null : Icons.check,
                showSpinner: widget.submitting,
              ),
            ),
          ],
        ),
      ],
    );
  }
}

/// A single editable line-item card.
class _ItemCard extends StatefulWidget {
  final int index;
  final LineItem item;
  final NumberFormat rp;
  final bool canRemove;
  final ValueChanged<LineItem> onChanged;
  final VoidCallback onRemove;

  const _ItemCard({
    required this.index,
    required this.item,
    required this.rp,
    required this.canRemove,
    required this.onChanged,
    required this.onRemove,
  });

  @override
  State<_ItemCard> createState() => _ItemCardState();
}

class _ItemCardState extends State<_ItemCard> {
  bool _editing = false;
  late TextEditingController _productCtl;
  late TextEditingController _qtyCtl;
  late TextEditingController _priceCtl;

  @override
  void initState() {
    super.initState();
    _productCtl = TextEditingController(text: widget.item.product);
    _qtyCtl = TextEditingController(text: widget.item.qty.toString());
    _priceCtl = TextEditingController(text: widget.item.unitPrice.toString());
  }

  @override
  void dispose() {
    _productCtl.dispose();
    _qtyCtl.dispose();
    _priceCtl.dispose();
    super.dispose();
  }

  void _commit() {
    final qty = int.tryParse(_qtyCtl.text.trim()) ?? widget.item.qty;
    final price = int.tryParse(_priceCtl.text.trim()) ?? widget.item.unitPrice;
    widget.onChanged(widget.item.copyWith(
      product: _productCtl.text.trim().isEmpty ? widget.item.product : _productCtl.text.trim(),
      qty: qty,
      unitPrice: price,
    ));
  }

  @override
  Widget build(BuildContext context) {
    final item = widget.item;
    return Container(
      decoration: BoxDecoration(
        color: FortunasColors.surface,
        border: Border.all(color: FortunasColors.ink, width: 1.5),
        borderRadius: BorderRadius.circular(16),
        boxShadow: popShadow(offset: 2),
      ),
      padding: const EdgeInsets.fromLTRB(14, 12, 12, 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Row 1: index badge + product + edit/remove
          Row(
            children: [
              Container(
                width: 22, height: 22,
                decoration: BoxDecoration(
                  color: FortunasColors.lime,
                  border: Border.all(color: FortunasColors.ink, width: 1.2),
                  borderRadius: BorderRadius.circular(7),
                ),
                child: Center(
                  child: Text('${widget.index + 1}',
                      style: mono(fontSize: 11, color: FortunasColors.ink, letterSpacing: 0)),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _editing
                    ? _MiniField(controller: _productCtl, hint: 'Nama produk')
                    : Text(item.product,
                        style: display(fontSize: 15, weight: FontWeight.w700, color: FortunasColors.ink, letterSpacing: -0.2, height: 1.15)),
              ),
              _IconBtn(
                icon: _editing ? Icons.check : Icons.edit_outlined,
                onTap: () {
                  if (_editing) _commit();
                  setState(() => _editing = !_editing);
                },
              ),
              if (widget.canRemove) ...[
                const SizedBox(width: 6),
                _IconBtn(icon: Icons.close, onTap: widget.onRemove),
              ],
            ],
          ),
          const SizedBox(height: 10),
          // Row 2: qty × price = subtotal
          Row(
            children: [
              Expanded(
                child: _editing
                    ? _LabeledMini(label: 'JUMLAH', controller: _qtyCtl, keyboardType: TextInputType.number)
                    : _Stat(label: 'JUMLAH', value: '${item.qty}'),
              ),
              Expanded(
                child: _editing
                    ? _LabeledMini(label: 'HARGA', controller: _priceCtl, keyboardType: TextInputType.number)
                    : _Stat(label: 'HARGA SATUAN', value: widget.rp.format(item.unitPrice)),
              ),
              _Stat(label: 'SUBTOTAL', value: widget.rp.format(item.total), accent: true, alignEnd: true),
            ],
          ),
        ],
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  final String label;
  final String value;
  final bool accent;
  final bool alignEnd;
  const _Stat({required this.label, required this.value, this.accent = false, this.alignEnd = false});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: alignEnd ? CrossAxisAlignment.end : CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(label, style: mono(fontSize: 9, color: FortunasColors.ink3, letterSpacing: 0.4)),
        const SizedBox(height: 3),
        Text(value,
            style: display(
              fontSize: 13.5,
              weight: FontWeight.w700,
              color: accent ? FortunasColors.violet : FortunasColors.ink,
              letterSpacing: -0.2,
              height: 1.1,
            )),
      ],
    );
  }
}

class _MiniField extends StatelessWidget {
  final TextEditingController controller;
  final String hint;
  const _MiniField({required this.controller, required this.hint});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 34,
      child: TextField(
        controller: controller,
        style: display(fontSize: 14, weight: FontWeight.w700, color: FortunasColors.ink),
        decoration: InputDecoration(
          hintText: hint,
          isDense: true,
          filled: true,
          fillColor: FortunasColors.surfaceSoft,
          contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
          enabledBorder: OutlineInputBorder(
            borderSide: const BorderSide(color: FortunasColors.ink, width: 1.5),
            borderRadius: BorderRadius.circular(8),
          ),
          focusedBorder: OutlineInputBorder(
            borderSide: const BorderSide(color: FortunasColors.violet, width: 1.5),
            borderRadius: BorderRadius.circular(8),
          ),
        ),
      ),
    );
  }
}

class _LabeledMini extends StatelessWidget {
  final String label;
  final TextEditingController controller;
  final TextInputType? keyboardType;
  const _LabeledMini({required this.label, required this.controller, this.keyboardType});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(label, style: mono(fontSize: 9, color: FortunasColors.ink3, letterSpacing: 0.4)),
          const SizedBox(height: 3),
          _MiniField(controller: controller, hint: ''),
        ],
      ),
    );
  }
}

class _IconBtn extends StatelessWidget {
  final IconData icon;
  final VoidCallback onTap;
  const _IconBtn({required this.icon, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Container(
          width: 30, height: 30,
          decoration: BoxDecoration(
            color: FortunasColors.surfaceSoft,
            border: Border.all(color: FortunasColors.ink, width: 1.2),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(icon, size: 15, color: FortunasColors.ink),
        ),
      ),
    );
  }
}

class _ActionButton extends StatelessWidget {
  final bool disabled;
  final VoidCallback? onTap;
  final Color bg;
  final Color fg;
  final String label;
  final IconData? icon;
  final bool showSpinner;

  const _ActionButton({
    required this.disabled,
    required this.onTap,
    required this.bg,
    required this.fg,
    required this.label,
    this.icon,
    this.showSpinner = false,
  });

  @override
  Widget build(BuildContext context) {
    return Opacity(
      opacity: disabled ? 0.6 : 1.0,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: disabled ? null : onTap,
          borderRadius: BorderRadius.circular(14),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
            decoration: BoxDecoration(
              color: bg,
              border: Border.all(color: FortunasColors.ink, width: 1.5),
              borderRadius: BorderRadius.circular(14),
              boxShadow: popShadow(offset: bg == FortunasColors.ink ? 4 : 2),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                if (showSpinner)
                  SizedBox(
                    width: 18, height: 18,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor: AlwaysStoppedAnimation(fg),
                      backgroundColor: fg.withValues(alpha: 0.35),
                    ),
                  )
                else if (icon != null)
                  Icon(icon, size: 16, color: fg),
                if (showSpinner || icon != null) const SizedBox(width: 8),
                Text(label, style: body(fontSize: 13, weight: FontWeight.w700, color: fg)),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
