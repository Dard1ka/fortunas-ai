// Smoke test for the Flutter test harness.
//
// The default counter-template test was removed — it referenced a non-existent
// `MyApp` (this app's root widget is `FortunasApp`, see lib/main.dart) and made
// `flutter analyze` fail. We keep a minimal sanity test here so `flutter test`
// stays green; real widget tests for FortunasApp screens are a follow-up
// (pumping the full app needs provider/plugin/router test scaffolding).

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('test harness sanity', (WidgetTester tester) async {
    await tester.pumpWidget(
      const MaterialApp(home: Scaffold(body: SizedBox.shrink())),
    );
    expect(find.byType(Scaffold), findsOneWidget);
  });
}
