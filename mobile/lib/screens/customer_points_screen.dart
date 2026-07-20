import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/models.dart';
import '../customer/customer_loyalty_controllers.dart';
import '../theme/tokens.dart';
import '../ui/screen_header.dart';

/// Customer Points (REQUIREMENTS §6.4): saldo + riwayat ledger poin.
class CustomerPointsScreen extends ConsumerStatefulWidget {
  const CustomerPointsScreen({super.key});
  @override
  ConsumerState<CustomerPointsScreen> createState() => _CustomerPointsScreenState();
}

class _CustomerPointsScreenState extends ConsumerState<CustomerPointsScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback(
        (_) => ref.read(customerPointsControllerProvider.notifier).load());
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(customerPointsControllerProvider);
    final p = state.points;
    return RefreshIndicator(
      onRefresh: () => ref.read(customerPointsControllerProvider.notifier).load(),
      child: ListView(
        padding: const EdgeInsets.fromLTRB(18, 8, 18, 120),
        children: [
          const ScreenHeader(subtitle: 'Poin Saya'),
          const SizedBox(height: 8),
          Text('Poin Saya', style: display(fontSize: 22, letterSpacing: -0.4)),
          const SizedBox(height: 12),
          if (state.loading && p == null)
            const Padding(
                padding: EdgeInsets.symmetric(vertical: 48),
                child: Center(child: CircularProgressIndicator()))
          else if (p != null) ...[
            _balanceCard(p.balance),
            const SizedBox(height: 16),
            Text('RIWAYAT POIN', style: mono(fontSize: 10, color: FortunasColors.ink3)),
            const SizedBox(height: 8),
            if (p.recent.isEmpty)
              Text('Belum ada aktivitas poin.',
                  style: body(fontSize: 12.5, color: FortunasColors.ink3))
            else
              ...p.recent.map(_ledgerTile),
          ] else if (state.errorMessage != null)
            Text(state.errorMessage!,
                style: body(fontSize: 12.5, color: FortunasColors.error)),
        ],
      ),
    );
  }

  Widget _balanceCard(int balance) => Container(
        width: double.infinity,
        padding: const EdgeInsets.all(22),
        decoration: BoxDecoration(
          color: FortunasColors.lime,
          border: Border.all(color: FortunasColors.ink, width: 1.5),
          borderRadius: BorderRadius.circular(FortunasRadius.xl),
          boxShadow: popShadow(),
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('SALDO POIN', style: mono(fontSize: 10, color: FortunasColors.ink2)),
          const SizedBox(height: 6),
          Row(crossAxisAlignment: CrossAxisAlignment.baseline,
              textBaseline: TextBaseline.alphabetic, children: [
            Text('$balance', style: display(fontSize: 48, letterSpacing: -1)),
            const SizedBox(width: 8),
            Text('poin', style: body(fontSize: 16, color: FortunasColors.ink2)),
          ]),
        ]),
      );

  Widget _ledgerTile(PointsLedgerEntry e) {
    final earn = e.pointsDelta >= 0;
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: FortunasColors.surface,
        border: Border.all(color: FortunasColors.ink, width: 1.5),
        borderRadius: BorderRadius.circular(FortunasRadius.md),
        boxShadow: popShadow(offset: 2),
      ),
      child: Row(children: [
        Container(
          width: 34,
          height: 34,
          decoration: BoxDecoration(
            color: earn ? FortunasColors.limeDeep : FortunasColors.peach,
            border: Border.all(color: FortunasColors.ink, width: 1.5),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Icon(earn ? Icons.add : Icons.remove, size: 18, color: FortunasColors.ink),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(_label(e.eventType),
                style: body(fontSize: 13, weight: FontWeight.w600, color: FortunasColors.ink)),
            Text([
              if (e.invoice != null) 'Invoice ${e.invoice}',
              if (e.createdAt.isNotEmpty) e.createdAt.split('T').first,
            ].join(' · '), style: body(fontSize: 11, color: FortunasColors.ink3)),
          ]),
        ),
        Text('${earn ? '+' : ''}${e.pointsDelta}',
            style: display(
                fontSize: 18,
                color: earn ? FortunasColors.success : FortunasColors.error)),
      ]),
    );
  }

  String _label(String eventType) {
    switch (eventType) {
      case 'earn':
        return 'Poin dari transaksi';
      case 'redeem':
        return 'Tukar untuk promo';
      case 'expire':
        return 'Poin kedaluwarsa';
      default:
        return 'Penyesuaian';
    }
  }
}
