import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/api/client.dart';
import 'package:fortunas_ai/api/models.dart';
import 'package:fortunas_ai/scan/scan_controller.dart';

import '../support/fakes.dart';

ProviderContainer _container(FakeApi api) {
  final c = ProviderContainer(overrides: [apiProvider.overrideWithValue(api)]);
  addTearDown(c.dispose);
  return c;
}

void main() {
  test('validate success (valid=true) sets result, no error, trims token', () async {
    final api = FakeApi()
      ..scanValidateResult = const QrValidateResponse(
          valid: true, customerUserId: 'C1', username: 'Sari',
          isNewMember: true, memberSince: '2026-06-27');
    final c = _container(api);
    await c.read(scanControllerProvider.notifier).validate('  qr-token  ');
    final st = c.read(scanControllerProvider);
    expect(st.result?.valid, true);
    expect(st.result?.username, 'Sari');
    expect(st.submitting, false);
    expect(st.errorMessage, isNull);
    expect(api.lastScanValidate?.customerQrToken, 'qr-token');
  });

  test('validate invalid (valid=false) is a result, NOT an error', () async {
    final api = FakeApi()
      ..scanValidateResult = const QrValidateResponse(valid: false, reason: 'expired');
    final c = _container(api);
    await c.read(scanControllerProvider.notifier).validate('qr-token');
    final st = c.read(scanControllerProvider);
    expect(st.result?.valid, false);
    expect(st.result?.reason, 'expired');
    expect(st.errorMessage, isNull);
    expect(st.submitting, false);
  });

  test('validate exception sets errorMessage, result null', () async {
    final api = FakeApi()..scanValidateError = Exception('503');
    final c = _container(api);
    await c.read(scanControllerProvider.notifier).validate('qr-token');
    final st = c.read(scanControllerProvider);
    expect(st.errorMessage, isNotNull);
    expect(st.result, isNull);
    expect(st.submitting, false);
  });

  test('reset clears result + error', () async {
    final api = FakeApi()
      ..scanValidateResult = const QrValidateResponse(valid: true, username: 'Sari', isNewMember: false);
    final c = _container(api);
    final ctrl = c.read(scanControllerProvider.notifier);
    await ctrl.validate('qr-token');
    ctrl.reset();
    expect(c.read(scanControllerProvider).hasResult, false);
    expect(c.read(scanControllerProvider).errorMessage, isNull);
  });
}
