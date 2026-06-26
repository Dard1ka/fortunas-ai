import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/scan/scan_rules.dart';

void main() {
  test('maps known reasons to Indonesian text', () {
    expect(scanReasonMessage('expired'), contains('kadaluarsa'));
    expect(scanReasonMessage('replayed'), contains('sudah dipakai'));
    expect(scanReasonMessage('tampered'), 'QR tidak valid.');
  });

  test('falls back for unknown/null', () {
    expect(scanReasonMessage(null), 'QR tidak valid.');
    expect(scanReasonMessage('weird'), 'QR tidak valid.');
  });
}
