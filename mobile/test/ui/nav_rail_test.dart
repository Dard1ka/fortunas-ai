import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/theme/tokens.dart';
import 'package:fortunas_ai/ui/nav_rail.dart';
import 'package:fortunas_ai/ui/nav_spec.dart';

/// Warna [Material] pembungkus slot `rail_$id` — ini adalah sinyal render
/// nyata dari status aktif ([FortunasColors.violetSoft] vs transparan),
/// bukan nilai [NavSpec] atau argumen yang dilewatkan ke widget.
Color _railSlotMaterialColor(WidgetTester tester, String id) {
  final finder = find.ancestor(
    of: find.byKey(Key('rail_$id')),
    matching: find.byType(Material),
  );
  return tester.widget<Material>(finder.first).color!;
}

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

  testWidgets(
      'FAB tidak kolaps ke ukuran isi di rail sempit (lebar eksplisit)',
      (tester) async {
    await _pump(tester, location: '/', extended: false);
    // Target eksplisit di kode adalah 52 (menyamai _MicFab di
    // bottom_nav.dart), tapi inset border kanan rail (nav_rail.dart:41,
    // 1.5px — otomatis jadi padding lewat BoxDecoration.padding) memangkas
    // slot yang tersedia: kNavRailWidth(76) - 1.5 - padding horizontal FAB
    // (12*2) = 50.5. Nilai ini mengunci hasil render nyata; ia akan gagal
    // bila FAB kolaps ke lebar isi (jauh di bawah 50.5) ataupun bila
    // lebarnya diam-diam melebihi slot yang tersedia.
    expect(tester.getSize(find.byKey(const Key('rail_voice_fab'))).width,
        50.5);
  });

  testWidgets('tab aktif mengikuti navItemIsActive (/result milik tab /)',
      (tester) async {
    await _pump(tester, location: '/result', extended: true);
    // '/result' adalah kelanjutan tab '/' (home) — slotnya harus tersorot
    // violetSoft. '/briefing' bukan tab aktif — slotnya harus tetap
    // transparan. Ini mengecek _RailItem yang benar-benar dirender oleh
    // FortunasNavRail (nav_rail.dart:56), bukan navItemIsActive terisolasi
    // (sudah jadi cakupan Task 1 di nav_spec_test.dart).
    expect(_railSlotMaterialColor(tester, 'home'), FortunasColors.violetSoft);
    expect(_railSlotMaterialColor(tester, 'briefing'), Colors.transparent);
  });
}
