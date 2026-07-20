import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../api/models.dart';
import '../customer/customer_loyalty_controllers.dart';
import '../theme/tokens.dart';
import '../ui/screen_header.dart';

/// Customer Home (REQUIREMENTS §6.2): daftar UMKM dikunjungi, total poin,
/// transaksi terakhir, promo terakhir.
class CustomerHomeScreen extends ConsumerStatefulWidget {
  const CustomerHomeScreen({super.key});
  @override
  ConsumerState<CustomerHomeScreen> createState() => _CustomerHomeScreenState();
}

class _CustomerHomeScreenState extends ConsumerState<CustomerHomeScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback(
        (_) => ref.read(customerHomeControllerProvider.notifier).load());
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(customerHomeControllerProvider);
    final home = state.home;
    return RefreshIndicator(
      onRefresh: () => ref.read(customerHomeControllerProvider.notifier).load(),
      child: ListView(
        padding: const EdgeInsets.fromLTRB(18, 8, 18, 120),
        children: [
          const ScreenHeader(subtitle: 'Pelanggan'),
          const SizedBox(height: 8),
          Text('Halo, ${home?.username ?? '...'} 👋',
              style: display(fontSize: 22, letterSpacing: -0.4)),
          const SizedBox(height: 4),
          Text('Kumpulkan poin, tukar jadi promo.',
              style: body(fontSize: 12.5, color: FortunasColors.ink3)),
          const SizedBox(height: 16),
          if (state.loading && home == null)
            const Padding(
                padding: EdgeInsets.symmetric(vertical: 48),
                child: Center(child: CircularProgressIndicator()))
          else if (state.errorMessage != null && home == null)
            _errorBox(state.errorMessage!)
          else if (home != null) ...[
            _pointsCard(context, home.totalPoints),
            const SizedBox(height: 14),
            if (home.lastPromo != null) ...[
              _sectionLabel('PROMO TERAKHIR'),
              const SizedBox(height: 8),
              _PromoTile(promo: home.lastPromo!),
              const SizedBox(height: 14),
            ],
            _sectionLabel('UMKM YANG KAMU KUNJUNGI'),
            const SizedBox(height: 8),
            if (home.memberships.isEmpty)
              _emptyBox('Belum ada UMKM. Scan QR-mu di kasir untuk mulai.')
            else
              ...home.memberships.map((m) => _MembershipTile(
                    membership: m,
                    onGeneratePromo: () =>
                        context.push('/customer/promo', extra: m),
                  )),
            if (home.lastTransaction != null) ...[
              const SizedBox(height: 14),
              _sectionLabel('TRANSAKSI TERAKHIR'),
              const SizedBox(height: 8),
              _lastTxTile(home.lastTransaction!),
            ],
          ],
        ],
      ),
    );
  }

  Widget _pointsCard(BuildContext context, int points) => Container(
        width: double.infinity,
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: FortunasColors.violet,
          border: Border.all(color: FortunasColors.ink, width: 1.5),
          borderRadius: BorderRadius.circular(FortunasRadius.xl),
          boxShadow: popShadow(),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('TOTAL POIN', style: mono(fontSize: 10, color: Colors.white70)),
            const SizedBox(height: 6),
            Text('$points',
                style: display(fontSize: 44, color: Colors.white, letterSpacing: -1)),
            const SizedBox(height: 4),
            Text('Poin universal — berlaku di semua UMKM tempat kamu transaksi.',
                style: body(fontSize: 11.5, color: Colors.white70)),
          ],
        ),
      );

  Widget _lastTxTile(Map<String, dynamic> tx) {
    final desc = tx['Description']?.toString() ?? tx['description']?.toString() ?? 'Transaksi';
    final date = tx['InvoiceDate']?.toString() ?? '';
    final tenant = tx['tenant_name']?.toString() ?? '';
    return _card(Row(children: [
      const Icon(Icons.receipt_long, size: 20, color: FortunasColors.ink3),
      const SizedBox(width: 10),
      Expanded(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(desc, style: body(fontSize: 13, weight: FontWeight.w600, color: FortunasColors.ink)),
          if (tenant.isNotEmpty || date.isNotEmpty)
            Text([tenant, date.split('T').first].where((s) => s.isNotEmpty).join(' · '),
                style: body(fontSize: 11, color: FortunasColors.ink3)),
        ]),
      ),
    ]));
  }

  Widget _sectionLabel(String s) => Text(s, style: mono(fontSize: 10, color: FortunasColors.ink3));
  Widget _card(Widget child) => Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: FortunasColors.surface,
          border: Border.all(color: FortunasColors.ink, width: 1.5),
          borderRadius: BorderRadius.circular(FortunasRadius.lg),
          boxShadow: popShadow(offset: 2),
        ),
        child: child,
      );
  Widget _emptyBox(String s) => _card(Text(s,
      style: body(fontSize: 12.5, color: FortunasColors.ink3)));
  Widget _errorBox(String s) => Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: FortunasColors.peachSoft,
          border: Border.all(color: FortunasColors.ink, width: 1.5),
          borderRadius: BorderRadius.circular(FortunasRadius.lg),
        ),
        child: Text(s, style: body(fontSize: 12.5, color: FortunasColors.ink)),
      );
}

class _MembershipTile extends StatelessWidget {
  final MembershipSummary membership;
  final VoidCallback onGeneratePromo;
  const _MembershipTile({required this.membership, required this.onGeneratePromo});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: FortunasColors.surface,
        border: Border.all(color: FortunasColors.ink, width: 1.5),
        borderRadius: BorderRadius.circular(FortunasRadius.lg),
        boxShadow: popShadow(offset: 2),
      ),
      child: Row(children: [
        Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: FortunasColors.limeDeep,
            border: Border.all(color: FortunasColors.ink, width: 1.5),
            borderRadius: BorderRadius.circular(12),
          ),
          child: const Icon(Icons.storefront, size: 20, color: FortunasColors.ink),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(membership.tenantName,
                style: body(fontSize: 14, weight: FontWeight.w700, color: FortunasColors.ink)),
            if (membership.memberSince != null)
              Text('Member sejak ${membership.memberSince}',
                  style: body(fontSize: 11, color: FortunasColors.ink3)),
          ]),
        ),
        TextButton(
          onPressed: onGeneratePromo,
          style: TextButton.styleFrom(
            foregroundColor: FortunasColors.violet,
            padding: const EdgeInsets.symmetric(horizontal: 8),
          ),
          child: Text('Buat Promo',
              style: body(fontSize: 12, weight: FontWeight.w700, color: FortunasColors.violet)),
        ),
      ]),
    );
  }
}

class _PromoTile extends StatelessWidget {
  final PromoInstance promo;
  const _PromoTile({required this.promo});

  @override
  Widget build(BuildContext context) {
    final redeemed = promo.status == 'redeemed';
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: redeemed ? FortunasColors.surfaceSoft : FortunasColors.peachSoft,
        border: Border.all(color: FortunasColors.ink, width: 1.5),
        borderRadius: BorderRadius.circular(FortunasRadius.lg),
        boxShadow: popShadow(offset: 2),
      ),
      child: Row(children: [
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(promo.name,
                style: body(fontSize: 13.5, weight: FontWeight.w700, color: FortunasColors.ink)),
            const SizedBox(height: 2),
            Text('Kode ${promo.code} · ${promo.status}',
                style: mono(fontSize: 10, color: FortunasColors.ink3)),
          ]),
        ),
        Text('Rp${promo.discountAmount}',
            style: display(fontSize: 16, color: FortunasColors.ink)),
      ]),
    );
  }
}
