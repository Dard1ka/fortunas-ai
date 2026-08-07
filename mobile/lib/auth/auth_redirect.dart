import 'auth_state.dart';

/// Pure gate logic for GoRouter `redirect`. Returns the path to redirect to,
/// or null to allow the requested [path].
String? authRedirect(AuthStatus status, String path) {
  final onAuthPage = path == '/login' || path == '/register';
  final isCustomerFlow = path.startsWith('/customer/');
  // Alur pesan-publik pelanggan: anonim, tanpa akun UMKM maupun customer.
  final isPublicOrder = path == '/order' || path.startsWith('/order/');
  switch (status) {
    case AuthStatus.unknown:
      return path == '/splash' ? null : '/splash';
    case AuthStatus.unauthenticated:
      return (onAuthPage || isCustomerFlow || isPublicOrder) ? null : '/login';
    case AuthStatus.authenticated:
      if (onAuthPage || path == '/splash') return '/';
      return null;
  }
}
