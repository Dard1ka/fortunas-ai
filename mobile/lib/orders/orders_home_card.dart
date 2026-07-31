import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../theme/tokens.dart';
import '../ui/quick_action_card.dart';
import 'order_controller.dart';

/// Pintu masuk inbox pesanan dari layar home, dengan badge jumlah pesanan yang
/// menunggu diterima. Badge-nya bukan hiasan: tanpa notifikasi push (butuh
/// Firebase, ditunda) ini satu-satunya cara UMKM tahu ada pesanan masuk tanpa
/// membuka layarnya.
class OrdersHomeCard extends ConsumerWidget {
  const OrdersHomeCard({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final n = ref.watch(pendingOrderCountProvider).valueOrNull ?? 0;
    return QuickActionCard(
      key: const Key('home_orders'),
      title: 'Pesanan Masuk',
      subtitle: n == 0
          ? 'Pesanan online dari pelanggan'
          : '$n pesanan menunggu diterima',
      icon: Icons.receipt_long,
      iconBg: FortunasColors.peach,
      onTap: () => context.push('/orders'),
    );
  }
}
