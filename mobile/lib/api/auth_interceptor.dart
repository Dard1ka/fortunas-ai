import 'package:dio/dio.dart';

/// Attaches the bearer token to each request and signals 401s.
/// Pure (no Riverpod) so it is unit-testable by calling onRequest/onError.
class AuthInterceptor extends Interceptor {
  final String? Function() getToken;
  final void Function()? onUnauthorized;

  AuthInterceptor({required this.getToken, this.onUnauthorized});

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    // Jalur publik (`/public/*`) dipakai pelanggan ANONIM yang tak punya token.
    // Kalau seorang UMKM kebetulan sedang login di app yang sama, tokennya TAK
    // boleh ikut menempel di sini: backend `create_public_order` membaca header
    // ini sebagai identitas PELANGGAN (`_optional_customer_id`, role=customer),
    // jadi token UMKM cuma sampah yang berpotensi memicu 401 palsu. Di-skip.
    if (!options.path.startsWith('/public/')) {
      final token = getToken();
      if (token != null && token.isNotEmpty) {
        options.headers['Authorization'] = 'Bearer $token';
      }
    }
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    if (err.response?.statusCode == 401) {
      onUnauthorized?.call();
    }
    handler.next(err);
  }
}
