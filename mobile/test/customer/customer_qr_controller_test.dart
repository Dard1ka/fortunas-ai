import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/api/client.dart';
import 'package:fortunas_ai/api/models.dart';
import 'package:fortunas_ai/customer/customer_qr_controller.dart';

import '../support/fakes.dart';

QrSessionResponse _resp({int ttl = 90}) => QrSessionResponse(
      qrToken: 'qr-jwt-token-abc', nonce: 'n1',
      issuedAt: '2026-06-26T00:00:00Z', expiresAt: '2026-06-26T00:01:30Z',
      ttlSeconds: ttl,
    );

/// autoDispose provider needs an active listener to stay alive in a container;
/// the listener + addTearDown(dispose) also cancels the controller's Timer
/// (via ref.onDispose) so no real timer leaks past the test.
ProviderContainer _container(FakeApi api) {
  final c = ProviderContainer(overrides: [apiProvider.overrideWithValue(api)]);
  c.listen(customerQrControllerProvider, (_, __) {});
  addTearDown(c.dispose);
  return c;
}

void main() {
  test('refresh success sets session + hasQr, loading false', () async {
    final api = FakeApi()..customerQrSessionResult = _resp();
    final c = _container(api);
    await c.read(customerQrControllerProvider.notifier).refresh();
    final st = c.read(customerQrControllerProvider);
    expect(st.hasQr, true);
    expect(st.session?.qrToken, 'qr-jwt-token-abc');
    expect(st.loading, false);
    expect(st.errorMessage, isNull);
    expect(api.customerQrSessionCallCount, 1);
  });

  test('refresh error sets errorMessage, session null', () async {
    final api = FakeApi()..customerQrSessionError = Exception('503');
    final c = _container(api);
    await c.read(customerQrControllerProvider.notifier).refresh();
    final st = c.read(customerQrControllerProvider);
    expect(st.errorMessage, isNotNull);
    expect(st.session, isNull);
    expect(st.hasQr, false);
    expect(st.loading, false);
  });
}
