import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/api/client.dart';
import 'package:fortunas_ai/api/models.dart';
import 'package:fortunas_ai/auth/token_store.dart';
import 'package:fortunas_ai/customer/customer_auth_controller.dart';

import '../support/fakes.dart';

ProviderContainer _container(FakeApi api) {
  final c = ProviderContainer(overrides: [apiProvider.overrideWithValue(api)]);
  addTearDown(c.dispose);
  return c;
}

CustomerBootstrapResponse _resp() => const CustomerBootstrapResponse(
      accessToken: 'cust-jwt-123', role: 'customer', isNewUser: true,
      profile: CustomerProfile(customerUserId: 'C1', username: 'Sari', phoneNumber: '628123456'),
    );

void main() {
  test('bootstrap success sets tokenProvider + profile, sends dev token', () async {
    final api = FakeApi()..customerBootstrapResult = _resp();
    final c = _container(api);
    final ok = await c.read(customerAuthControllerProvider.notifier)
        .bootstrap(phone: '+62 812-3456', username: '  Sari  ', birthDate: '');
    expect(ok, true);
    expect(c.read(customerAuthControllerProvider).profile?.username, 'Sari');
    expect(c.read(customerAuthControllerProvider).submitting, false);
    expect(c.read(tokenProvider), 'cust-jwt-123');
    expect(api.lastCustomerBootstrap?.firebaseIdToken, 'dev:628123456:628123456');
    expect(api.lastCustomerBootstrap?.username, 'Sari'); // trimmed
  });

  test('bootstrap error sets errorMessage, no token, profile null', () async {
    final api = FakeApi()..customerBootstrapError = Exception('503');
    final c = _container(api);
    final ok = await c.read(customerAuthControllerProvider.notifier)
        .bootstrap(phone: '08123456', username: 'Sari', birthDate: '');
    expect(ok, false);
    final st = c.read(customerAuthControllerProvider);
    expect(st.errorMessage, isNotNull);
    expect(st.profile, isNull);
    expect(st.submitting, false);
    expect(c.read(tokenProvider), isNull);
  });

  test('logout clears token + state', () async {
    final api = FakeApi()..customerBootstrapResult = _resp();
    final c = _container(api);
    final ctrl = c.read(customerAuthControllerProvider.notifier);
    await ctrl.bootstrap(phone: '08123456', username: 'Sari', birthDate: '');
    ctrl.logout();
    expect(c.read(customerAuthControllerProvider).profile, isNull);
    expect(c.read(tokenProvider), isNull);
  });
}
