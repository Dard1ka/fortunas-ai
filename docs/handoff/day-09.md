# Handoff Day 9 — Sprint Briefing → Checkout → Customer OTP → Render QR (Slice 1 of 4)

**Dev hari ini:** Go Steven Sanjaya
**Tanggal:** 2026-06-26
**Branch:** `feat/briefing-5analisis-ui` (dari `main` @ `0effa1b`) → PR #13

> **Day 9 adalah sprint 4-slice.** File ini akan dilengkapi oleh slice 2–4 (Checkout UI, Customer OTP, Render QR) sebelum merge ke `main`.

---

## ✅ Slice 1 — Briefing 5-analisis UI (Flutter mobile)

Layar briefing kini menampilkan **semua 5 analisis** termasuk `top_product` (sebelumnya hanya 4 via `take(4)`). Grid KPI diganti layout 2-kolom berbasis `Column`/`Row` dengan kartu ganjil (trailing) yang otomatis span full-width melalui helper murni `pairRows`.

### File yang diubah

| File | Keterangan |
|---|---|
| `mobile/lib/screens/briefing_kpi.dart` | Tambah fungsi murni generic `pairRows<T>` untuk grouping KPI row |
| `mobile/lib/screens/briefing_screen.dart` | Hapus `.take(4)` → semua analisis render; identitas `top_product` (icon `flame`, accent `warning`); ganti `GridView.count` → `Column`/`Row` + `pairRows`; `FakeApi.reportDaily` override |
| `mobile/test/screens/briefing_kpi_test.dart` | Unit test `pairRows` (6 case: empty, single, pair, 4, 5, 9) |
| `mobile/test/screens/briefing_screen_test.dart` | Widget test: semua 5 label tampil; kartu ganjil (ke-5) full-width |

**Tidak ada perubahan backend/Python. Tidak ada dependency baru.**

### Identitas `top_product`

| Atribut | Nilai |
|---|---|
| Icon | `Icons.local_fire_department_outlined` ("flame") |
| Accent color | `FortunasColors.warning` |

### Keputusan layout

`GridView.count(crossAxisCount: 2)` tidak bisa membuat kartu terakhir span full-width secara native. Solusi: layout manual `Column` + `Row`, dibantu fungsi murni `pairRows<T>` yang memecah list menjadi baris 2-item; item ganjil terakhir menghasilkan singleton row (`[item]`). Kartu singleton dirender dengan `Expanded` penuh. Pendekatan ini lebih mudah ditest (pure fn, tanpa widget) dan tidak butuh `GridView.builder` + `crossAxisCellCount` dari Sliver.

## ⚙️ Catatan teknis & keputusan kunci

- `pairRows` adalah fungsi murni generic — ditest di unit test terpisah tanpa widget pump.
- `briefing_screen_test` pakai `FakeApi.reportDaily` override (pola yang sama dengan `FakeApi` di slice sebelumnya) sehingga bebas jaringan dan server.
- Dikerjakan dalam beberapa commit terpisah (feat → test assertion → hardening) untuk menjaga riwayat review jelas; di-squash saat merge (lihat PR #13).
- Final review (opus) menambah guard overflow: widget test pada `textScaler` 1.5× memastikan kartu KPI tidak overflow di text-scale besar (tinggi baris `_kpiRowHeight = 116.0` tetap; 1.5× tidak overflow → tanpa perubahan layout, risiko dikunci test).
- Suite Flutter: **64 hijau** (naik dari 52 Day 8). `flutter analyze --no-fatal-infos`: 7 info pre-existing (deprecated `localeId` + `print` di `tool/parser_check.dart`), exit 0, **tidak ada issue baru**.

## 🔴 Blocker

- TIDAK ADA.

## 🎯 Slice berikutnya (2–4, masih dalam branch ini)

- **Slice 2:** Checkout UI mobile (`/checkout` layar konfirmasi + integrasi `POST /checkout/confirm`)
- **Slice 3:** Customer phone OTP (3 layar: HP → OTP → profil)
- **Slice 4:** Render QR identity customer (`qr_flutter`, auto-refresh 90s)

Semua slice akan ditambahkan ke file `day-09.md` ini sebelum PR #13 di-merge.

## 📌 Out-of-scope / deferred

- Scanner QR sisi UMKM (`mobile_scanner` + kamera) — slice terpisah.
- BigQuery kolom enriched `CustomerUserID`/`TenantID` di checkout — slice 2 scope.
- Tidak ada seam eksternal baru → `PENDING_EXTERNAL_SETUP.md` tak berubah.

---

## ✅ Slice 2 — Checkout (Kasir) Screen (Flutter mobile)

Layar kasir manual multi-item untuk UMKM: input produk + qty + harga → kirim ke `POST /checkout/confirm` → tampilkan hasil inline. Tidak ada promo, tidak ada scanner QR customer (deferred), `customer_qr_token` null by default.

### File yang diubah

| File | Keterangan |
|---|---|
| `mobile/lib/checkout/checkout_rules.dart` | Fungsi murni: `parseLineItem`, `canConfirm`, `grandTotal`, `withItem`, `withoutItemAt` |
| `mobile/lib/checkout/checkout_state.dart` | `CheckoutLineItem`, `CheckoutResult`, `CheckoutState` (immutable + `copyWith` dengan `clearResult`/`clearError`) |
| `mobile/lib/checkout/checkout_controller.dart` | `CheckoutController` (Riverpod `Notifier`): `addItem`, `removeItemAt`, `confirm`, `reset` |
| `mobile/lib/api/client.dart` | Tambah method `checkoutConfirm(String rawText)` — thin wrapper `POST /checkout/confirm` |
| `mobile/lib/api/fake_api.dart` | Override `FakeApi.checkoutConfirm` untuk test bebas jaringan |
| `mobile/lib/screens/checkout/checkout_screen.dart` | Layar kasir: form input item, list item + hapus, pinned total + tombol Konfirmasi, inline success `_SuccessView` (invoice + total + reply AI + "Transaksi Baru"), error banner |
| `mobile/lib/app.dart` | Tambah route `/checkout` ke `GoRouter` |
| `mobile/lib/screens/home_screen.dart` | Kartu "Kasir" di quick-action grid (generalize `_QuickActionCard`) |
| `mobile/test/checkout/checkout_rules_test.dart` | Unit test fungsi murni checkout rules (10 case) |
| `mobile/test/checkout/checkout_controller_test.dart` | Unit test controller (5 case: addItem/removeItemAt, confirm sukses, confirm error, no-op tanpa item, reset) |
| `mobile/test/screens/checkout_screen_test.dart` | Widget test: Konfirmasi disabled tanpa item, Tambah → update total + enable Konfirmasi |

**Tidak ada perubahan backend/Python. Tidak ada dependency baru.**

### Keputusan desain

| Topik | Keputusan |
|---|---|
| Input transaksi | Manual multi-item kasir — satu baris per item (nama, qty, harga) |
| `customer_qr_token` | `null` (scanner QR deferred ke slice terpisah) |
| Customer name | Opsional — field kosong tetap lolos konfirmasi |
| Success state | Inline (bukan navigasi): `_SuccessView` tampil di halaman yang sama dengan invoice, total, reply AI, dan tombol "Transaksi Baru" |
| Promo | Tidak ada di slice ini — deferred ke v5.1 |
| Scanner QR | Tidak ada di slice ini — deferred ke slice QR terpisah |
| Pinned confirm bar | `SafeArea` + `Column` fixed di bawah layar — tidak ter-scroll |
| Test transport | `FakeApi.checkoutConfirm` override (pola DPA/auth) — bebas jaringan |

### Catatan teknis

- `parseLineItem` returns `({CheckoutLineItem? item, String? error})` — named record. Dikonsumsi di screen sebagai `parsed.error` / `parsed.item!`.
- `checkoutControllerProvider` expose state dengan getter convenience: `checkoutResult`, `checkoutError`, `lastCheckout`, `submitting`.
- `_QuickActionCard` di `home_screen.dart` digeneralisasi (sebelumnya hardcoded DPA card) — tidak ada perubahan visual kartu yang sudah ada.
- PR #13 masih terbuka (branch `feat/checkout-kasir-screen`, squash merge setelah semua slice selesai).

## ⚙️ Catatan teknis Slice 2

- Tidak ada seam eksternal baru.
- Suite Flutter: **84 hijau** (naik dari 64 Day 9 slice 1). `flutter analyze --no-fatal-infos`: 7 info pre-existing (sama persis dengan slice 1), exit 0, **tidak ada issue baru**.
- PR: **#14** (branch `feat/checkout-kasir-screen`)

## 🔴 Blocker Slice 2

- TIDAK ADA.

## 🎯 Slice berikutnya (3–4, masih dalam branch ini)

- **Slice 3:** Customer phone OTP (3 layar: HP → OTP → profil)
- **Slice 4:** Render QR identity customer (`qr_flutter`, auto-refresh 90s)
