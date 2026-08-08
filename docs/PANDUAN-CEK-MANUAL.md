# Panduan Cek Manual — Fortunas AI (PWA React)

Panduan ini untuk hal-hal yang **tidak bisa diverifikasi otomatis** karena butuh HP sungguhan:
izin mikrofon, pemasangan aplikasi ke layar utama, dan kenyamanan sentuh. Sisanya (login,
analisis, kasir, DPA, scan, offline) sudah diuji otomatis — hasilnya di
`docs/VERIFICATION-2026-08-08.md`.

**Alamat aplikasi:** `https://app.fortunas.id`
**Perlu:** 1 HP Android (Chrome) dan/atau iPhone (Safari), koneksi internet, akun UMKM uji.

Tiap langkah ditulis dengan format yang sama: **apa yang ditekan → apa yang diharapkan →
artinya kalau tidak terjadi.** Kalau ada satu langkah gagal, lanjut saja ke langkah berikutnya
dan catat yang gagal — tidak ada langkah yang saling menggantung.

---

## 1. Mikrofon & suara

**Tekan:** buka `https://app.fortunas.id` di HP → login → di layar Beranda, ketuk **tombol mic
bulat** di sebelah kotak pertanyaan → izinkan saat browser bertanya → ucapkan
*"siapa pelanggan paling loyal saya"* → ketuk mic sekali lagi untuk berhenti.

**Diharapkan:** muncul tulisan `● Mendengar… ketuk mic lagi untuk berhenti` saat merekam, lalu
kalimatmu masuk ke kotak pertanyaan.

**Kalau tidak terjadi:**
- Browser sama sekali tidak menanyakan izin → halamannya belum HTTPS (alamatnya harus `https://`,
  bukan `http://`). Ini masalah server, bukan HP-mu.
- Izin muncul tapi teks tidak keluar → mesin pengenal suara browser tidak mendukung; catat merek
  HP + versi Chrome/Safari-nya.

## 2. Pasang ke layar utama — Android (Chrome)

**Tekan:** buka `https://app.fortunas.id` di Chrome → menu **⋮** (kanan atas) → **Tambahkan ke
layar utama** / *Install app* → konfirmasi.

**Diharapkan:** ikon Fortunas muncul di layar utama HP. Buka dari ikon itu — aplikasi tampil
**tanpa address bar** browser.

**Kalau tidak terjadi:** menu "Tambahkan ke layar utama" tidak ada → service worker atau manifest
gagal dimuat. Catat dan laporkan; ini masalah build/server.

## 3. Pasang ke layar utama — iPhone (Safari)

**Tekan:** buka `https://app.fortunas.id` di **Safari** (bukan Chrome iOS) → tombol **Bagikan**
(kotak dengan panah ke atas) → **Tambahkan ke Layar Utama** → Tambah.

**Diharapkan:** ikon muncul di layar utama, terbuka tanpa address bar.

**Catatan penting:** di iOS memang **tidak akan pernah** muncul tawaran pasang otomatis — Apple
tidak menyediakannya. Harus lewat menu Bagikan. Jadi ini **perilaku normal, bukan kerusakan**.

## 4. Boot saat offline

**Tekan:** buka aplikasi sekali sampai selesai memuat (online) → aktifkan **mode pesawat** →
tutup aplikasi → buka lagi dari ikon layar utama.

**Diharapkan:** aplikasi tetap terbuka dan tampilannya muncul (isi data tentu kosong/tertunda —
yang diuji di sini kemampuannya menyala tanpa internet).

**Kalau tidak terjadi:** layar putih atau pesan "tidak ada koneksi" → service worker belum
terpasang. Coba buka sekali lagi dalam keadaan online (pemasangan terjadi di kunjungan pertama),
baru ulangi. Kalau tetap gagal, laporkan.

> Yang **bukan** masalah: kunjungan **paling pertama** tetap butuh internet. Itu memang caranya
> bekerja, bukan bug.

## 5. Scan member — daftarkan pelanggan

> ⚠️ Langkah 5 dan 6 butuh **dua HP** (satu jadi kasir, satu jadi pelanggan), dan butuh mode
> pengembangan login pelanggan **dinyalakan sementara** — login pelanggan pakai OTP sungguhan
> belum aktif (menunggu Firebase). Minta dev menyalakannya sebelum mulai, dan mematikannya lagi
> setelah selesai.

**Tekan:**
1. **HP pelanggan:** buka `https://app.fortunas.id/customer/login` → isi nomor HP →
   **Kirim kode OTP** → isi 6 angka bebas → isi nama → masuk → buka menu **QR** →
   ketuk **Salin token**.
2. **HP kasir:** Beranda → aksi cepat **Scan Member** → tempel token di kotak
   **Token QR pelanggan** → **Validasi**.

**Diharapkan:** muncul pesan sukses dengan **ikon centang** dan keterangan pelanggan terdaftar
sebagai member (varian *member baru* atau *member sejak …*).

**Kalau tidak terjadi:**
- Muncul kotak kosong atau karakter aneh, bukan centang → laporkan, itu kemunduran tampilan ikon.
- Pesan **"QR sudah dipakai"** → token bekas. Token **sekali pakai dan hangus dalam 90 detik**;
  minta pelanggan menekan **Perbarui** di layar QR-nya, lalu salin token yang baru.

## 6. Kasir — transaksi + tautkan pelanggan

**Tekan:** HP kasir → Beranda → aksi cepat **Kasir** → isi 2 barang (nama, jumlah, harga) →
tempel **token QR pelanggan yang BARU** (bukan yang tadi dipakai di langkah 5!) →
**Simpan transaksi**.

**Diharapkan:** transaksi tersimpan, dan di kartu hasil muncul **`Customer tertaut ✓`** beserta
keterangan *(member baru)* atau *(member sejak …)*.

**Kalau tidak terjadi:** transaksi tersimpan tapi muncul catatan bahwa poin tidak terhubung →
tokennya bekas atau sudah lewat 90 detik. **Ini justru perilaku yang benar**: transaksinya tidak
boleh gagal cuma karena QR-nya kedaluwarsa, dan aplikasi wajib memberitahumu apa adanya. Ulangi
dengan token segar. Yang **salah** adalah kalau gagal tapi tampak seperti berhasil.

## 7. Kenyamanan sentuh & keterbacaan

**Tekan:** telusuri layar Beranda, Kasir, Briefing, dan Riwayat sambil memegang HP satu tangan.

**Diharapkan:** semua tombol dan chip enak ditekan dengan jempol tanpa meleset, dan teks terbaca
tanpa perlu memperbesar layar.

**Kalau tidak terjadi:** catat layar dan tombol mana yang terlalu kecil atau tulisannya terlalu
kecil, sertakan tangkapan layar. Itu berarti ada ukuran yang lolos dari standar kami (minimal
44 piksel untuk area sentuh).

---

## Cara melaporkan hasil

Untuk tiap langkah cukup tulis: **nomor langkah — berhasil / gagal — (kalau gagal: apa yang
terlihat + tangkapan layar + merek HP & browser).**

Hasilnya nanti dipindahkan ke `docs/VERIFICATION-2026-08-08.md`: yang berhasil menjadi baris
**PROVEN**, yang gagal menjadi temuan yang ditindaklanjuti.

## Yang belum bisa dicek di panduan ini

- **Pembayaran QRIS dan halaman pesan-antar publik** — layar-layar itu belum diport ke aplikasi
  React (masih dijadwalkan, lihat catatan Wave C). Akan ditambahkan ke panduan ini saat sudah ada.
- **OTP SMS sungguhan** — masih menunggu penyiapan Firebase; sementara ini login pelanggan
  memakai mode pengembangan seperti dicatat di langkah 5.
