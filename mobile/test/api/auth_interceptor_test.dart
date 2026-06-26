import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/api/auth_interceptor.dart';

void main() {
  test('attaches Bearer header when token present', () {
    final i = AuthInterceptor(getToken: () => 'jwt123');
    final options = RequestOptions(path: '/ask');
    i.onRequest(options, RequestInterceptorHandler());
    expect(options.headers['Authorization'], 'Bearer jwt123');
  });

  test('omits header when token null or empty', () {
    final i = AuthInterceptor(getToken: () => null);
    final o1 = RequestOptions(path: '/ask');
    i.onRequest(o1, RequestInterceptorHandler());
    expect(o1.headers.containsKey('Authorization'), isFalse);

    final i2 = AuthInterceptor(getToken: () => '');
    final o2 = RequestOptions(path: '/ask');
    i2.onRequest(o2, RequestInterceptorHandler());
    expect(o2.headers.containsKey('Authorization'), isFalse);
  });

  test('calls onUnauthorized on 401 response', () {
    var called = false;
    final i = AuthInterceptor(getToken: () => null, onUnauthorized: () => called = true);
    final ro = RequestOptions(path: '/ask');
    final err = DioException(
      requestOptions: ro,
      response: Response(requestOptions: ro, statusCode: 401),
    );
    // runZonedGuarded absorbs the standalone-handler completer artifact:
    // ErrorInterceptorHandler.next() completes an internal Completer with an
    // error; outside a real Dio chain there is no listener, which would
    // produce an unhandled async error. onUnauthorized fires synchronously
    // before propagation, so `called` is set before the expect.
    runZonedGuarded(
      () => i.onError(err, ErrorInterceptorHandler()),
      (_, __) {}, // absorb completer artifact
    );
    expect(called, isTrue);
  });

  test('does not call onUnauthorized on non-401', () {
    var called = false;
    final i = AuthInterceptor(getToken: () => null, onUnauthorized: () => called = true);
    final ro = RequestOptions(path: '/ask');
    final err = DioException(
      requestOptions: ro,
      response: Response(requestOptions: ro, statusCode: 500),
    );
    runZonedGuarded(
      () => i.onError(err, ErrorInterceptorHandler()),
      (_, __) {}, // absorb completer artifact
    );
    expect(called, isFalse);
  });
}
