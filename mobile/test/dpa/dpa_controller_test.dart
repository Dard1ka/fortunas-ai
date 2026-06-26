import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/api/client.dart';
import 'package:fortunas_ai/api/models.dart';
import 'package:fortunas_ai/dpa/dpa_controller.dart';

import '../support/fakes.dart';

ProviderContainer _container(FakeApi api) {
  final c = ProviderContainer(overrides: [apiProvider.overrideWithValue(api)]);
  addTearDown(c.dispose);
  return c;
}

DioException _http403() {
  final ro = RequestOptions(path: '/umkm/dpa');
  return DioException(
    requestOptions: ro,
    type: DioExceptionType.badResponse,
    response: Response(
      requestOptions: ro,
      statusCode: 403,
      data: {'detail': 'Konfirmasi password salah.'},
    ),
  );
}

void main() {
  test('load version 0 -> empty, not loading, not editing', () async {
    final api = FakeApi()..dpaResult = const DpaPayload(); // version 0
    final c = _container(api);
    await c.read(dpaControllerProvider.notifier).load();
    final s = c.read(dpaControllerProvider);
    expect(s.loading, isFalse);
    expect(s.isEmpty, isTrue);
    expect(s.editing, isFalse);
  });

  test('load version >= 1 -> read mode with payload', () async {
    final api = FakeApi()
      ..dpaResult = const DpaPayload(
        rawText: 'Tidak jual rokok.',
        forbiddenRules: ['rokok'],
        version: 2,
      );
    final c = _container(api);
    await c.read(dpaControllerProvider.notifier).load();
    final s = c.read(dpaControllerProvider);
    expect(s.isEmpty, isFalse);
    expect(s.payload?.forbiddenRules, ['rokok']);
  });

  test('load failure -> loadError set', () async {
    final api = FakeApi()..dpaError = _http403();
    final c = _container(api);
    await c.read(dpaControllerProvider.notifier).load();
    expect(c.read(dpaControllerProvider).loadError, 'Konfirmasi password salah.');
  });

  test('startEdit seeds drafts from payload', () async {
    final api = FakeApi()
      ..dpaResult = const DpaPayload(
          rawText: 'X', allowedRules: ['diskon'], forbiddenRules: ['rokok'], version: 1);
    final c = _container(api);
    final n = c.read(dpaControllerProvider.notifier);
    await n.load();
    n.startEdit();
    final s = c.read(dpaControllerProvider);
    expect(s.editing, isTrue);
    expect(s.draftRawText, 'X');
    expect(s.draftAllowed, ['diskon']);
    expect(s.draftForbidden, ['rokok']);
  });

  test('addForbidden dedups + removeForbidden via pure rules', () {
    final c = _container(FakeApi());
    final n = c.read(dpaControllerProvider.notifier);
    n.startEdit();
    n.addForbidden('rokok');
    n.addForbidden('ROKOK');
    expect(c.read(dpaControllerProvider).draftForbidden, ['rokok']);
    n.removeForbidden(0);
    expect(c.read(dpaControllerProvider).draftForbidden, isEmpty);
  });

  test('save success -> read mode + new payload, submitting false', () async {
    final api = FakeApi()
      ..updateResult =
          const DpaPayload(rawText: 'X', forbiddenRules: ['rokok'], version: 1);
    final c = _container(api);
    final n = c.read(dpaControllerProvider.notifier);
    n.startEdit();
    n.setRawText('X');
    n.addForbidden('rokok');
    final ok = await n.save('secret');
    final s = c.read(dpaControllerProvider);
    expect(ok, isTrue);
    expect(s.editing, isFalse);
    expect(s.submitting, isFalse);
    expect(s.payload?.version, 1);
    expect(api.lastUpdate?.password, 'secret');
    expect(api.lastUpdate?.forbiddenRules, ['rokok']);
  });

  test('save 403 -> errorMessage from detail, stays editing', () async {
    final api = FakeApi()..updateError = _http403();
    final c = _container(api);
    final n = c.read(dpaControllerProvider.notifier);
    n.startEdit();
    final ok = await n.save('wrong');
    final s = c.read(dpaControllerProvider);
    expect(ok, isFalse);
    expect(s.errorMessage, 'Konfirmasi password salah.');
    expect(s.editing, isTrue);
    expect(s.submitting, isFalse);
  });
}
