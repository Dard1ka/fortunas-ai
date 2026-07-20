import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/client.dart';
import '../api/errors.dart';
import '../api/models.dart';
import '../theme/tokens.dart';
import '../ui/screen_header.dart';

/// Customer transaction history (REQUIREMENTS §6.7): riwayat lintas UMKM dari BigQuery.
final _customerTxProvider = FutureProvider.autoDispose<CustomerTransactionsResponse>((ref) {
  return ref.read(apiProvider).customerTransactions();
});

class CustomerHistoryScreen extends ConsumerWidget {
  const CustomerHistoryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(_customerTxProvider);
    return RefreshIndicator(
      onRefresh: () async => ref.invalidate(_customerTxProvider),
      child: ListView(
        padding: const EdgeInsets.fromLTRB(18, 8, 18, 120),
        children: [
          const ScreenHeader(subtitle: 'Riwayat'),
          const SizedBox(height: 8),
          Text('Riwayat Transaksi', style: display(fontSize: 22, letterSpacing: -0.4)),
          const SizedBox(height: 12),
          async.when(
            loading: () => const Padding(
                padding: EdgeInsets.symmetric(vertical: 48),
                child: Center(child: CircularProgressIndicator())),
            error: (e, _) => Text(humanizeError(e),
                style: body(fontSize: 12.5, color: FortunasColors.error)),
            data: (resp) {
              if (resp.transactions.isEmpty) {
                return Text(
                    resp.message.isNotEmpty
                        ? resp.message
                        : 'Belum ada transaksi.',
                    style: body(fontSize: 12.5, color: FortunasColors.ink3));
              }
              return Column(children: resp.transactions.map(_txTile).toList());
            },
          ),
        ],
      ),
    );
  }

  Widget _txTile(Map<String, dynamic> tx) {
    final desc = tx['Description']?.toString() ?? 'Transaksi';
    final qty = tx['Quantity']?.toString() ?? '';
    final price = tx['Price']?.toString() ?? '';
    final date = (tx['InvoiceDate']?.toString() ?? '').split('T').first;
    final tenant = tx['tenant_name']?.toString() ?? '';
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
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(desc,
                style: body(fontSize: 13, weight: FontWeight.w600, color: FortunasColors.ink)),
            Text([
              if (tenant.isNotEmpty) tenant,
              if (qty.isNotEmpty) 'x$qty',
              if (date.isNotEmpty) date,
            ].join(' · '), style: body(fontSize: 11, color: FortunasColors.ink3)),
          ]),
        ),
        if (price.isNotEmpty)
          Text('Rp$price', style: display(fontSize: 14, color: FortunasColors.ink)),
      ]),
    );
  }
}
