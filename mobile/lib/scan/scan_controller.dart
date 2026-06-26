import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/client.dart';
import '../api/errors.dart';
import '../api/models.dart';
import 'scan_state.dart';

class ScanController extends Notifier<ScanState> {
  @override
  ScanState build() => const ScanState();

  Future<void> validate(String token) async {
    state = state.copyWith(submitting: true, clearError: true, clearResult: true);
    try {
      final r = await ref.read(apiProvider).scanValidate(
            QrValidateRequest(customerQrToken: token.trim()),
          );
      // r.valid may be false (expired/tampered/replayed) — that is still a RESULT.
      state = state.copyWith(submitting: false, result: r);
    } catch (e) {
      state = state.copyWith(submitting: false, errorMessage: humanizeError(e));
    }
  }

  void reset() => state = const ScanState();
}

final scanControllerProvider =
    NotifierProvider<ScanController, ScanState>(ScanController.new);
