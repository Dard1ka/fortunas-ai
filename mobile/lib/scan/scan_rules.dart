/// Pure mapping of backend scan-validate [reason] codes to Indonesian UI text.
String scanReasonMessage(String? reason) {
  switch (reason) {
    case 'expired':
      return 'QR sudah kadaluarsa. Minta pelanggan tampilkan ulang.';
    case 'replayed':
      return 'QR sudah dipakai. Minta QR baru dari pelanggan.';
    case 'tampered':
      return 'QR tidak valid.';
    default:
      return 'QR tidak valid.';
  }
}
