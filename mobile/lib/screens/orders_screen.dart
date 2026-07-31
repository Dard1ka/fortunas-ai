import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../api/models.dart';
import '../orders/order_controller.dart';
import '../theme/tokens.dart';
import '../ui/screen_header.dart';

/// Inbox pesanan online untuk UMKM. Tanpa notifikasi push (butuh Firebase,
/// ditunda) → penyegaran lewat tarik-untuk-refresh + muat saat layar dibuka.
class OrdersScreen extends ConsumerStatefulWidget {
  const OrdersScreen({super.key});

  @override
  ConsumerState<OrdersScreen> createState() => _OrdersScreenState();
}

class _OrdersScreenState extends ConsumerState<OrdersScreen> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() => ref.read(orderControllerProvider.notifier).load());
  }

  String _rupiah(int v) {
    final s = v.toString();
    final buf = StringBuffer();
    for (var i = 0; i < s.length; i++) {
      if (i > 0 && (s.length - i) % 3 == 0) buf.write('.');
      buf.write(s[i]);
    }
    return 'Rp$buf';
  }

  void _toast(String msg) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(msg)));
  }

  Future<void> _confirmReject(UmkmOrder o) async {
    final yes = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Tolak pesanan?'),
        // Wajib disebut: stok kembali otomatis, uang TIDAK. Menolak pesanan yang
        // sudah dibayar tanpa memberi tahu ini memancing sengketa dengan pelanggan.
        content: Text(
          'Stok ${o.items.length} item akan dikembalikan otomatis. '
          'Pengembalian uang ke pelanggan harus kamu lakukan manual.',
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.of(ctx).pop(false),
              child: const Text('Batal')),
          FilledButton(
              onPressed: () => Navigator.of(ctx).pop(true),
              child: const Text('Tolak Pesanan')),
        ],
      ),
    );
    if (yes != true) return;
    final ok = await ref.read(orderControllerProvider.notifier).reject(o.id);
    _toast(ok ? 'Pesanan ditolak, stok dikembalikan.' : 'Gagal menolak pesanan.');
  }

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(orderControllerProvider);
    return Scaffold(
      backgroundColor: FortunasColors.bg,
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: () => ref.read(orderControllerProvider.notifier).load(),
          child: ListView(
            padding: const EdgeInsets.only(bottom: 24),
            children: [
              const ScreenHeader(subtitle: 'Pesanan Masuk'),
              // Konvensi rumah: SETIAP layar push punya tombol kembali dalam-app
              // (`ScreenHeader` tak menyediakannya, dan `PhoneFrame` di web/desktop
              // tak punya tombol back sistem). Pola & penamaan Key mengikuti
              // products_back / checkout_back / dpa_back / scan_back.
              Align(
                alignment: Alignment.centerLeft,
                child: TextButton.icon(
                  key: const Key('orders_back'),
                  onPressed: () => context.pop(),
                  icon: const Icon(Icons.arrow_back, size: 18),
                  style: TextButton.styleFrom(
                    foregroundColor: FortunasColors.ink,
                    padding: const EdgeInsets.symmetric(horizontal: 4),
                  ),
                  label: const Text('Kembali'),
                ),
              ),
              if (s.errorMessage != null)
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 18),
                  child: Text(s.errorMessage!,
                      style: const TextStyle(color: FortunasColors.peach)),
                ),
              if (s.loading && s.orders.isEmpty)
                const Padding(
                  padding: EdgeInsets.all(32),
                  child: Center(child: CircularProgressIndicator()),
                )
              else if (s.orders.isEmpty)
                Padding(
                  key: const Key('orders_empty'),
                  padding: const EdgeInsets.all(28),
                  child: Column(
                    children: const [
                      Icon(Icons.inbox_outlined, size: 40),
                      SizedBox(height: 10),
                      Text('Belum ada pesanan masuk.',
                          textAlign: TextAlign.center),
                      SizedBox(height: 4),
                      Text('Bagikan kode tokomu ke pelanggan untuk mulai menerima pesanan.',
                          textAlign: TextAlign.center),
                    ],
                  ),
                )
              else
                ...s.orders.map(_card),
            ],
          ),
        ),
      ),
    );
  }

  Widget _card(UmkmOrder o) {
    final busy = ref.watch(orderControllerProvider).submittingId == o.id;
    return Container(
      margin: const EdgeInsets.fromLTRB(18, 0, 18, 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: FortunasColors.surface,
        border: Border.all(color: FortunasColors.borderSoft),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(o.customerName.isEmpty ? 'Pelanggan' : o.customerName,
                  style: const TextStyle(fontWeight: FontWeight.bold)),
              Text(o.status),
            ],
          ),
          // Backend membekukan `status` di `accepted` kalau refund datang setelah
          // UMKM menerima — supaya keputusannya tak terhapus diam-diam. Tanpa
          // peringatan ini, UMKM menyiapkan pesanan yang uangnya sudah kembali
          // ke pelanggan.
          if (o.isRefunded)
            Padding(
              key: Key('orders_refunded_${o.id}'),
              padding: const EdgeInsets.only(top: 4),
              child: Text('⚠ Dana sudah dikembalikan ke pelanggan (${o.paymentStatus})',
                  style: const TextStyle(color: FortunasColors.peach)),
            ),
          const SizedBox(height: 6),
          ...o.items.map((it) => Text('${it.qty}× ${it.name}  ${_rupiah(it.subtotal)}')),
          const SizedBox(height: 6),
          Text('Total ${_rupiah(o.total)}',
              style: const TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 10),
          Row(children: _actions(o, busy)),
        ],
      ),
    );
  }

  List<Widget> _actions(UmkmOrder o, bool busy) {
    if (o.status == 'paid') {
      return [
        FilledButton(
          key: Key('orders_accept_${o.id}'),
          onPressed: busy
              ? null
              : () async {
                  final ok =
                      await ref.read(orderControllerProvider.notifier).accept(o.id);
                  _toast(ok ? 'Pesanan diterima.' : 'Gagal menerima pesanan.');
                },
          child: const Text('Terima'),
        ),
        const SizedBox(width: 8),
        OutlinedButton(
          key: Key('orders_reject_${o.id}'),
          onPressed: busy ? null : () => _confirmReject(o),
          child: const Text('Tolak'),
        ),
      ];
    }
    if (o.status == 'accepted') {
      return [
        FilledButton(
          key: Key('orders_complete_${o.id}'),
          onPressed: busy
              ? null
              : () async {
                  final ok = await ref
                      .read(orderControllerProvider.notifier)
                      .complete(o.id);
                  _toast(ok ? 'Pesanan selesai.' : 'Gagal menyelesaikan pesanan.');
                },
          child: const Text('Selesai'),
        ),
      ];
    }
    return const [];
  }
}
