import 'package:dio/dio.dart';

/// User-facing error messages in Bahasa Indonesia.
/// React equivalent: frontend/src/api/errors.js
String humanizeError(Object error) {
  if (error is DioException) {
    // Prefer the backend's specific message (FastAPI {"detail": "..."}).
    final data = error.response?.data;
    if (data is Map &&
        data['detail'] is String &&
        (data['detail'] as String).trim().isNotEmpty) {
      return (data['detail'] as String).trim();
    }
    // Validasi FastAPI (422): detail berupa list [{loc, msg, type}, ...].
    // Tanpa ini pesannya jatuh ke teks generik dan user tak tahu field mana.
    if (data is Map && data['detail'] is List && (data['detail'] as List).isNotEmpty) {
      final first = (data['detail'] as List).first;
      if (first is Map) {
        final msg = first['msg']?.toString().trim() ?? '';
        final loc = first['loc'];
        final field = (loc is List && loc.isNotEmpty) ? loc.last.toString() : '';
        if (msg.isNotEmpty) {
          return field.isEmpty ? msg : '$field: $msg';
        }
      }
    }
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
