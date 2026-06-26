import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/auth/auth_redirect.dart';
import 'package:fortunas_ai/auth/auth_state.dart';

void main() {
  test('unknown -> /splash unless already on /splash', () {
    expect(authRedirect(AuthStatus.unknown, '/'), '/splash');
    expect(authRedirect(AuthStatus.unknown, '/briefing'), '/splash');
    expect(authRedirect(AuthStatus.unknown, '/splash'), isNull);
  });

  test('unauthenticated -> /login unless on /login or /register', () {
    expect(authRedirect(AuthStatus.unauthenticated, '/'), '/login');
    expect(authRedirect(AuthStatus.unauthenticated, '/me'), '/login');
    expect(authRedirect(AuthStatus.unauthenticated, '/login'), isNull);
    expect(authRedirect(AuthStatus.unauthenticated, '/register'), isNull);
  });

  test('authenticated -> / when on auth/splash pages, else stay', () {
    expect(authRedirect(AuthStatus.authenticated, '/login'), '/');
    expect(authRedirect(AuthStatus.authenticated, '/register'), '/');
    expect(authRedirect(AuthStatus.authenticated, '/splash'), '/');
    expect(authRedirect(AuthStatus.authenticated, '/briefing'), isNull);
    expect(authRedirect(AuthStatus.authenticated, '/'), isNull);
  });

  test('protected /dpa: authenticated allowed, unauthenticated -> /login', () {
    expect(authRedirect(AuthStatus.authenticated, '/dpa'), isNull);
    expect(authRedirect(AuthStatus.unauthenticated, '/dpa'), '/login');
    expect(authRedirect(AuthStatus.unknown, '/dpa'), '/splash');
  });
}
