import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../customer/customer_auth_controller.dart';
import '../customer/customer_auth_rules.dart';
import '../customer/customer_auth_state.dart';
import '../api/models.dart';
import '../theme/tokens.dart';
import '../ui/screen_header.dart';

/// Step 3 of customer login. Form mode collects username (+ optional birth
/// date) and bootstraps the session; once logged in, the same screen shows the
/// customer profile + logout. Slice 4 adds the QR button to the logged-in view.
class CustomerProfileScreen extends ConsumerStatefulWidget {
  final String phone;
  const CustomerProfileScreen({super.key, required this.phone});
  @override
  ConsumerState<CustomerProfileScreen> createState() => _CustomerProfileScreenState();
}

class _CustomerProfileScreenState extends ConsumerState<CustomerProfileScreen> {
  final _username = TextEditingController();
  final _birth = TextEditingController();
  String? _localError;

  @override
  void dispose() {
    _username.dispose();
    _birth.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final err = validateUsername(_username.text);
    if (err != null) {
      setState(() => _localError = err);
      return;
    }
    setState(() => _localError = null);
    await ref.read(customerAuthControllerProvider.notifier).bootstrap(
          phone: widget.phone,
          username: _username.text,
          birthDate: _birth.text,
        );
  }

  void _logout() {
    ref.read(customerAuthControllerProvider.notifier).logout();
    context.go('/login');
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(customerAuthControllerProvider);
    return Scaffold(
      backgroundColor: FortunasColors.bg,
      body: SafeArea(
        child: state.profile != null
            ? _loggedIn(state.profile!)
            : _form(state),
      ),
    );
  }

  Widget _form(CustomerAuthState state) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(18, 8, 18, 24),
      children: [
        const ScreenHeader(subtitle: 'Profil'),
        const SizedBox(height: 8),
        Text('Lengkapi profil', style: display(fontSize: 22, letterSpacing: -0.4)),
        const SizedBox(height: 4),
        Text('Nomor HP: ${widget.phone}',
            style: body(fontSize: 12.5, color: FortunasColors.ink3)),
        const SizedBox(height: 18),
        TextField(
          key: const Key('cust_username'),
          controller: _username,
          decoration: const InputDecoration(labelText: 'Nama'),
        ),
        const SizedBox(height: 12),
        TextField(
          key: const Key('cust_birth'),
          controller: _birth,
          decoration: const InputDecoration(labelText: 'Tanggal lahir (opsional, YYYY-MM-DD)'),
        ),
        if (_localError != null)
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Text(_localError!, style: body(fontSize: 12.5, color: FortunasColors.error)),
          ),
        if (state.errorMessage != null)
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Text(state.errorMessage!, style: body(fontSize: 12.5, color: FortunasColors.error)),
          ),
        const SizedBox(height: 14),
        ElevatedButton(
          key: const Key('cust_submit'),
          onPressed: state.submitting ? null : _submit,
          child: Text(state.submitting ? 'Memproses…' : 'Masuk'),
        ),
      ],
    );
  }

  Widget _loggedIn(CustomerProfile p) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(18, 8, 18, 24),
      children: [
        const ScreenHeader(subtitle: 'Pelanggan'),
        const SizedBox(height: 8),
        Text('Halo, ${p.username}', style: display(fontSize: 22, letterSpacing: -0.4)),
        const SizedBox(height: 12),
        _row('Nama', p.username),
        _row('Nomor HP', p.phoneNumber.isEmpty ? widget.phone : p.phoneNumber),
        if (p.createdAt.isNotEmpty) _row('Member sejak', p.createdAt),
        const SizedBox(height: 18),
        ElevatedButton(
          key: const Key('cust_show_qr'),
          onPressed: () => context.push('/customer/qr'),
          child: const Text('Tampilkan QR'),
        ),
        const SizedBox(height: 8),
        OutlinedButton(
          key: const Key('cust_logout'),
          onPressed: _logout,
          child: const Text('Keluar'),
        ),
      ],
    );
  }

  Widget _row(String label, String value) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 6),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label, style: mono(fontSize: 11, color: FortunasColors.ink3, letterSpacing: 0.6)),
            Text(value, style: body(fontSize: 13, color: FortunasColors.ink)),
          ],
        ),
      );
}
