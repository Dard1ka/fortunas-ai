import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/models.dart';
import '../scan/scan_controller.dart';
import '../scan/scan_rules.dart';
import '../scan/scan_state.dart';
import '../theme/tokens.dart';
import '../ui/screen_header.dart';

/// UMKM scans a customer's QR identity token to auto-register membership.
/// DEV MODE — token entered manually (paste). Real camera (mobile_scanner) is a
/// deferred seam: swap the TextField for a MobileScanner widget that feeds the
/// detected token into controller.validate() (see PENDING_EXTERNAL_SETUP.md).
class ScanScreen extends ConsumerStatefulWidget {
  const ScanScreen({super.key});
  @override
  ConsumerState<ScanScreen> createState() => _ScanScreenState();
}

class _ScanScreenState extends ConsumerState<ScanScreen> {
  final _token = TextEditingController();

  @override
  void dispose() {
    _token.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(scanControllerProvider);
    return Scaffold(
      backgroundColor: FortunasColors.bg,
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(18, 8, 18, 24),
          children: [
            const ScreenHeader(subtitle: 'Scan Pelanggan'),
            const SizedBox(height: 8),
            Text('Scan QR Pelanggan', style: display(fontSize: 22, letterSpacing: -0.4)),
            const SizedBox(height: 4),
            Text('Tempel token QR pelanggan (mode demo) — kamera menyusul.',
                style: body(fontSize: 12.5, color: FortunasColors.ink3)),
            const SizedBox(height: 18),
            state.hasResult ? _resultView(state.result!) : _inputView(state),
          ],
        ),
      ),
    );
  }

  Widget _inputView(ScanState state) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // TODO seam: ganti TextField dgn MobileScanner saat device-day (lihat PENDING_EXTERNAL_SETUP).
        TextField(
          key: const Key('scan_token'),
          controller: _token,
          minLines: 1,
          maxLines: 3,
          decoration: const InputDecoration(labelText: 'Token QR pelanggan'),
          onChanged: (_) => setState(() {}),
        ),
        if (state.errorMessage != null)
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Text(state.errorMessage!,
                key: const Key('scan_error'),
                style: body(fontSize: 12.5, color: FortunasColors.error)),
          ),
        const SizedBox(height: 14),
        ElevatedButton(
          key: const Key('scan_submit'),
          onPressed: (state.submitting || _token.text.trim().isEmpty)
              ? null
              : () => ref.read(scanControllerProvider.notifier).validate(_token.text),
          child: Text(state.submitting ? 'Memvalidasi…' : 'Validasi'),
        ),
      ],
    );
  }

  Widget _resultView(QrValidateResponse r) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Container(
          key: const Key('scan_result'),
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: FortunasColors.surface,
            border: Border.all(
                color: r.valid ? FortunasColors.ink : FortunasColors.error, width: 2),
            borderRadius: BorderRadius.circular(16),
          ),
          child: r.valid
              ? _validBody(r)
              : Text(scanReasonMessage(r.reason),
                  style: body(fontSize: 14, color: FortunasColors.error)),
        ),
        const SizedBox(height: 14),
        OutlinedButton(
          key: const Key('scan_again'),
          onPressed: () {
            _token.clear();
            ref.read(scanControllerProvider.notifier).reset();
          },
          child: const Text('Scan lagi'),
        ),
      ],
    );
  }

  Widget _validBody(QrValidateResponse r) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('✓ ${r.username ?? 'Pelanggan'} terdaftar sebagai member',
            style: display(fontSize: 16, letterSpacing: -0.3)),
        const SizedBox(height: 8),
        Text(r.isNewMember ? 'Member baru 🎉' : 'Sudah member',
            style: body(fontSize: 13, color: FortunasColors.ink)),
        if (r.memberSince != null && r.memberSince!.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(top: 4),
            child: Text('Member sejak ${r.memberSince}',
                style: body(fontSize: 12, color: FortunasColors.ink3)),
          ),
      ],
    );
  }
}
