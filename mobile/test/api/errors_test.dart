import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/api/errors.dart';

DioException _err(int code, dynamic data) {
  final ro = RequestOptions(path: '/auth/login');
  return DioException(
    requestOptions: ro,
    type: DioExceptionType.badResponse,
    response: Response(requestOptions: ro, statusCode: code, data: data),
  );
}

void main() {
  test('returns backend detail when present', () {
    expect(
      humanizeError(_err(401, {'detail': 'Email atau password salah.'})),
      'Email atau password salah.',
    );
    expect(
      humanizeError(_err(409, {'detail': 'Email sudah terdaftar.'})),
      'Email sudah terdaftar.',
    );
  });

  test('falls back to generic message when no detail', () {
    expect(
      humanizeError(_err(500, null)),
      'Server sedang bermasalah. Coba lagi sebentar lagi.',
    );
  });
}
