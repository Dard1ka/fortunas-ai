import 'package:dio/dio.dart';

/// User-facing error messages in Bahasa Indonesia.
/// React equivalent: frontend/src/api/errors.js
String humanizeError(Object error) {
  if (error is DioException) {
    final code = error.response?.statusCode;
    if (error.type == DioExceptionType.cancel) return '';
    if (error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.receiveTimeout ||
        code == 408 ||
        code == 504) {
      return 'Permintaan memakan waktu terlalu lama. Coba sederhanakan pertanyaan.';
    }
    if (error.type == DioExceptionType.connectionError) {
      return 'Tidak dapat terhubung ke server. Periksa koneksi atau pastikan backend menyala.';
    }
    if (code == null) return 'Tidak dapat terhubung ke server.';
    if (code >= 500) return 'Server sedang bermasalah. Coba lagi sebentar lagi.';
    if (code == 429) return 'Terlalu banyak permintaan. Tunggu beberapa detik, lalu coba lagi.';
    if (code == 404) return 'Endpoint tidak ditemukan. Pastikan backend berjalan.';
    if (code >= 400) return 'Permintaan tidak dapat diproses. Periksa kembali pertanyaan Anda.';
  }
  return error.toString();
}
