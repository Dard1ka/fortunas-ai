// mobile/test/dpa/dpa_rules_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/dpa/dpa_rules.dart';

void main() {
  group('addRule', () {
    test('appends trimmed value', () {
      expect(addRule(const ['a'], '  b '), ['a', 'b']);
    });
    test('ignores empty / whitespace-only', () {
      expect(addRule(const ['a'], '   '), ['a']);
      expect(addRule(const ['a'], ''), ['a']);
    });
    test('dedups case-insensitively (keeps existing)', () {
      expect(addRule(const ['Rokok'], 'rokok'), ['Rokok']);
    });
    test('does not mutate the input list', () {
      final input = ['a'];
      addRule(input, 'b');
      expect(input, ['a']);
    });
  });

  group('removeRuleAt', () {
    test('removes the entry at index', () {
      expect(removeRuleAt(const ['a', 'b', 'c'], 1), ['a', 'c']);
    });
    test('out-of-range index returns unchanged copy', () {
      expect(removeRuleAt(const ['a'], 5), ['a']);
      expect(removeRuleAt(const ['a'], -1), ['a']);
    });
  });
}
