import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

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

/// Concrete secure store in the app; override in tests with a fake.
final tokenStoreProvider = Provider<TokenStore>((ref) => SecureTokenStore());

/// In-memory current bearer token — the single runtime source of truth the
/// Dio AuthInterceptor reads each request. Written by AuthController.
final tokenProvider = StateProvider<String?>((ref) => null);
