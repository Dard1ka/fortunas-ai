import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/screens/briefing_kpi.dart';

void main() {
  group('pairRows', () {
    test('empty -> empty', () {
      expect(pairRows<int>(const []), <List<int>>[]);
    });
    test('single -> one singleton row', () {
      expect(pairRows(const [1]), [
        [1]
      ]);
    });
    test('pair -> one row', () {
      expect(pairRows(const [1, 2]), [
        [1, 2]
      ]);
    });
    test('three -> pair + singleton', () {
      expect(pairRows(const [1, 2, 3]), [
        [1, 2],
        [3]
      ]);
    });
    test('four -> two pairs', () {
      expect(pairRows(const [1, 2, 3, 4]), [
        [1, 2],
        [3, 4]
      ]);
    });
    test('five -> two pairs + singleton', () {
      expect(pairRows(const [1, 2, 3, 4, 5]), [
        [1, 2],
        [3, 4],
        [5]
      ]);
    });
    test('nine -> four pairs + singleton', () {
      expect(pairRows(const [1, 2, 3, 4, 5, 6, 7, 8, 9]), [
        [1, 2],
        [3, 4],
        [5, 6],
        [7, 8],
        [9]
      ]);
    });
  });
}
