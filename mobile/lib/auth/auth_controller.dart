import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/client.dart';
import '../api/errors.dart';
import '../api/models.dart';
import 'auth_state.dart';
import 'token_store.dart';

class AuthController extends Notifier<AuthState> {
  @override
  AuthState build() => const AuthState();

  FortunasApi get _api => ref.read(apiProvider);
  TokenStore get _store => ref.read(tokenStoreProvider);
  void _setToken(String? token) =>
      ref.read(tokenProvider.notifier).state = token;

  Future<void> bootstrap() async {
    final stored = await _store.read();
    if (stored == null || stored.isEmpty) {
      state = const AuthState(status: AuthStatus.unauthenticated);
      return;
    }
    _setToken(stored);
    try {
      final account = await _api.me();
      state = AuthState(status: AuthStatus.authenticated, account: account);
    } catch (_) {
      await _store.delete();
      _setToken(null);
      state = const AuthState(status: AuthStatus.unauthenticated);
    }
  }

  Future<bool> login(String email, String password) async {
    state = state.copyWith(submitting: true, clearError: true);
    try {
      final res = await _api.login(email, password);
      await _persist(res, email);
      return true;
    } catch (e) {
      _fail(e);
      return false;
    }
  }

  Future<bool> register({
    required String email,
    required String password,
    required String businessName,
  }) async {
    state = state.copyWith(submitting: true, clearError: true);
    try {
      final res = await _api.register(
          email: email, password: password, businessName: businessName);
      await _persist(res, email);
      return true;
    } catch (e) {
      _fail(e);
      return false;
    }
  }

  Future<void> logout() async {
    await _store.delete();
    _setToken(null);
    state = const AuthState(status: AuthStatus.unauthenticated);
  }

  Future<void> _persist(AuthResponse res, String email) async {
    await _store.write(res.accessToken);
    _setToken(res.accessToken);
    state = AuthState(
      status: AuthStatus.authenticated,
      account: UmkmAccount(
        email: email,
        tenantId: res.tenantId,
        tenantName: res.tenantName,
        tablePrefix: res.tablePrefix,
      ),
    );
  }

  void _fail(Object e) {
    state = state.copyWith(
      submitting: false,
      status: AuthStatus.unauthenticated,
      errorMessage: humanizeError(e),
    );
  }
}

final authControllerProvider =
    NotifierProvider<AuthController, AuthState>(AuthController.new);
