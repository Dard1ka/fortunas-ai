import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/ui/nav_rail.dart';
import 'package:fortunas_ai/ui/nav_spec.dart';

Future<void> _pump(WidgetTester tester,
    {required String location, required bool extended}) async {
  tester.view.devicePixelRatio = 1.0;
  tester.view.physicalSize = const Size(1440, 900);
  addTearDown(tester.view.reset);
  await tester.pumpWidget(MaterialApp(
    home: Scaffold(
      body: Row(children: [
        FortunasNavRail(currentLocation: location, extended: extended),
        const Expanded(child: SizedBox.shrink()),
      ]),
    ),
  ));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('rail sempit: satu tombol per slot, label disembunyikan',
      (tester) async {
    await _pump(tester, location: '/', extended: false);
    for (final item in kUmkmNavItems) {
      expect(find.byKey(Key('rail_${item.id}')), findsOneWidget,
          reason: item.id);
    }
    // Label hanya muncul di mode extended.
    expect(find.text('Briefing'), findsNothing);
    expect(tester.getSize(find.byKey(const Key('nav_rail'))).width,
        kNavRailWidth);
  });

  testWidgets('rail extended: label tampil dan lebih lebar', (tester) async {
    await _pump(tester, location: '/', extended: true);
    expect(find.text('Briefing'), findsOneWidget);
    expect(find.text('Riwayat'), findsOneWidget);
    expect(tester.getSize(find.byKey(const Key('nav_rail'))).width,
        kNavRailExtendedWidth);
  });

  testWidgets('slot voice dirender sebagai mic FAB, bukan tab biasa',
      (tester) async {
    await _pump(tester, location: '/', extended: false);
    expect(find.byKey(const Key('rail_voice_fab')), findsOneWidget);
  });

  testWidgets('tab aktif mengikuti navItemIsActive (/result milik tab /)',
      (tester) async {
    await _pump(tester, location: '/result', extended: true);
    final active = tester.widget<FortunasNavRail>(
        find.byType(FortunasNavRail));
    expect(navItemIsActive('/', active.currentLocation), isTrue);
    expect(navItemIsActive('/briefing', active.currentLocation), isFalse);
  });
}
