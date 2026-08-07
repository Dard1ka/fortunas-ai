import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Persists the UMKM bearer token across launches.
/// Abstract so tests inject a fake — [SecureTokenStore] uses a platform
/// channel and is verified by `flutter analyze` + manual run, not unit tests.
abstract class TokenStore {
  Future<String?> read();
  Future<void> write(String token);
  Future<void> delete();
}

class SecureTokenStore implements TokenStore {
  static const _key = 'umkm_access_token';
  final FlutterSecureStorage _storage;
  SecureTokenStore([FlutterSecureStorage? storage])
      : _storage = storage ?? const FlutterSecureStorage();

  @override
  Future<String?> read() => _storage.read(key: _key);
  @override
  Future<void> write(String token) => _storage.write(key: _key, value: token);
  @override
  Future<void> delete() => _storage.delete(key: _key);
}

/// Penyimpanan token untuk web.
///
/// Browser tidak punya padanan Keystore/Keychain, jadi token tinggal di
/// localStorage (lewat shared_preferences). Trade-off yang disengaja dan
/// didokumentasikan di spec §4.6: token kebaca JS bila ada XSS. Permukaan XSS
/// aplikasi ini dangkal secara struktural — CanvasKit menggambar seluruh UI ke
/// satu <canvas>, tidak ada innerHTML, dan index.html tidak memuat script
/// eksternal.
class PrefsTokenStore implements TokenStore {
  static const _key = 'umkm_access_token';

  @override
  Future<String?> read() async =>
      (await SharedPreferences.getInstance()).getString(_key);

  @override
  Future<void> write(String token) async =>
      (await SharedPreferences.getInstance()).setString(_key, token);

  @override
  Future<void> delete() async =>
      (await SharedPreferences.getInstance()).remove(_key);
}

/// Web (kanal rilis) pakai localStorage; native (APK demo) tetap
/// Keystore/Keychain. Override dengan fake di test.
final tokenStoreProvider = Provider<TokenStore>(
  (ref) => kIsWeb ? PrefsTokenStore() : SecureTokenStore(),
);

/// In-memory current bearer token — the single runtime source of truth the
/// Dio AuthInterceptor reads each request. Written by AuthController.
final tokenProvider = StateProvider<String?>((ref) => null);
