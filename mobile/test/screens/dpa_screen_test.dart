import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/api/models.dart';
import 'package:fortunas_ai/dpa/dpa_controller.dart';
import 'package:fortunas_ai/dpa/dpa_state.dart';
import 'package:fortunas_ai/screens/dpa_screen.dart';

class SpyDpaController extends DpaController {
  SpyDpaController(this._initial);
  final DpaState _initial;
  int saveCalls = 0;
  String? lastPassword;

  @override
  DpaState build() => _initial;
  @override
  Future<void> load() async {} // no-op: keep the seeded initial state
  @override
  Future<bool> save(String password) async {
    saveCalls++;
    lastPassword = password;
    return true;
  }
}

Future<void> _pump(WidgetTester tester, DpaState initial,
    {SpyDpaController? spy}) async {
  final controller = spy ?? SpyDpaController(initial);
  await tester.pumpWidget(ProviderScope(
    overrides: [dpaControllerProvider.overrideWith(() => controller)],
    child: const MaterialApp(home: DpaScreen()),
  ));
  await tester.pump();
}

void main() {
  testWidgets('empty state shows onboarding CTA', (tester) async {
    await _pump(tester, const DpaState());
    expect(find.byKey(const Key('dpa_setup_cta')), findsOneWidget);
    expect(find.text('Atur Pagar AI'), findsOneWidget);
  });

  testWidgets('read mode renders forbidden chips + Edit button', (tester) async {
    await _pump(
      tester,
      const DpaState(
        payload: DpaPayload(forbiddenRules: ['rokok'], version: 1),
      ),
    );
    expect(find.text('rokok'), findsOneWidget);
    expect(find.byKey(const Key('dpa_edit_button')), findsOneWidget);
  });

  testWidgets('edit mode: typing + Tambah adds a chip', (tester) async {
    await _pump(tester, const DpaState(editing: true));
    await tester.enterText(find.byKey(const Key('dpa_forbidden_input')), 'rokok');
    await tester.tap(find.byKey(const Key('dpa_forbidden_add')));
    await tester.pump();
    expect(find.text('rokok'), findsOneWidget);
  });

  testWidgets('save with empty password shows validation, not called', (tester) async {
    final spy = SpyDpaController(const DpaState(editing: true));
    await _pump(tester, const DpaState(editing: true), spy: spy);
    await tester.tap(find.byKey(const Key('dpa_save')));
    await tester.pump();
    expect(find.text('Password wajib diisi'), findsOneWidget);
    expect(spy.saveCalls, 0);
  });

  testWidgets('valid save calls controller.save with password', (tester) async {
    final spy = SpyDpaController(const DpaState(editing: true));
    await _pump(tester, const DpaState(editing: true), spy: spy);
    await tester.enterText(find.byKey(const Key('dpa_password')), 'secret');
    await tester.tap(find.byKey(const Key('dpa_save')));
    await tester.pump();
    expect(spy.saveCalls, 1);
    expect(spy.lastPassword, 'secret');
  });
}
