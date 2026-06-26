# Handoff Day 10 — Scan QR Pelanggan (#5 mobile house)

**Dev hari ini:** Go Steven Sanjaya
**Tanggal:** 2026-06-27
**Branch:** `feat/scan-qr-membership` (dari `main` @ `0effa1b`) → PR #<TBD>

---

## ✅ Scan QR Pelanggan (#5 mobile house) — Flutter mobile

Layar UMKM untuk validasi QR pelanggan: input token manual → `POST /umkm/customer/scan/validate` → tampilkan hasil membership (member/non-member/alasan valid:false). Diakses via kartu "Scan QR Pelanggan" di home quick-action UMKM. **Backend sudah ada sejak Day 4 (PR #7) — tidak ada perubahan backend di slice ini.**

Fitur kamera (`mobile_scanner`) sengaja di-defer sebagai seam — UI house pakai `TextField` input token manual; kamera akan disambungkan saat device fisik tersedia (lihat `PENDING_EXTERNAL_SETUP.md`).

### File yang ditambahkan / diubah

| File | Keterangan |
|---|---|
| `mobile/lib/scan/scan_rules.dart` | Fungsi murni `scanReasonMessage(String? reason)` — terjemahan kode reason ke teks Bahasa Indonesia |
| `mobile/lib/scan/scan_state.dart` | `ScanState` immutable (result, submitting, errorMessage) + `hasResult` + `copyWith(clearResult/clearError)` |
| `mobile/lib/scan/scan_controller.dart` | `scanControllerProvider` (Riverpod `Notifier`): `validate(String token)` + `reset()` |
| `mobile/lib/screens/scan_screen.dart` | Layar scan: input token manual (`scan_token`) + tombol submit (`scan_submit`) + render hasil member/reason (`scan_result`) + error banner (`scan_error`) + tombol "Scan lagi" (`scan_again`) |
| `mobile/lib/api/client.dart` | Tambah method `scanValidate(QrValidateRequest, {CancelToken?})` — POST `/umkm/customer/scan/validate` |
| `mobile/lib/api/fake_api.dart` | Override `FakeApi.scanValidate` untuk test bebas jaringan |
| `mobile/lib/screens/home_screen.dart` | Kartu "Scan QR Pelanggan" (`home_scan`) di quick-action grid → route `/scan` |
| `mobile/lib/app.dart` | Tambah route `/scan` top-level (PhoneFrame-wrapped, outside ShellRoute) |
| `mobile/test/scan/scan_rules_test.dart` | Unit test `scanReasonMessage` |
| `mobile/test/scan/scan_controller_test.dart` | Unit test controller: `validate` sukses (valid:true), `validate` valid:false (hasil bukan error), error jaringan, `reset` |
| `mobile/test/screens/scan_screen_test.dart` | Widget test: render precedence hasResult→input, valid/invalid/error state, tombol "Scan lagi" |
| `mobile/test/screens/home_screen_test.dart` | +1 assertion gate: `/scan` (non-`/customer` path) → auth-gated untuk unauth user |

**Tidak ada perubahan backend/Python. NOL dependency baru.**

### Keputusan desain

| Topik | Keputusan |
|---|---|
| Input QR | Token input **manual** via `TextField` — kamera `mobile_scanner` = deferred seam (butuh device fisik + native plugin; CI tidak bisa validasi) |
| `valid:false` | Diperlakukan sebagai **hasil scan** (bukan error): `errorMessage == null`, `result` diisi dengan `valid=false` + `reason`. Error = kegagalan jaringan/server. |
| Membership | Standalone — backend `POST /umkm/customer/scan/validate` auto-insert membership jika first visit (sudah ada sejak Day 4) |
| Route gate | `/scan` bukan path `/customer` → `authRedirect` existing memetakan unauth→`/login`, auth→null. **NOL perubahan kode gate** — hanya +1 test assertion memverifikasi perilaku. |
| Dep baru | **NOL** — `mobile_scanner` tidak ditambahkan; TextField cukup untuk house; disambungkan saat device fisik siap |

### Catatan teknis

- `scan_controller.dart` pakai `scanControllerProvider` (Riverpod `Notifier`, bukan `AutoDispose`) — state scan dipertahankan selama sesi UMKM.
- Render precedence layar: `hasResult` → tampil hasil (member info + reason) · `submitting` → loading · else → form input.
- `valid:false` (expired/replayed/tampered QR) ditampilkan sebagai informasi membership (kartu merah + `scanReasonMessage(reason)`), bukan banner error. `scan_error` widget `findsNothing` di skenario ini.
- Kunci widget: `scan_token`, `scan_submit`, `scan_result`, `scan_error`, `scan_again`, `home_scan` — konsisten lintas task.
- `_QuickActionCard` di `home_screen.dart` sudah dipersiapkan dengan `super.key` (Day 9 slice 2) sehingga kunci bisa dipasang.
- Suite Flutter: **123 hijau** (naik dari 111 Day 9 slice 4). `flutter analyze --no-fatal-infos`: 7 info pre-existing (deprecated `localeId` + `print` di `tool/parser_check.dart`), exit 0, **tidak ada issue baru**.
- PR: **#<TBD>** (branch `feat/scan-qr-membership`)

## 🔴 Blocker

- TIDAK ADA.

## 📌 Out-of-scope / deferred

- Kamera `mobile_scanner` (device fisik + native plugin config) — dicatat di `PENDING_EXTERNAL_SETUP.md` "Scanner QR UMKM (#5)".
- Checkout scan integration (kolom BQ enriched `CustomerUserID`/`TenantID`) — scope Hari 9/10 original plan.
- Promo redemption via QR — v5.1 post-submission.
