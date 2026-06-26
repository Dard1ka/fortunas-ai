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
