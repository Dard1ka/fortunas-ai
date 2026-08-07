# Aset pembayaran QRIS statis

Taruh gambar **QRIS toko** di folder ini dengan nama persis:

```
qr.jpeg
```

Layar pembayaran pelanggan (`lib/screens/public_order_screen.dart`) menampilkannya
lewat `Image.asset('assets/payments/qr.jpeg')`. Bila file belum ada, layar
menampilkan placeholder ("QR belum dipasang") — build tetap jalan.

Catatan:
- Ini QRIS **statis** tunggal (satu QR untuk seluruh pesanan). Nominal diketik/
  disesuaikan pembeli di aplikasi bank/e-wallet-nya; total pesanan ditampilkan di layar.
- QRIS **dinamis per-UMKM** (dan pembayaran otomatis via Midtrans) = future scope.
