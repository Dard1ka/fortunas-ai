import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../customer/customer_auth_rules.dart';
import '../theme/tokens.dart';
import '../ui/screen_header.dart';

// Step 2 of customer login: OTP entry. DEV MODE — there is no real SMS;
// any 6-digit code is accepted. Real Firebase phone-auth is a deferred seam
// (see Fortunas/PENDING_EXTERNAL_SETUP.md).
class CustomerOtpScreen extends StatefulWidget {
  final String phone;
  const CustomerOtpScreen({super.key, required this.phone});
  @override
  State<CustomerOtpScreen> createState() => _CustomerOtpScreenState();
}

class _CustomerOtpScreenState extends State<CustomerOtpScreen> {
  final _otp = TextEditingController();
  String? _error;

  @override
  void dispose() {
    _otp.dispose();
    super.dispose();
  }

  void _verify() {
    final err = validateOtp(_otp.text);
    if (err != null) {
      setState(() => _error = err);
      return;
    }
    setState(() => _error = null);
    context.push('/customer/profile', extra: widget.phone);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: FortunasColors.bg,
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(18, 8, 18, 24),
          children: [
            const ScreenHeader(subtitle: 'Verifikasi'),
            const SizedBox(height: 8),
            Text('Masukkan kode OTP',
                style: display(fontSize: 22, letterSpacing: -0.4)),
            const SizedBox(height: 4),
            Text('Mode demo: masukkan 6 angka apa saja.',
                style: body(fontSize: 12.5, color: FortunasColors.ink3)),
            const SizedBox(height: 18),
            TextField(
              key: const Key('cust_otp'),
              controller: _otp,
              keyboardType: TextInputType.number,
              decoration:
                  const InputDecoration(labelText: 'Kode OTP (6 angka)'),
            ),
            if (_error != null)
              Padding(
                padding: const EdgeInsets.only(top: 6),
                child: Text(_error!,
                    style: body(fontSize: 12.5, color: FortunasColors.error)),
              ),
            const SizedBox(height: 14),
            ElevatedButton(
              key: const Key('cust_otp_verify'),
              onPressed: _verify,
              child: const Text('Verifikasi'),
            ),
          ],
        ),
      ),
    );
  }
}
