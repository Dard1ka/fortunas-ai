import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'screens/home_screen.dart';
import 'screens/briefing_screen.dart';
import 'screens/result_screen.dart';
import 'screens/history_screen.dart';
import 'screens/profile_screen.dart';
import 'theme/tokens.dart';
import 'ui/bottom_nav.dart';
import 'voice/voice_flow.dart';

/// Phone-width used to frame the mobile UI on wide viewports.
const double kPhoneFrameWidth = 430.0;

/// Frames its [child] in a centered phone-width column on wide viewports
/// (web / desktop / tablet) so the mobile UI matches the design mockup
/// instead of stretching edge-to-edge.
///
/// Placed INSIDE route builders (not MaterialApp.builder) so the incoming
/// constraints are tight/bounded — guaranteeing the child fills the full
/// viewport height (otherwise the Scaffold collapses and the bottom nav
/// floats in the middle).
class PhoneFrame extends StatelessWidget {
  final Widget child;
  const PhoneFrame({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (ctx, constraints) {
        // Real phone (narrow): render full-screen, no frame.
        if (constraints.maxWidth <= kPhoneFrameWidth) return child;

        // Wide viewport: center a phone-width column at full viewport height.
        return ColoredBox(
          color: const Color(0xFFE9E4D8), // backdrop around the phone frame
          child: Center(
            child: SizedBox(
              width: kPhoneFrameWidth,
              height: constraints.maxHeight,
              child: ClipRect(child: child),
            ),
          ),
        );
      },
    );
  }
}

/// Root app. Mirrors the React `App.jsx` router shape:
///   /             → HomeScreen
///   /briefing     → BriefingScreen
///   /result?q=... → ResultScreen
///   /history      → HistoryScreen
///   /me           → ProfileScreen
///
/// VoiceFlow is shown as a full-screen modal route (`/voice`) — Flutter
/// equivalent of the React overlay pattern in App.jsx.
class FortunasApp extends StatelessWidget {
  const FortunasApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'Fortunas AI',
      debugShowCheckedModeBanner: false,
      theme: buildFortunasTheme(),
      routerConfig: _router,
    );
  }
}

final GoRouter _router = GoRouter(
  initialLocation: '/',
  routes: [
    ShellRoute(
      builder: (context, state, child) {
        // Wrap every primary tab in a Scaffold that owns the bottom nav.
        // VoiceFlow does NOT use this shell — it's a top-level route below.
        final location = state.uri.path;
        return PhoneFrame(
          child: Scaffold(
            backgroundColor: FortunasColors.bg,
            extendBody: true,
            body: SafeArea(bottom: false, child: child),
            bottomNavigationBar: FortunasBottomNav(currentLocation: location),
          ),
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
      pageBuilder: (ctx, st) => MaterialPage(
        fullscreenDialog: true,
        child: const PhoneFrame(child: VoiceFlow()),
      ),
    ),
  ],
);
