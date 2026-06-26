import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/api/client.dart';
import 'package:fortunas_ai/api/models.dart';
import 'package:fortunas_ai/auth/auth_controller.dart';
import 'package:fortunas_ai/auth/auth_state.dart';
import 'package:fortunas_ai/auth/token_store.dart';

import '../support/fakes.dart';

ProviderContainer _container(FakeApi api, FakeTokenStore store) {
  final c = ProviderContainer(overrides: [
    apiProvider.overrideWithValue(api),
    tokenStoreProvider.overrideWithValue(store),
  ]);
  addTearDown(c.dispose);
  return c;
}

DioException _http401() {
  final ro = RequestOptions(path: '/auth/login');
  return DioException(
    requestOptions: ro,
    type: DioExceptionType.badResponse,
    response: Response(
      requestOptions: ro,
      statusCode: 401,
      data: {'detail': 'Email atau password salah.'},
    ),
  );
}

void main() {
  test('bootstrap with no stored token -> unauthenticated', () async {
    final c = _container(FakeApi(), FakeTokenStore());
    await c.read(authControllerProvider.notifier).bootstrap();
    expect(c.read(authControllerProvider).status, AuthStatus.unauthenticated);
  });

  test('bootstrap with valid token -> authenticated + account + tokenProvider set', () async {
    final api = FakeApi()
      ..meResult = const UmkmAccount(email: 'a@b.id', tenantName: 'Toko');
    final c = _container(api, FakeTokenStore('jwt'));
    await c.read(authControllerProvider.notifier).bootstrap();
    final s = c.read(authControllerProvider);
    expect(s.status, AuthStatus.authenticated);
    expect(s.account?.email, 'a@b.id');
    expect(c.read(tokenProvider), 'jwt');
  });

  test('bootstrap token but /me fails -> token cleared, unauthenticated', () async {
    final api = FakeApi()..meError = _http401();
    final store = FakeTokenStore('jwt');
    final c = _container(api, store);
    await c.read(authControllerProvider.notifier).bootstrap();
    expect(c.read(authControllerProvider).status, AuthStatus.unauthenticated);
    expect(store.value, isNull);
    expect(c.read(tokenProvider), isNull);
  });

  test('login success persists token + authenticated with email', () async {
    final api = FakeApi()
      ..loginResult = const AuthResponse(
          accessToken: 'jwt', tenantId: 1, tenantName: 'Toko', tablePrefix: 'toko');
    final store = FakeTokenStore();
    final c = _container(api, store);
    final ok = await c.read(authControllerProvider.notifier).login('a@b.id', 'secret');
    expect(ok, isTrue);
    expect(store.value, 'jwt');
    expect(c.read(tokenProvider), 'jwt');
    final s = c.read(authControllerProvider);
    expect(s.status, AuthStatus.authenticated);
    expect(s.account?.email, 'a@b.id');
    expect(s.submitting, isFalse);
  });

  test('login failure surfaces detail + stays unauthenticated', () async {
    final api = FakeApi()..loginError = _http401();
    final store = FakeTokenStore();
    final c = _container(api, store);
    final ok = await c.read(authControllerProvider.notifier).login('a@b.id', 'wrong');
    expect(ok, isFalse);
    final s = c.read(authControllerProvider);
    expect(s.errorMessage, 'Email atau password salah.');
    expect(s.status, AuthStatus.unauthenticated);
    expect(s.submitting, isFalse);
    expect(store.value, isNull);
  });

  test('register success -> authenticated', () async {
    final api = FakeApi()
      ..registerResult = const AuthResponse(
          accessToken: 'jwt2', tenantId: 2, tenantName: 'Warung', tablePrefix: 'warung');
    final c = _container(api, FakeTokenStore());
    final ok = await c.read(authControllerProvider.notifier).register(
        email: 'w@x.id', password: 'secret', businessName: 'Warung');
    expect(ok, isTrue);
    expect(c.read(authControllerProvider).status, AuthStatus.authenticated);
    expect(c.read(authControllerProvider).account?.tenantName, 'Warung');
  });

  test('logout clears token + unauthenticated', () async {
    final store = FakeTokenStore('jwt');
    final c = _container(FakeApi(), store);
    c.read(tokenProvider.notifier).state = 'jwt';
    await c.read(authControllerProvider.notifier).logout();
    expect(c.read(authControllerProvider).status, AuthStatus.unauthenticated);
    expect(store.value, isNull);
    expect(c.read(tokenProvider), isNull);
  });
}
