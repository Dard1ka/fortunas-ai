import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:qr_flutter/qr_flutter.dart';

import '../customer/customer_qr_controller.dart';
import '../customer/customer_qr_state.dart';
import '../theme/tokens.dart';
import '../ui/screen_header.dart';

/// Customer QR identity screen. Fetches a short-lived (TTL 90s) signed QR token
/// and renders it; the controller auto-refreshes before expiry so the QR shown
/// to a cashier is always valid. Scanner side (UMKM) is deferred.
class CustomerQrScreen extends ConsumerStatefulWidget {
  const CustomerQrScreen({super.key});
  @override
  ConsumerState<CustomerQrScreen> createState() => _CustomerQrScreenState();
}

class _CustomerQrScreenState extends ConsumerState<CustomerQrScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(customerQrControllerProvider.notifier).refresh();
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(customerQrControllerProvider);
    return Scaffold(
      backgroundColor: FortunasColors.bg,
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(18, 8, 18, 24),
          children: [
            const ScreenHeader(subtitle: 'QR Saya'),
            const SizedBox(height: 8),
            Text('QR Identitas', style: display(fontSize: 22, letterSpacing: -0.4)),
            const SizedBox(height: 4),
            Text('Tunjukkan ke kasir · QR diperbarui otomatis.',
                style: body(fontSize: 12.5, color: FortunasColors.ink3)),
            const SizedBox(height: 18),
            _content(state),
            const SizedBox(height: 18),
            ElevatedButton(
              key: const Key('cust_qr_refresh'),
              onPressed: state.loading ? null : () => ref.read(customerQrControllerProvider.notifier).refresh(),
              child: Text(state.loading ? 'Memuat…' : 'Perbarui'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _content(CustomerQrState state) {
    if (state.hasQr) {
      return Center(
        child: Container(
          key: const Key('cust_qr_image'),
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
          ),
          child: QrImageView(
            data: state.session!.qrToken,
            version: QrVersions.auto,
            size: 220,
            backgroundColor: Colors.white,
          ),
        ),
      );
    }
    if (state.errorMessage != null) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 24),
        child: Text(state.errorMessage!,
            key: const Key('cust_qr_error'),
            textAlign: TextAlign.center,
            style: body(fontSize: 13, color: FortunasColors.error)),
      );
    }
    return const Padding(
      padding: EdgeInsets.symmetric(vertical: 48),
      child: Center(child: CircularProgressIndicator()),
    );
  }
}
