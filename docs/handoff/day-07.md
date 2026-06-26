# Handoff Day 7 (Mobile Login UMKM — MVP #1 sisi Flutter)

> _Ditulis retroaktif (backfill) 2026-06-26 dari git history + catatan dev; fakta diverifikasi terhadap squash `e045567` (PR #10)._

**Dev hari ini:** Go Steven Sanjaya
**Tanggal:** 2026-06-26
**Branch:** `feat/mobile-login-umkm` (dari `main` @ `806df95` = Day 6 merge) → PR #10, squash `e045567`

## ✅ Selesai — MVP fitur #1 (Login UMKM, sisi aplikasi Flutter)

**Pertama kali track Flutter dikerjakan.** Sebelum slice ini mobile app **tanpa auth** (langsung Home, client tanpa token). Sekarang: bootstrap → splash → login/register → token → route ter-gate → logout + auto-logout 401.

- `lib/api/models.dart` — DTO `AuthResponse` + `UmkmAccount`.
- `lib/api/errors.dart` — `humanizeError` mengangkat `detail` pesan backend.
- `lib/auth/token_store.dart` — abstract `TokenStore` + `SecureTokenStore` (`flutter_secure_storage`) + `tokenStoreProvider` + `tokenProvider`.
- `lib/api/auth_interceptor.dart` + `lib/api/client.dart` — `AuthInterceptor` auto-`Bearer` + `login/register/me` + `apiProvider` token-aware (+ `onUnauthorized`→logout).
- `lib/auth/auth_state.dart` + `auth_controller.dart` — `AuthState`/`AuthStatus` + `AuthController` (bootstrap/login/register/logout).
- `lib/auth/auth_redirect.dart` — `authRedirect()` pure (gate).
- `lib/app.dart` — `routerProvider` (GoRouter + `refreshListenable`), bootstrap di `initState`.
- `lib/screens/` — `splash_screen.dart`, `login_screen.dart`, `register_screen.dart`, `profile_screen.dart` (kartu Akun + logout).
- `test/support/fakes.dart` — `FakeApi` + `FakeTokenStore` (seam test).

## ⚙️ Catatan teknis & keputusan kunci

- **Token di `flutter_secure_storage`** (bukan `shared_preferences`) — Keystore/Keychain, never di-log/prefs.
- **Token↔client "approach B":** `tokenProvider` in-memory (sinkron untuk interceptor) + persist `TokenStore`.
- **`mobile/pubspec.lock` tetap UNTRACKED** ikut konvensi `.gitignore` repo (Steven pilih saat plan — GitHub = sumber kebenaran).
- **CI mobile sekarang jalan `flutter test`** (dulu cuma `flutter analyze`).
- **Kartu Profile "AI ENGINE" (Qwen3/Ollama) + banner compliance sengaja TIDAK disentuh** (known-issue narasi grant).

### Gotcha Flutter (pakai ulang)
- `AuthInterceptor.onError` jangan dikontorsi untuk artefak test — `runZonedGuarded` di test, produksi tetap bersih.
- Circular import `client.dart↔auth_controller.dart` AMAN karena referensi di dalam closure provider lazy (no construction cycle).
- `OutlinedButton.icon`/`ElevatedButton.icon` bikin subclass yang TIDAK match `find.byType(OutlinedButton)` (exact-type) → pakai widget plain bila test pakai `find.byType`.
- Wrapper HTTP tipis (login/register/me) diverifikasi `analyze`, BUKAN unit-test (tanpa dep mock-HTTP).
- CI: 26 test Flutter hijau (Backend 22s, Mobile analyze+test 1m6s), analyze bersih.

## 🔴 Blocker
- TIDAK ADA.

## 🎯 Goal berikutnya
- Lanjut UI mobile credential-free di atas backend yang sudah jadi: **DPA UI** (paling bersih), render QR customer, scanner, checkout, briefing 5-analisis.

## 📌 Out-of-scope / deferred non-blocking
- Widget test `RegisterScreen` (gap terbesar, fast-follow), coverage `humanizeError` fallback, assert email/prefix di beberapa test, pill "AI online" di layar auth, flag `clearAccount` tak terpakai. Ledger: `.superpowers/sdd/progress.md`.
- **PENDING (luar repo):** HTTPS/domain VPS + `flutter_secure_storage` minSdk≥18 (cek saat build APK) → `PENDING_EXTERNAL_SETUP.md`.
