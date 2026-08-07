// `phone_frame_route_test.dart` proves `PhoneFrame` itself is route-aware,
// but it pumps a synthetic minimal router — it never exercises the real
// `ShellRoute` builder wired up inside `routerProvider` in app.dart (the
// second region Task 4 touches: tier switch + FortunasNavRail + Row).
// `FortunasNavRail`, `AdaptiveShell`, and `shellTierFor` each have their own
// unit tests elsewhere, but the glue that wires them into the UMKM tab shell
// had zero coverage. This file exercises the actual `routerProvider` (not a
// duplicate of its logic) so a regression in that wiring goes red here.
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/api/client.dart';
import 'package:fortunas_ai/api/models.dart';
import 'package:fortunas_ai/app.dart';
import 'package:fortunas_ai/auth/auth_controller.dart';
import 'package:fortunas_ai/auth/auth_state.dart';
import 'package:fortunas_ai/screens/home_screen.dart';
import 'package:fortunas_ai/ui/adaptive_shell.dart';
import 'package:fortunas_ai/ui/bottom_nav.dart';
import 'package:fortunas_ai/ui/nav_rail.dart';

import '../support/fakes.dart';

/// Sudah authenticated sejak awal — melewati /splash tanpa memanggil API asli.
class _AuthedController extends AuthController {
  @override
  AuthState build() => const AuthState(
        status: AuthStatus.authenticated,
        account: UmkmAccount(
          email: 'budi@toko.id',
          tenantName: 'Toko Budi',
          tablePrefix: 'toko_budi',
        ),
      );
}

Future<void> _pumpUmkmShell(WidgetTester tester, Size size) async {
  tester.view.devicePixelRatio = 1.0;
  tester.view.physicalSize = size;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(ProviderScope(
    overrides: [
      authControllerProvider.overrideWith(() => _AuthedController()),
      apiProvider.overrideWithValue(FakeApi()),
    ],
    child: Consumer(
      builder: (context, ref, _) =>
          MaterialApp.router(routerConfig: ref.watch(routerProvider)),
    ),
  ));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets(
      'shell UMKM di viewport lebar (1440) pakai FortunasNavRail extended dan konten 840',
      (tester) async {
    await _pumpUmkmShell(tester, const Size(1440, 900));
    expect(find.byType(FortunasNavRail), findsOneWidget);
    expect(find.byType(FortunasBottomNav), findsNothing);
    // Pin `extended: tier == ShellTier.expanded` — di 1440 (expanded) rail
    // harus lebar 200 (ikon + label), bukan 76 (ikon saja).
    expect(tester.getSize(find.byKey(const Key('nav_rail'))).width,
        kNavRailExtendedWidth);
    // Pin `AdaptiveShell(phoneOnly: false, ...)` — kalau ini diam-diam jadi
    // true, konten jadi strip 430 di samping rail 200 pada viewport 1440,
    // persis kegagalan yang dilarang requirement utama.
    expect(
        tester.getSize(find.byType(HomeScreen)).width, kExpandedContentWidth);
  });

  testWidgets(
      'shell UMKM di viewport medium (600, ambang bawah) pakai rail ikon-saja (76), tidak extended',
      (tester) async {
    await _pumpUmkmShell(tester, const Size(600, 900));
    expect(find.byType(FortunasNavRail), findsOneWidget);
    expect(find.byType(FortunasBottomNav), findsNothing);
    // Pin sisi lain dari `extended: tier == ShellTier.expanded` — di 600
    // (medium, persis di ambang bawahnya) rail harus TETAP 76, bukan 200.
    expect(
        tester.getSize(find.byKey(const Key('nav_rail'))).width, kNavRailWidth);
  });

  testWidgets(
      'shell UMKM di viewport sempit (390) tetap pakai FortunasBottomNav (regresi)',
      (tester) async {
    await _pumpUmkmShell(tester, const Size(390, 844));
    expect(find.byType(FortunasBottomNav), findsOneWidget);
    expect(find.byType(FortunasNavRail), findsNothing);
  });
}
