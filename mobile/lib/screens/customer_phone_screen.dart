import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../customer/customer_auth_rules.dart';
import '../theme/tokens.dart';
import '../ui/screen_header.dart';

// Step 1 of customer login: phone entry. Dev-mode: no real SMS is sent;
// the OTP step is theatre (any 6 digits) — see CustomerOtpScreen.
class CustomerPhoneScreen extends StatefulWidget {
  const CustomerPhoneScreen({super.key});
  @override
  State<CustomerPhoneScreen> createState() => _CustomerPhoneScreenState();
}

class _CustomerPhoneScreenState extends State<CustomerPhoneScreen> {
  final _phone = TextEditingController();
  String? _error;

  @override
  void dispose() {
    _phone.dispose();
    super.dispose();
  }

  void _next() {
    final err = validatePhone(_phone.text);
    if (err != null) {
      setState(() => _error = err);
      return;
    }
    setState(() => _error = null);
    context.push('/customer/otp', extra: _phone.text);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: FortunasColors.bg,
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(18, 8, 18, 24),
          children: [
            const ScreenHeader(subtitle: 'Pelanggan'),
            const SizedBox(height: 8),
            Text('Masuk sebagai Pelanggan',
                style: display(fontSize: 22, letterSpacing: -0.4)),
            const SizedBox(height: 4),
            Text('Masukkan nomor HP untuk menerima kode OTP.',
                style: body(fontSize: 12.5, color: FortunasColors.ink3)),
            const SizedBox(height: 18),
            TextField(
              key: const Key('cust_phone'),
              controller: _phone,
              keyboardType: TextInputType.phone,
              decoration: const InputDecoration(labelText: 'Nomor HP'),
            ),
            if (_error != null)
              Padding(
                padding: const EdgeInsets.only(top: 6),
                child: Text(_error!,
                    style: body(fontSize: 12.5, color: FortunasColors.error)),
              ),
            const SizedBox(height: 14),
            ElevatedButton(
              key: const Key('cust_phone_next'),
              onPressed: _next,
              child: const Text('Lanjut'),
            ),
            const SizedBox(height: 6),
            TextButton(
              onPressed: () => context.go('/login'),
              child: const Text('Kembali ke login UMKM'),
            ),
          ],
        ),
      ),
    );
  }
}
