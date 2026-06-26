import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/api/models.dart';
import 'package:fortunas_ai/dpa/dpa_state.dart';

void main() {
  test('default state: not loading/editing, isEmpty true (no payload)', () {
    const s = DpaState();
    expect(s.loading, isFalse);
    expect(s.editing, isFalse);
    expect(s.isEmpty, isTrue);
  });

  test('isEmpty false when payload version >= 1', () {
    const s = DpaState(payload: DpaPayload(version: 1));
    expect(s.isEmpty, isFalse);
  });

  test('isEmpty true when payload version 0', () {
    const s = DpaState(payload: DpaPayload(version: 0));
    expect(s.isEmpty, isTrue);
  });

  test('copyWith clearError nulls errorMessage', () {
    const s = DpaState(errorMessage: 'x');
    expect(s.copyWith(clearError: true).errorMessage, isNull);
  });

  test('copyWith preserves unspecified fields', () {
    const s = DpaState(editing: true, draftRawText: 'hi');
    final s2 = s.copyWith(submitting: true);
    expect(s2.editing, isTrue);
    expect(s2.draftRawText, 'hi');
    expect(s2.submitting, isTrue);
  });
}
