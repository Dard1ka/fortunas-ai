import 'package:dio/dio.dart';

/// Attaches the bearer token to each request and signals 401s.
/// Pure (no Riverpod) so it is unit-testable by calling onRequest/onError.
class AuthInterceptor extends Interceptor {
  final String? Function() getToken;
  final void Function()? onUnauthorized;

  AuthInterceptor({required this.getToken, this.onUnauthorized});

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final token = getToken();
    if (token != null && token.isNotEmpty) {
      options.headers['Authorization'] = 'Bearer $token';
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
