// Pure helpers for the customer login (dev) flow. No Flutter/Riverpod deps.

String normalizePhone(String raw) => raw.replaceAll(RegExp(r'[^0-9]'), '');

/// Backend dev token (FORTUNAS_DEV_AUTH=1): `"dev:<uid>:<phone>"`.
/// uid and phone both use the normalized digits.
String devFirebaseToken(String phone) {
  final n = normalizePhone(phone);
  return 'dev:$n:$n';
}

String? validatePhone(String raw) =>
    normalizePhone(raw).length < 8 ? 'Nomor HP tidak valid (minimal 8 digit).' : null;

String? validateOtp(String raw) =>
    RegExp(r'^[0-9]{6}$').hasMatch(raw.trim()) ? null : 'Kode OTP harus 6 angka.';

String? validateUsername(String raw) =>
    raw.trim().isEmpty ? 'Nama wajib diisi.' : null;
