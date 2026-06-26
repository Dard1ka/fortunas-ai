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

  test('scan route requires UMKM auth', () {
    expect(authRedirect(AuthStatus.unauthenticated, '/scan'), '/login');
    expect(authRedirect(AuthStatus.authenticated, '/scan'), isNull);
  });

  test('customer flow allowed while UMKM unauthenticated', () {
    expect(authRedirect(AuthStatus.unauthenticated, '/customer/login'), isNull);
    expect(authRedirect(AuthStatus.unauthenticated, '/customer/otp'), isNull);
    expect(authRedirect(AuthStatus.unauthenticated, '/customer/profile'), isNull);
    expect(authRedirect(AuthStatus.unauthenticated, '/customer/qr'), isNull);
    // non-customer protected path still bounces:
    expect(authRedirect(AuthStatus.unauthenticated, '/random'), '/login');
    // unknown still goes to splash even for customer paths:
    expect(authRedirect(AuthStatus.unknown, '/customer/login'), '/splash');
    // authenticated UMKM hitting a customer path is allowed through (null),
    // because authRedirect only bounces onAuthPage or /splash to '/':
    expect(authRedirect(AuthStatus.authenticated, '/customer/login'), isNull);
  });
}
