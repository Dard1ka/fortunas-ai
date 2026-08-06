import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'auth/auth_controller.dart';
import 'auth/auth_redirect.dart';
import 'auth/auth_state.dart';
import 'screens/briefing_screen.dart';
import 'screens/checkout_screen.dart';
import 'screens/scan_screen.dart';
import 'screens/customer_otp_screen.dart';
import 'screens/customer_phone_screen.dart';
import 'screens/customer_profile_screen.dart';
import 'screens/customer_qr_screen.dart';
import 'screens/customer_home_screen.dart';
import 'screens/customer_points_screen.dart';
import 'screens/customer_promo_screen.dart';
import 'screens/customer_history_screen.dart';
import 'screens/customer_menu_screen.dart';
import 'api/models.dart';
import 'ui/customer_bottom_nav.dart';
import 'screens/dpa_screen.dart';
import 'screens/history_screen.dart';
import 'screens/home_screen.dart';
import 'screens/login_screen.dart';
import 'screens/orders_screen.dart';
import 'screens/products_screen.dart';
import 'screens/public_order_screen.dart';
import 'screens/profile_screen.dart';
import 'screens/register_screen.dart';
import 'screens/result_screen.dart';
import 'screens/splash_screen.dart';
import 'theme/tokens.dart';
import 'ui/adaptive_shell.dart';
import 'ui/bottom_nav.dart';
import 'ui/nav_rail.dart';
import 'voice/voice_flow.dart';

/// Lebar kolom phone-only. Dipertahankan sebagai alias publik — bukan karena
/// ada pemakai lama yang diketahui (repo ini nol; cek sendiri kalau ragu),
/// tapi untuk jaga-jaga kalau ada konsumen yang belum di-push oleh developer
/// lain yang sedang mengedit file ini secara paralel. Nilainya kini hidup di
/// `ui/adaptive_shell.dart`.
const double kPhoneFrameWidth = kPhoneOnlyFrameWidth;

/// Membingkai konten route sesuai viewport.
///
/// **Nama ini sengaja dipertahankan.** Ia dipanggil oleh route builder di
/// bawah, dan dengan mempertahankannya setiap route baru — termasuk yang
/// ditambahkan dev lain — otomatis mendapat perilaku responsif tanpa perlu
/// tahu apa pun soal shell.
///
/// Keputusan phone-vs-adaptif diturunkan dari **path route** (lihat
/// [isPhoneOnlyRoute]), sehingga tidak ada satu baris route pun yang perlu
/// diedit. Logika layout-nya sendiri ada di [AdaptiveShell].
///
/// Ditempatkan DI DALAM route builder (bukan `MaterialApp.builder`) untuk dua
/// alasan yang keduanya keras:
/// 1. Constraint yang masuk sudah bounded, sehingga [AdaptiveShell] bisa memaku
///    tinggi ke `constraints.maxHeight` — tanpa itu child yang **tidak greedy**
///    (mis. `Column(mainAxisSize: min)`) menyusut ke tinggi isinya dan
///    dipusatkan di tengah viewport. (`Scaffold` sendiri kebal: ia memakai
///    `constraints.biggest`. Lihat catatan di `ui/adaptive_shell.dart`.)
/// 2. `GoRouterState.of(context)` di [build] butuh `ModalRoute` route ini di
///    atas context-nya. Di `MaterialApp.builder` — di atas Navigator — ia
///    melempar `GoError`, bukan diam-diam salah.
class PhoneFrame extends StatelessWidget {
  final Widget child;
  const PhoneFrame({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    // Lokasi dibaca lewat `GoRouterState.of(context)`, BUKAN
    // `GoRouter.of(context).state`. Bedanya menentukan benar/salah, bukan gaya:
    //
    // - `GoRouter.state` (go_router 14.8.1 `router.dart:257-264`) adalah
    //   **puncak stack** — "the state of the route that was last used in either
    //   GoRouter.go or GoRouter.push". Setiap PhoneFrame yang sedang berada
    //   DI BAWAH route lain yang di-push akan ikut membaca lokasi route paling
    //   atas, bukan lokasinya sendiri.
    // - `GoRouterState.of(context)` (`state.dart:118`) adalah **per-route** dan
    //   reaktif: ia menelusuri ModalRoute di atas `context` lalu mengambil state
    //   yang terdaftar untuk Page route ITU (`builder.dart:219`), jadi tiap
    //   PhoneFrame membingkai route-nya sendiri.
    //
    // Kenapa ini penting: `login_screen.dart` melakukan
    // `context.push('/customer/login')` dari layar login UMKM, jadi stack
    // dua-dalam lintas-audiens (UMKM di bawah, customer di atas) memang terjadi
    // di app ini. Dengan pembacaan puncak-stack, layar UMKM di bawahnya ikut
    // menyusut ke kolom HP 430px begitu ia dibangun ulang — terukur 840→430
    // pada saat animasi push (lihat `phone_frame_route_test.dart`, grup
    // "stack dua-dalam"). Hari ini itu hanya tidak terlihat karena SEMUA
    // call-site UMKM `const` dan Flutter tidak membangun ulang widget const;
    // route yang membawa nilai runtime (`state.extra`, path/query param) TIDAK
    // BISA `const`, dan route seperti itulah yang paling mungkin ditambahkan
    // berikutnya. Jadi jangan bersandar pada const — bersandar pada baris ini.
    //
    // `maybeOf` dipakai murni sebagai penjaga null: `GoRouterState.of` MELEMPAR
    // GoError kalau tidak ada router di atas context, dan PhoneFrame memang
    // bisa dirender di luar router (mis. dalam widget test). Lokasi kosong
    // diperlakukan sebagai route UMKM.
    final router = GoRouter.maybeOf(context);
    final location = router == null ? '' : GoRouterState.of(context).uri.path;
    // ColoredBox: mengecat gutter di luar kolom framed. Tanpa ini, region di
    // luar kolom 840/720/430px itu tidak dilukis siapa pun — MaterialApp
    // tidak menyisipkan surface root, jadi di mobile region itu clear ke
    // hitam, di web ke warna halaman host. Aman di ketiga cabang
    // AdaptiveShell: compact mengembalikan child penuh (menutupi box ini
    // seluruhnya); phone-only melukis kPhoneOnlyBackdrop di atasnya; shell
    // tab UMKM tidak lewat PhoneFrame sama sekali (Scaffold-nya sendiri
    // sudah mengecat token yang sama).
    return ColoredBox(
      color: FortunasColors.bg,
      child: AdaptiveShell(
        phoneOnly: isPhoneOnlyRoute(location),
        child: child,
      ),
    );
  }
}

/// Provider-backed router with auth gate.
/// Replaces the old top-level `_router` GoRouter instance.
final routerProvider = Provider<GoRouter>((ref) {
  final refresh = ValueNotifier<AuthStatus>(ref.read(authControllerProvider).status);
  ref.listen(authControllerProvider, (_, next) => refresh.value = next.status);
  ref.onDispose(refresh.dispose);

  return GoRouter(
    initialLocation: '/splash',
    refreshListenable: refresh,
    redirect: (context, state) =>
        authRedirect(ref.read(authControllerProvider).status, state.uri.path),
    routes: [
      GoRoute(
        path: '/splash',
        builder: (_, __) => const PhoneFrame(child: SplashScreen()),
      ),
      GoRoute(
        path: '/login',
        builder: (_, __) => const PhoneFrame(child: LoginScreen()),
      ),
      GoRoute(
        path: '/register',
        builder: (_, __) => const PhoneFrame(child: RegisterScreen()),
      ),
      ShellRoute(
        builder: (context, state, child) {
          // Tab utama UMKM. Compact → bottom nav (persis seperti sebelumnya);
          // viewport lebar → rail kiri + konten dibatasi lebar baca.
          final location = state.uri.path;
          return LayoutBuilder(
            builder: (ctx, constraints) {
              final tier = shellTierFor(constraints.maxWidth);
              if (tier == ShellTier.compact) {
                return Scaffold(
                  backgroundColor: FortunasColors.bg,
                  extendBody: true,
                  body: SafeArea(bottom: false, child: child),
                  bottomNavigationBar:
                      FortunasBottomNav(currentLocation: location),
                );
              }
              return Scaffold(
                backgroundColor: FortunasColors.bg,
                body: SafeArea(
                  bottom: false,
                  child: Row(
                    children: [
                      FortunasNavRail(
                        currentLocation: location,
                        extended: tier == ShellTier.expanded,
                      ),
                      Expanded(
                        child: AdaptiveShell(phoneOnly: false, child: child),
                      ),
                    ],
                  ),
                ),
              );
            },
          );
        },
        routes: [
          GoRoute(path: '/',         builder: (_, __) => const HomeScreen()),
          GoRoute(path: '/briefing', builder: (_, __) => const BriefingScreen()),
          GoRoute(path: '/result',   builder: (ctx, st) {
            final q = st.uri.queryParameters['q'] ?? '';
            return ResultScreen(question: q);
          }),
          GoRoute(path: '/history',  builder: (_, __) => const HistoryScreen()),
          GoRoute(path: '/me',       builder: (_, __) => const ProfileScreen()),
        ],
      ),
      GoRoute(
        path: '/voice',
        pageBuilder: (ctx, st) => const MaterialPage(
          fullscreenDialog: true,
          child: PhoneFrame(child: VoiceFlow()),
        ),
      ),
      GoRoute(
        path: '/dpa',
        builder: (_, __) => const PhoneFrame(child: DpaScreen()),
      ),
      GoRoute(
        path: '/checkout',
        builder: (_, __) => const PhoneFrame(child: CheckoutScreen()),
      ),
      GoRoute(
        path: '/products',
        builder: (_, __) => const PhoneFrame(child: ProductsScreen()),
      ),
      GoRoute(
        path: '/orders',
        builder: (_, __) => const PhoneFrame(child: OrdersScreen()),
      ),
      GoRoute(
        path: '/scan',
        builder: (_, __) => const PhoneFrame(child: ScanScreen()),
      ),
      // Alur pesan-publik pelanggan (tanpa akun). Diizinkan tanpa auth —
      // lihat authRedirect (`/order` di-whitelist bersama `/customer/*`).
      GoRoute(
        path: '/order',
        builder: (_, __) => const PhoneFrame(child: PublicOrderScreen()),
      ),
      GoRoute(
        path: '/customer/login',
        builder: (_, __) => const PhoneFrame(child: CustomerPhoneScreen()),
      ),
      GoRoute(
        path: '/customer/otp',
        builder: (ctx, st) =>
            PhoneFrame(child: CustomerOtpScreen(phone: st.extra as String? ?? '')),
      ),
      GoRoute(
        path: '/customer/profile',
        builder: (ctx, st) =>
            PhoneFrame(child: CustomerProfileScreen(phone: st.extra as String? ?? '')),
      ),
      // Customer shell: 5-tab bottom nav (Beranda · Riwayat · QR · Poin · Profil).
      ShellRoute(
        builder: (context, state, child) {
          final location = state.uri.path;
          return PhoneFrame(
            child: Scaffold(
              backgroundColor: FortunasColors.bg,
              extendBody: true,
              body: SafeArea(bottom: false, child: child),
              bottomNavigationBar: CustomerBottomNav(currentLocation: location),
            ),
          );
        },
        routes: [
          GoRoute(path: '/customer/home',    builder: (_, __) => const CustomerHomeScreen()),
          GoRoute(path: '/customer/history', builder: (_, __) => const CustomerHistoryScreen()),
          GoRoute(path: '/customer/qr',      builder: (_, __) => const CustomerQrScreen()),
          GoRoute(path: '/customer/points',  builder: (_, __) => const CustomerPointsScreen()),
          GoRoute(path: '/customer/menu',    builder: (_, __) => const CustomerMenuScreen()),
        ],
      ),
      GoRoute(
        path: '/customer/promo',
        builder: (ctx, st) {
          final m = st.extra;
          if (m is MembershipSummary) {
            return PhoneFrame(child: CustomerPromoScreen(membership: m));
          }
          // Fallback jika dibuka tanpa argumen membership.
          return const PhoneFrame(child: CustomerHomeScreen());
        },
      ),
    ],
  );
});

/// Root app widget. Bootstraps auth on first launch and drives navigation
/// via [routerProvider] which gates routes based on [AuthStatus].
///
/// Mirrors the React `App.jsx` router shape:
///   /             → HomeScreen
///   /briefing     → BriefingScreen
///   /result?q=... → ResultScreen
///   /history      → HistoryScreen
///   /me           → ProfileScreen
///   /splash       → SplashScreen (auth resolving)
///   /login        → LoginScreen
///   /register     → RegisterScreen
///
/// VoiceFlow is shown as a full-screen modal route (`/voice`) — Flutter
/// equivalent of the React overlay pattern in App.jsx.
class FortunasApp extends ConsumerStatefulWidget {
  const FortunasApp({super.key});

  @override
  ConsumerState<FortunasApp> createState() => _FortunasAppState();
}

class _FortunasAppState extends ConsumerState<FortunasApp> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() => ref.read(authControllerProvider.notifier).bootstrap());
  }

  @override
  Widget build(BuildContext context) {
    final router = ref.watch(routerProvider);
    return MaterialApp.router(
      title: 'Fortunas AI',
      debugShowCheckedModeBanner: false,
      theme: buildFortunasTheme(),
      routerConfig: router,
    );
  }
}
