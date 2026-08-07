import 'package:dio/dio.dart';
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

  // ── Topologi same-origin: base berakhir `/api`, endpoint mulai `/…` ──
  //
  // Yang menopang seluruh deployment PWA bukan nilai konstanta `kApiBaseUrl`,
  // melainkan cara Dio MENGGABUNGKAN base itu dengan path endpoint. nginx
  // memakai `location /api/ { proxy_pass http://127.0.0.1:8000/; }` — trailing
  // slash pada `proxy_pass` MEMOTONG prefiks `/api`, jadi backend menerima
  // `/auth/login`, persis route yang memang ada. Itu hanya benar kalau URI yang
  // dikirim browser tepat `/api/auth/login`. Kalau join pernah menghasilkan
  // `/apiauth/login`, `/api//auth/login`, atau `/auth/login` (base terbuang),
  // seluruh deployment mati dan tidak ada test lain yang menangkapnya.
  //
  // Dio menggabungkan dengan `baseUrl + path` lalu `Uri.parse(...)
  // .normalizePath()` (`dio/lib/src/options.dart:662-677`) — jalur kode yang
  // SAMA entah base-nya relatif atau absolut. Jadi bentuk join-nya bisa dipaku
  // dari Dart VM dengan base absolut yang berakhir `/api`; yang tidak bisa
  // disimulasi di VM hanyalah base relatifnya sendiri (lihat test berikutnya).
  //
  // Port 1 di loopback: connection refused seketika, jadi test ini offline-safe
  // dan tidak pernah menyentuh jaringan nyata. Yang diperiksa bukan responsnya,
  // tapi URI yang Dio sudah susun dan bawa di `requestOptions`.
  test('join same-origin: base berakhir /api + /auth/login → /api/auth/login',
      () async {
    final api = FortunasApi(baseUrl: 'http://127.0.0.1:1/api');
    try {
      await api.login('owner@toko.com', 'rahasia123');
      fail('request ke port 1 seharusnya tidak pernah berhasil');
    } on DioException catch (e) {
      expect(e.requestOptions.uri.path, '/api/auth/login');
    }
  });

  // Temuan saat menulis test di atas, dipaku supaya tidak jadi kejutan:
  // Dio MENOLAK base relatif di luar web — setter `baseUrl`
  // (`dio/lib/src/options.dart:103`) melempar ArgumentError kalau
  // `!kIsWeb && Uri.parse(value).host.isEmpty`. Jadi `'/api'` sah HANYA di
  // build web. Konsekuensi praktis: jangan pernah menjalankan build native
  // (APK demo) dengan `--dart-define=FORTUNAS_API=/api` — app akan melempar
  // saat `FortunasApi` dibuat, bukan gagal pelan-pelan di request pertama.
  test('base relatif hanya sah di web — di VM Dio melempar ArgumentError', () {
    expect(() => FortunasApi(baseUrl: '/api'), throwsArgumentError);
  });
}
