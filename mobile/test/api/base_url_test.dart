import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/api/client.dart';

void main() {
  test('joinMediaUrl: path relatif digabung ke base', () {
    expect(joinMediaUrl('http://127.0.0.1:8000', '/media/products/a/b.png'),
        'http://127.0.0.1:8000/media/products/a/b.png');
  });

  test('joinMediaUrl: base kosong (same-origin web) menyisakan path relatif',
      () {
    expect(joinMediaUrl('', '/media/products/a/b.png'),
        '/media/products/a/b.png');
  });

  test('joinMediaUrl: imageUrl kosong menghasilkan string kosong', () {
    expect(joinMediaUrl('http://127.0.0.1:8000', ''), '');
    expect(joinMediaUrl('', ''), '');
  });

  test('di VM (bukan web) base API tetap absolut', () {
    // Test berjalan di Dart VM, jadi kIsWeb == false.
    expect(kApiBaseUrl, 'http://127.0.0.1:8000');
    expect(kMediaBaseUrl, 'http://127.0.0.1:8000');
  });
}
