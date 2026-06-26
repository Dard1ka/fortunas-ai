import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/api/client.dart';
import 'package:fortunas_ai/api/models.dart';
import 'package:fortunas_ai/screens/briefing_screen.dart';

import '../support/fakes.dart';

BriefingSection _section(String type, String label) => BriefingSection(
      analysisType: type,
      label: label,
      status: 'success',
      summary: '$label ringkasan.',
      topFindings: ['$label temuan teratas'],
      recommendation: ['$label rekomendasi'],
      rowCount: 12,
    );

DailyReportResponse _fiveSections() => DailyReportResponse(
      status: 'success',
      message: 'ok',
      latest: DailyReportEntry(
        generatedAt: '2026-06-26T08:00:00',
        date: '2026-06-26',
        executiveSummary: 'Ringkasan eksekutif harian.',
        sections: [
          _section('repeat_customer', 'Loyal'),
          _section('high_value_customer', 'Bernilai'),
          _section('peak_hour', 'Jam Ramai'),
          _section('bundle_opportunity', 'Bundling'),
          _section('top_product', 'Terlaris'),
        ],
      ),
      history: const [],
    );

Future<void> _pump(WidgetTester tester, DailyReportResponse resp) async {
  final api = FakeApi()..reportResult = resp;
  await tester.pumpWidget(ProviderScope(
    overrides: [apiProvider.overrideWithValue(api)],
    child: const MaterialApp(home: Scaffold(body: BriefingScreen())),
  ));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('renders all 5 section labels (no take(4) truncation)',
      (tester) async {
    await _pump(tester, _fiveSections());
    expect(find.text('LOYAL'), findsOneWidget);
    expect(find.text('BERNILAI'), findsOneWidget);
    expect(find.text('JAM RAMAI'), findsOneWidget);
    expect(find.text('BUNDLING'), findsOneWidget);
    expect(find.text('TERLARIS'), findsOneWidget); // 5th — dropped before fix
    expect(find.text('5 analisis selesai.'), findsOneWidget);
  });

  testWidgets('top_product card uses the flame icon', (tester) async {
    await _pump(tester, _fiveSections());
    expect(find.byIcon(Icons.local_fire_department_outlined), findsOneWidget);
  });

  testWidgets('odd trailing card spans full width (wider than a paired card)',
      (tester) async {
    await _pump(tester, _fiveSections());
    // _KpiCard root is the nearest Container ancestor of its uppercased label.
    final terlarisCard = find
        .ancestor(of: find.text('TERLARIS'), matching: find.byType(Container))
        .first;
    final loyalCard = find
        .ancestor(of: find.text('LOYAL'), matching: find.byType(Container))
        .first;
    final terlarisWidth = tester.getSize(terlarisCard).width;
    final loyalWidth = tester.getSize(loyalCard).width;
    // Paired cards take ~half the row; the singleton spans the full row.
    expect(terlarisWidth, greaterThan(loyalWidth * 1.5));
  });

  testWidgets('empty state shows placeholder copy', (tester) async {
    await _pump(
      tester,
      DailyReportResponse(
        status: 'empty',
        message: 'kosong',
        latest: null,
        history: const [],
      ),
    );
    expect(find.text('Belum ada briefing tersimpan'), findsOneWidget);
  });
}
