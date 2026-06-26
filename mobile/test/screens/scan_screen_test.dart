import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/api/client.dart';
import 'package:fortunas_ai/api/models.dart';
import 'package:fortunas_ai/screens/scan_screen.dart';

import '../support/fakes.dart';

Future<void> _pump(WidgetTester tester, FakeApi api) async {
  await tester.pumpWidget(ProviderScope(
    overrides: [apiProvider.overrideWithValue(api)],
    child: const MaterialApp(home: ScanScreen()),
  ));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('valid scan shows member result; scan again resets', (tester) async {
    final api = FakeApi()
      ..scanValidateResult = const QrValidateResponse(
          valid: true, customerUserId: 'C1', username: 'Sari', isNewMember: true);
    await _pump(tester, api);
    await tester.enterText(find.byKey(const Key('scan_token')), 'qr-token');
    await tester.pump();
    await tester.tap(find.byKey(const Key('scan_submit')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('scan_result')), findsOneWidget);
    expect(find.textContaining('Sari'), findsOneWidget);
    await tester.tap(find.byKey(const Key('scan_again')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('scan_token')), findsOneWidget);
    expect(find.byKey(const Key('scan_result')), findsNothing);
  });

  testWidgets('invalid (valid=false) shows reason, not scan_error', (tester) async {
    final api = FakeApi()
      ..scanValidateResult = const QrValidateResponse(valid: false, reason: 'expired');
    await _pump(tester, api);
    await tester.enterText(find.byKey(const Key('scan_token')), 'qr-token');
    await tester.pump();
    await tester.tap(find.byKey(const Key('scan_submit')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('scan_result')), findsOneWidget);
    expect(find.textContaining('kadaluarsa'), findsOneWidget);
    expect(find.byKey(const Key('scan_error')), findsNothing);
  });

  testWidgets('exception shows scan_error, token field stays', (tester) async {
    final api = FakeApi()..scanValidateError = Exception('503');
    await _pump(tester, api);
    await tester.enterText(find.byKey(const Key('scan_token')), 'qr-token');
    await tester.pump();
    await tester.tap(find.byKey(const Key('scan_submit')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('scan_error')), findsOneWidget);
    expect(find.byKey(const Key('scan_token')), findsOneWidget);
    expect(find.byKey(const Key('scan_result')), findsNothing);
  });
}
