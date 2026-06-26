import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/client.dart';
import '../api/errors.dart';
import 'customer_qr_state.dart';

class CustomerQrController extends AutoDisposeNotifier<CustomerQrState> {
  Timer? _timer;

  @override
  CustomerQrState build() {
    ref.onDispose(() => _timer?.cancel());
    return const CustomerQrState();
  }

  Future<void> refresh() async {
    state = state.copyWith(loading: true, clearError: true);
    try {
      final s = await ref.read(apiProvider).customerQrSession();
      state = state.copyWith(loading: false, session: s);
      _scheduleRefresh(s.ttlSeconds);
    } catch (e) {
      // Keep any prior session visible; do NOT reschedule on error (manual retry via button).
      state = state.copyWith(loading: false, errorMessage: humanizeError(e));
    }
  }

  void _scheduleRefresh(int ttlSeconds) {
    _timer?.cancel();
    // Refresh BEFORE expiry (lead 5s) so the new QR arrives before the old dies = seamless.
    // Small ttl (tests) falls back to full ttl, floored at 1s so the Timer is never <=0.
    final lead = ttlSeconds > 10 ? ttlSeconds - 5 : (ttlSeconds > 0 ? ttlSeconds : 1);
    _timer = Timer(Duration(seconds: lead), refresh);
  }
}

final customerQrControllerProvider =
    NotifierProvider.autoDispose<CustomerQrController, CustomerQrState>(
        CustomerQrController.new);
