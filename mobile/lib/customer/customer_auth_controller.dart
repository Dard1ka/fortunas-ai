import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/client.dart';
import '../api/errors.dart';
import '../api/models.dart';
import '../auth/token_store.dart';
import 'customer_auth_rules.dart';
import 'customer_auth_state.dart';

class CustomerAuthController extends Notifier<CustomerAuthState> {
  @override
  CustomerAuthState build() => const CustomerAuthState();

  FortunasApi get _api => ref.read(apiProvider);

  Future<bool> bootstrap({
    required String phone,
    required String username,
    required String birthDate,
  }) async {
    state = state.copyWith(submitting: true, clearError: true);
    try {
      final resp = await _api.customerBootstrap(CustomerBootstrapRequest(
        firebaseIdToken: devFirebaseToken(phone),
        username: username.trim(),
        birthDate: birthDate.trim(),
      ));
      ref.read(tokenProvider.notifier).state = resp.accessToken;
      state = state.copyWith(submitting: false, profile: resp.profile);
      return true;
    } catch (e) {
      state = state.copyWith(submitting: false, errorMessage: humanizeError(e), clearProfile: true);
      return false;
    }
  }

  void logout() {
    ref.read(tokenProvider.notifier).state = null;
    state = const CustomerAuthState();
  }
}

final customerAuthControllerProvider =
    NotifierProvider<CustomerAuthController, CustomerAuthState>(CustomerAuthController.new);
