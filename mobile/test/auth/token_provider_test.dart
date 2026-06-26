import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/auth/token_store.dart';

void main() {
  test('tokenProvider defaults to null and is settable', () {
    final c = ProviderContainer();
    addTearDown(c.dispose);
    expect(c.read(tokenProvider), isNull);
    c.read(tokenProvider.notifier).state = 'jwt';
    expect(c.read(tokenProvider), 'jwt');
  });
}
