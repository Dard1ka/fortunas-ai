import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../api/models.dart';
import '../public_order/public_order_controller.dart';
import '../theme/tokens.dart';

/// Base URL backend — cermin dari api/client.dart (dipakai untuk URL gambar).
const _apiBase = String.fromEnvironment(
  'FORTUNAS_API',
  defaultValue: 'http://127.0.0.1:8000',
);

String _rupiah(int n) {
  final s = n.toString();
  final buf = StringBuffer('Rp ');
  for (int i = 0; i < s.length; i++) {
    if (i > 0 && (s.length - i) % 3 == 0) buf.write('.');
    buf.write(s[i]);
  }
  return buf.toString();
}

/// Alur pesan-publik pelanggan (tanpa akun): kode → menu → keranjang → bayar
/// (simulasi) → pantau status. Satu layar, tiga fase (lihat PublicOrderPhase),
/// supaya tak perlu banyak route untuk state yang saling terikat.
class PublicOrderScreen extends ConsumerStatefulWidget {
  const PublicOrderScreen({super.key});
  @override
  ConsumerState<PublicOrderScreen> createState() => _PublicOrderScreenState();
}

class _PublicOrderScreenState extends ConsumerState<PublicOrderScreen> {
  final _code = TextEditingController();
  final _search = TextEditingController();

  @override
  void dispose() {
    _code.dispose();
    _search.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final st = ref.watch(publicOrderControllerProvider);
    final ctrl = ref.read(publicOrderControllerProvider.notifier);

    return Scaffold(
      backgroundColor: FortunasColors.bg,
      appBar: AppBar(
        backgroundColor: FortunasColors.bg,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: FortunasColors.ink),
          onPressed: () {
            // Dari menu/pesanan → mundur satu fase; dari input kode → keluar.
            if (st.phase == PublicOrderPhase.menu) {
              ctrl.reset();
              _code.clear();
            } else if (st.phase == PublicOrderPhase.order) {
              ctrl.backToMenu();
            } else if (context.canPop()) {
              context.pop();
            } else {
              context.go('/login');
            }
          },
        ),
        title: Text(
          switch (st.phase) {
            PublicOrderPhase.code => 'Pesan tanpa akun',
            PublicOrderPhase.menu => st.umkm?.name ?? 'Menu',
            PublicOrderPhase.order => 'Status pesanan',
          },
          style: display(fontSize: 18, letterSpacing: -0.3),
        ),
      ),
      body: SafeArea(
        top: false,
        child: switch (st.phase) {
          PublicOrderPhase.code => _buildCode(st, ctrl),
          PublicOrderPhase.menu => _buildMenu(st, ctrl),
          PublicOrderPhase.order => _buildOrder(st, ctrl),
        },
      ),
    );
  }

  // ── Fase 1: input kode UMKM ──
  Widget _buildCode(PublicOrderState st, PublicOrderController ctrl) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(18, 12, 18, 30),
      children: [
        Text('Masukkan kode UMKM',
            style: display(fontSize: 24, letterSpacing: -0.4)),
        const SizedBox(height: 6),
        Text('Kode ada di etalase / struk toko (mis. KDS-001).',
            style: body(fontSize: 13, color: FortunasColors.ink3)),
        const SizedBox(height: 18),
        TextField(
          key: const Key('public_order_code'),
          controller: _code,
          textCapitalization: TextCapitalization.characters,
          textInputAction: TextInputAction.go,
          onSubmitted: (v) => ctrl.loadMenu(v),
          decoration: const InputDecoration(
            labelText: 'Kode UMKM',
            hintText: 'KDS-001',
          ),
        ),
        if (st.errorMessage != null) _errorText(st.errorMessage!),
        const SizedBox(height: 16),
        ElevatedButton(
          onPressed: st.loading ? null : () => ctrl.loadMenu(_code.text),
          child: st.loading ? _spinner() : const Text('Lihat Menu'),
        ),
      ],
    );
  }

  // ── Fase 2: menu grid + cari + keranjang ──
  Widget _buildMenu(PublicOrderState st, PublicOrderController ctrl) {
    final products = st.visibleProducts;
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(18, 4, 18, 8),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if ((st.umkm?.city ?? '').isNotEmpty)
                Text(st.umkm!.city,
                    style: mono(fontSize: 11, color: FortunasColors.ink3)),
              const SizedBox(height: 8),
              TextField(
                key: const Key('public_order_search'),
                controller: _search,
                onChanged: ctrl.setSearch,
                decoration: InputDecoration(
                  isDense: true,
                  hintText: 'Cari menu…',
                  prefixIcon: const Icon(Icons.search, size: 20),
                  suffixIcon: st.search.isEmpty
                      ? null
                      : IconButton(
                          icon: const Icon(Icons.close, size: 18),
                          onPressed: () {
                            _search.clear();
                            ctrl.setSearch('');
                          },
                        ),
                ),
              ),
            ],
          ),
        ),
        Expanded(
          child: products.isEmpty
              ? Center(
                  child: Text(
                    st.search.isEmpty
                        ? 'Belum ada menu di toko ini.'
                        : 'Menu "${st.search}" tak ditemukan.',
                    style: body(fontSize: 13, color: FortunasColors.ink3),
                  ),
                )
              : GridView.builder(
                  padding: const EdgeInsets.fromLTRB(18, 4, 18, 120),
                  gridDelegate:
                      const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2,
                    crossAxisSpacing: 12,
                    mainAxisSpacing: 12,
                    childAspectRatio: 0.68,
                  ),
                  itemCount: products.length,
                  itemBuilder: (_, i) => _MenuCard(
                    product: products[i],
                    qty: st.qtyOf(products[i].id),
                    onAdd: () => ctrl.increment(products[i]),
                    onRemove: () => ctrl.decrement(products[i].id),
                  ),
                ),
        ),
        if (st.errorMessage != null)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 18),
            child: _errorText(st.errorMessage!),
          ),
        _cartBar(st, ctrl),
      ],
    );
  }

  Widget _cartBar(PublicOrderState st, PublicOrderController ctrl) {
    if (st.itemCount == 0) return const SizedBox.shrink();
    return SafeArea(
      top: false,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(18, 6, 18, 10),
        child: Container(
          padding: const EdgeInsets.fromLTRB(14, 10, 10, 10),
          decoration: BoxDecoration(
            color: FortunasColors.ink,
            borderRadius: BorderRadius.circular(FortunasRadius.lg),
            boxShadow: popShadow(offset: 3),
          ),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('${st.itemCount} item',
                        style: mono(fontSize: 11, color: FortunasColors.lime)),
                    Text(_rupiah(st.cartTotal),
                        style: display(
                            fontSize: 18, color: Colors.white, letterSpacing: -0.3)),
                  ],
                ),
              ),
              ElevatedButton(
                key: const Key('public_order_checkout'),
                onPressed: () => _openCheckout(ctrl),
                child: const Text('Pesan'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // ── Sheet checkout: nama + no HP ──
  void _openCheckout(PublicOrderController ctrl) {
    final nameC = TextEditingController();
    final phoneC = TextEditingController();
    final formKey = GlobalKey<FormState>();
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: FortunasColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(FortunasRadius.xl)),
      ),
      builder: (sheetCtx) {
        return Padding(
          padding: EdgeInsets.only(
            left: 18, right: 18, top: 18,
            bottom: MediaQuery.of(sheetCtx).viewInsets.bottom + 18,
          ),
          child: Form(
            key: formKey,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text('Data pemesan',
                    style: display(fontSize: 18, letterSpacing: -0.3)),
                const SizedBox(height: 12),
                TextFormField(
                  key: const Key('checkout_name'),
                  controller: nameC,
                  textCapitalization: TextCapitalization.words,
                  decoration: const InputDecoration(labelText: 'Nama'),
                  validator: (v) =>
                      (v == null || v.trim().isEmpty) ? 'Nama wajib diisi' : null,
                ),
                const SizedBox(height: 10),
                TextFormField(
                  key: const Key('checkout_phone'),
                  controller: phoneC,
                  keyboardType: TextInputType.phone,
                  decoration:
                      const InputDecoration(labelText: 'No. HP (WhatsApp)'),
                  validator: (v) =>
                      (v == null || v.trim().isEmpty) ? 'No. HP wajib diisi' : null,
                ),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: () async {
                    if (!formKey.currentState!.validate()) return;
                    Navigator.of(sheetCtx).pop();
                    await ctrl.createOrder(
                      customerName: nameC.text,
                      customerPhone: phoneC.text,
                    );
                  },
                  child: const Text('Buat pesanan & bayar'),
                ),
              ],
            ),
          ),
        );
      },
    ).whenComplete(() {
      nameC.dispose();
      phoneC.dispose();
    });
  }

  // ── Fase 3: pesanan dibuat → bayar (simulasi) + status ──
  Widget _buildOrder(PublicOrderState st, PublicOrderController ctrl) {
    final o = st.order;
    if (o == null) return const SizedBox.shrink();
    final (statusLabel, statusColor) = _statusView(o.status);
    final pending = o.status == 'pending_payment';

    return ListView(
      padding: const EdgeInsets.fromLTRB(18, 8, 18, 30),
      children: [
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: FortunasColors.surface,
            border: Border.all(color: FortunasColors.ink, width: 1.5),
            borderRadius: BorderRadius.circular(FortunasRadius.lg),
            boxShadow: popShadow(offset: 2),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(children: [
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: statusColor,
                    borderRadius: BorderRadius.circular(999),
                    border: Border.all(color: FortunasColors.ink, width: 1),
                  ),
                  child: Text(statusLabel,
                      style: mono(fontSize: 10, color: FortunasColors.ink)),
                ),
                const Spacer(),
                Text('#${o.id}',
                    style: mono(fontSize: 11, color: FortunasColors.ink3)),
              ]),
              const SizedBox(height: 12),
              ...o.items.map((it) => Padding(
                    padding: const EdgeInsets.only(bottom: 6),
                    child: Row(children: [
                      Text('${it.qty}×',
                          style: mono(fontSize: 12, color: FortunasColors.ink3)),
                      const SizedBox(width: 8),
                      Expanded(
                          child: Text(it.name,
                              style: body(
                                  fontSize: 13.5, color: FortunasColors.ink))),
                      Text(_rupiah(it.subtotal),
                          style: body(
                              fontSize: 13, color: FortunasColors.ink2)),
                    ]),
                  )),
              const Divider(height: 18),
              Row(children: [
                Text('Total', style: body(fontSize: 14, weight: FontWeight.w700)),
                const Spacer(),
                Text(_rupiah(o.total),
                    style:
                        display(fontSize: 18, letterSpacing: -0.3)),
              ]),
            ],
          ),
        ),
        if (st.errorMessage != null) _errorText(st.errorMessage!),
        const SizedBox(height: 16),

        // Pembayaran — QRIS statis (Midtrans = future scope).
        if (pending) ...[
          _qrisPayment(o, st, ctrl),
        ] else ...[
          OutlinedButton.icon(
            onPressed: st.polling ? null : ctrl.refreshStatus,
            icon: st.polling
                ? _spinner(color: FortunasColors.ink)
                : const Icon(Icons.refresh, size: 18),
            label: const Text('Perbarui status'),
          ),
        ],

        const SizedBox(height: 10),
        TextButton(
          onPressed: () {
            ctrl.backToMenu();
          },
          child: const Text('Pesan lagi di toko ini'),
        ),
      ],
    );
  }

  // Blok pembayaran QRIS statis: tampilkan qr.jpeg + total + tombol konfirmasi.
  // Pelanggan scan QR, bayar lewat bank/e-wallet, lalu tekan "Saya sudah bayar".
  Widget _qrisPayment(
      PublicOrder o, PublicOrderState st, PublicOrderController ctrl) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: FortunasColors.surface,
            border: Border.all(color: FortunasColors.ink, width: 1.5),
            borderRadius: BorderRadius.circular(FortunasRadius.lg),
            boxShadow: popShadow(offset: 2),
          ),
          child: Column(children: [
            Text('Scan QRIS untuk bayar',
                style: body(fontSize: 13, weight: FontWeight.w700,
                    color: FortunasColors.ink)),
            const SizedBox(height: 4),
            Text('Total: ${_rupiah(o.total)}',
                style: display(fontSize: 20, letterSpacing: -0.3)),
            const SizedBox(height: 12),
            AspectRatio(
              aspectRatio: 1,
              child: ClipRRect(
                borderRadius: BorderRadius.circular(FortunasRadius.md),
                child: Image.asset(
                  'assets/payments/qr.jpeg',
                  fit: BoxFit.contain,
                  errorBuilder: (_, __, ___) => Container(
                    color: FortunasColors.surfaceSoft,
                    alignment: Alignment.center,
                    padding: const EdgeInsets.all(16),
                    child: Text(
                      'QR belum dipasang.\nTaruh assets/payments/qr.jpeg',
                      textAlign: TextAlign.center,
                      style: body(fontSize: 12, color: FortunasColors.ink4),
                    ),
                  ),
                ),
              ),
            ),
          ]),
        ),
        const SizedBox(height: 10),
        ElevatedButton(
          key: const Key('public_order_confirm_pay'),
          onPressed: st.loading ? null : ctrl.confirmPayment,
          child: st.loading ? _spinner() : const Text('Saya sudah bayar'),
        ),
        const SizedBox(height: 6),
        Text(
          'Scan QRIS di atas, bayar sesuai total, lalu tekan tombol ini. '
          'Penjual akan memverifikasi pembayaran sebelum memproses pesanan.',
          style: body(fontSize: 12, color: FortunasColors.ink3),
        ),
      ],
    );
  }

  // ── util UI ──
  (String, Color) _statusView(String status) => switch (status) {
        'pending_payment' => ('Menunggu bayar', FortunasColors.warning),
        'paid' => ('Sudah dibayar', FortunasColors.sky),
        'accepted' => ('Diterima toko', FortunasColors.lime),
        'completed' => ('Selesai', FortunasColors.success),
        'rejected' => ('Ditolak', FortunasColors.peach),
        'expired' => ('Kedaluwarsa', FortunasColors.surfaceHover),
        'cancelled' => ('Dibatalkan', FortunasColors.peach),
        _ => (status, FortunasColors.surfaceSoft),
      };

  Widget _errorText(String msg) => Padding(
        padding: const EdgeInsets.only(top: 8),
        child: Text(msg, style: body(fontSize: 12.5, color: FortunasColors.error)),
      );

  Widget _spinner({Color color = Colors.white}) => SizedBox(
        height: 18,
        width: 18,
        child: CircularProgressIndicator(strokeWidth: 2, color: color),
      );
}

/// Kartu produk di grid menu: gambar, nama, harga, dan stepper qty.
class _MenuCard extends StatelessWidget {
  final PublicMenuProduct product;
  final int qty;
  final VoidCallback onAdd;
  final VoidCallback onRemove;

  const _MenuCard({
    required this.product,
    required this.qty,
    required this.onAdd,
    required this.onRemove,
  });

  @override
  Widget build(BuildContext context) {
    final imgUrl = product.imageUrl.isEmpty ? null : '$_apiBase${product.imageUrl}';
    final disabled = !product.orderable;
    return Container(
      decoration: BoxDecoration(
        color: FortunasColors.surface,
        border: Border.all(color: FortunasColors.ink, width: 1.5),
        borderRadius: BorderRadius.circular(FortunasRadius.lg),
        boxShadow: popShadow(offset: 2),
      ),
      clipBehavior: Clip.antiAlias,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          AspectRatio(
            aspectRatio: 1.2,
            child: Container(
              color: FortunasColors.surfaceSoft,
              child: imgUrl == null
                  ? const Icon(Icons.image_not_supported,
                      color: FortunasColors.ink4)
                  : Image.network(imgUrl, fit: BoxFit.cover,
                      errorBuilder: (_, __, ___) => const Icon(
                          Icons.broken_image, color: FortunasColors.ink4)),
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(10, 8, 10, 10),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(product.name,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: body(
                        fontSize: 13, weight: FontWeight.w700,
                        color: FortunasColors.ink)),
                const SizedBox(height: 4),
                Text(
                  product.price == null ? 'Belum ada harga' : _rupiah(product.price!),
                  style: body(
                      fontSize: 12.5,
                      color: product.price == null
                          ? FortunasColors.ink4
                          : FortunasColors.ink2),
                ),
                if (product.stock == 0)
                  Padding(
                    padding: const EdgeInsets.only(top: 2),
                    child: Text('Habis',
                        style: mono(fontSize: 10, color: FortunasColors.error)),
                  ),
                const SizedBox(height: 8),
                if (disabled)
                  SizedBox(
                    height: 34,
                    child: OutlinedButton(
                      onPressed: null,
                      child: Text(product.price == null ? 'Belum dijual' : 'Habis'),
                    ),
                  )
                else if (qty == 0)
                  SizedBox(
                    height: 34,
                    child: ElevatedButton(
                      onPressed: onAdd,
                      style: ElevatedButton.styleFrom(
                          padding: EdgeInsets.zero,
                          textStyle: body(fontSize: 13, weight: FontWeight.w700)),
                      child: const Text('Tambah'),
                    ),
                  )
                else
                  _Stepper(qty: qty, onAdd: onAdd, onRemove: onRemove),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _Stepper extends StatelessWidget {
  final int qty;
  final VoidCallback onAdd;
  final VoidCallback onRemove;
  const _Stepper({required this.qty, required this.onAdd, required this.onRemove});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 34,
      decoration: BoxDecoration(
        color: FortunasColors.surfaceSoft,
        border: Border.all(color: FortunasColors.ink, width: 1.2),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          _stepBtn(Icons.remove, onRemove),
          Text('$qty',
              style: body(fontSize: 14, weight: FontWeight.w700,
                  color: FortunasColors.ink)),
          _stepBtn(Icons.add, onAdd),
        ],
      ),
    );
  }

  Widget _stepBtn(IconData icon, VoidCallback onTap) => InkWell(
        onTap: onTap,
        customBorder: const CircleBorder(),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8),
          child: Icon(icon, size: 18, color: FortunasColors.ink),
        ),
      );
}
