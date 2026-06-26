import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/customer/customer_auth_rules.dart';

void main() {
  test('normalizePhone strips non-digits', () {
    expect(normalizePhone('+62 812-3456'), '628123456');
    expect(normalizePhone('0812 3456 789'), '08123456789');
  });

  test('devFirebaseToken builds dev:<uid>:<phone> from digits', () {
    expect(devFirebaseToken('+62 812-3456'), 'dev:628123456:628123456');
  });

  group('validatePhone', () {
    test('valid >= 8 digits', () => expect(validatePhone('08123456'), isNull));
    test('too short', () => expect(validatePhone('0812'), isNotNull));
    test('empty', () => expect(validatePhone(''), isNotNull));
  });

  group('validateOtp', () {
    test('exactly 6 digits ok', () => expect(validateOtp('123456'), isNull));
    test('not 6 digits', () {
      expect(validateOtp('123'), isNotNull);
      expect(validateOtp('1234567'), isNotNull);
      expect(validateOtp('abcdef'), isNotNull);
    });
  });

  group('validateUsername', () {
    test('non-empty ok', () => expect(validateUsername('Sari'), isNull));
    test('blank rejected', () => expect(validateUsername('   '), isNotNull));
  });
}
