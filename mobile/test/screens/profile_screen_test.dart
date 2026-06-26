import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/api/client.dart';
import 'package:fortunas_ai/api/models.dart';
import 'package:fortunas_ai/auth/auth_controller.dart';
import 'package:fortunas_ai/auth/auth_state.dart';
import 'package:fortunas_ai/screens/profile_screen.dart';

import '../support/fakes.dart';

class AuthedSpyController extends AuthController {
  int logoutCalls = 0;
  @override
  AuthState build() => const AuthState(
        status: AuthStatus.authenticated,
        account: UmkmAccount(
          email: 'budi@toko.id',
          tenantName: 'Toko Budi',
          tablePrefix: 'toko_budi',
        ),
      );
  @override
  Future<void> logout() async {
    logoutCalls++;
  }
}

void main() {
  testWidgets('shows account fields + Keluar button', (tester) async {
    final spy = AuthedSpyController();
    final api = FakeApi()..meResult = const UmkmAccount();
    await tester.pumpWidget(ProviderScope(
      overrides: [
        authControllerProvider.overrideWith(() => spy),
        apiProvider.overrideWithValue(api),
      ],
      child: const MaterialApp(home: ProfileScreen()),
    ));
    await tester.pump();
    expect(find.text('Toko Budi'), findsOneWidget);
    expect(find.text('budi@toko.id'), findsOneWidget);
    expect(find.widgetWithText(OutlinedButton, 'Keluar'), findsOneWidget);
  });

  testWidgets('tapping Keluar calls logout', (tester) async {
    final spy = AuthedSpyController();
    final api = FakeApi()..meResult = const UmkmAccount();
    await tester.pumpWidget(ProviderScope(
      overrides: [
        authControllerProvider.overrideWith(() => spy),
        apiProvider.overrideWithValue(api),
      ],
      child: const MaterialApp(home: ProfileScreen()),
    ));
    await tester.pump();
    await tester.tap(find.widgetWithText(OutlinedButton, 'Keluar'));
    await tester.pump();
    expect(spy.logoutCalls, 1);
  });
}
