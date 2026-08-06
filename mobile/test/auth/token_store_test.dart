import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/auth/token_store.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  test('PrefsTokenStore: write lalu read mengembalikan token', () async {
    final store = PrefsTokenStore();
    expect(await store.read(), isNull);
    await store.write('jwt-abc');
    expect(await store.read(), 'jwt-abc');
  });

  test('PrefsTokenStore: delete mengosongkan token', () async {
    final store = PrefsTokenStore();
    await store.write('jwt-abc');
    await store.delete();
    expect(await store.read(), isNull);
  });

  test('PrefsTokenStore: write menimpa nilai lama', () async {
    final store = PrefsTokenStore();
    await store.write('lama');
    await store.write('baru');
    expect(await store.read(), 'baru');
  });

  test('PrefsTokenStore: read tidak melihat key store lain (kunci benar dipakai)', () async {
    SharedPreferences.setMockInitialValues({'umkm_access_token': 'seeded-value'});
    final store = PrefsTokenStore();
    expect(await store.read(), 'seeded-value');
  });
}
