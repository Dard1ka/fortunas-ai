import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../customer/customer_auth_controller.dart';
import '../theme/tokens.dart';
import '../ui/screen_header.dart';

/// Customer profile/menu (REQUIREMENTS §6.1 "Profile"): info akun + logout.
class CustomerMenuScreen extends ConsumerWidget {
  const CustomerMenuScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final profile = ref.watch(customerAuthControllerProvider).profile;
    return ListView(
      padding: const EdgeInsets.fromLTRB(18, 8, 18, 120),
      children: [
        const ScreenHeader(subtitle: 'Profil'),
        const SizedBox(height: 8),
        Text('Profil Saya', style: display(fontSize: 22, letterSpacing: -0.4)),
        const SizedBox(height: 16),
        Container(
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            color: FortunasColors.surface,
            border: Border.all(color: FortunasColors.ink, width: 1.5),
            borderRadius: BorderRadius.circular(FortunasRadius.xl),
            boxShadow: popShadow(),
          ),
          child: Row(children: [
            Container(
              width: 52,
              height: 52,
              decoration: BoxDecoration(
                color: FortunasColors.violetSoft,
                shape: BoxShape.circle,
                border: Border.all(color: FortunasColors.ink, width: 1.5),
              ),
              child: const Icon(Icons.person, color: FortunasColors.violet),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(profile?.username ?? 'Pelanggan',
                    style: display(fontSize: 18, letterSpacing: -0.3)),
                if (profile?.phoneNumber.isNotEmpty ?? false)
                  Text(profile!.phoneNumber,
                      style: body(fontSize: 12.5, color: FortunasColors.ink3)),
              ]),
            ),
          ]),
        ),
        const SizedBox(height: 20),
        _menuTile(Icons.qr_code_2, 'QR Identitas Saya',
            () => context.go('/customer/qr')),
        _menuTile(Icons.card_giftcard, 'Poin & Promo',
            () => context.go('/customer/points')),
        const SizedBox(height: 20),
        OutlinedButton.icon(
          onPressed: () {
            ref.read(customerAuthControllerProvider.notifier).logout();
            context.go('/login');
          },
          icon: const Icon(Icons.logout, size: 18),
          style: OutlinedButton.styleFrom(
            foregroundColor: FortunasColors.error,
            minimumSize: const Size.fromHeight(50),
            side: const BorderSide(color: FortunasColors.ink, width: 1.5),
            shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(FortunasRadius.lg)),
          ),
          label: Text('Keluar',
              style: body(fontSize: 14, weight: FontWeight.w700, color: FortunasColors.error)),
        ),
      ],
    );
  }

  Widget _menuTile(IconData icon, String label, VoidCallback onTap) => Container(
        margin: const EdgeInsets.only(bottom: 8),
        decoration: BoxDecoration(
          color: FortunasColors.surface,
          border: Border.all(color: FortunasColors.ink, width: 1.5),
          borderRadius: BorderRadius.circular(FortunasRadius.lg),
          boxShadow: popShadow(offset: 2),
        ),
        child: ListTile(
          leading: Icon(icon, color: FortunasColors.ink),
          title: Text(label,
              style: body(fontSize: 14, weight: FontWeight.w600, color: FortunasColors.ink)),
          trailing: const Icon(Icons.chevron_right, color: FortunasColors.ink3),
          onTap: onTap,
        ),
      );
}
