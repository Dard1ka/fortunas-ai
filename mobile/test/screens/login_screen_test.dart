import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fortunas_ai/auth/auth_controller.dart';
import 'package:fortunas_ai/screens/login_screen.dart';

class SpyAuthController extends AuthController {
  int loginCalls = 0;
  String? lastEmail;
  @override
  Future<bool> login(String email, String password) async {
    loginCalls++;
    lastEmail = email;
    return true;
  }
}

void main() {
  testWidgets('renders email + password fields and Masuk button', (tester) async {
    final spy = SpyAuthController();
    await tester.pumpWidget(ProviderScope(
      overrides: [authControllerProvider.overrideWith(() => spy)],
      child: const MaterialApp(home: LoginScreen()),
    ));
    expect(find.byType(TextFormField), findsNWidgets(2));
    expect(find.widgetWithText(ElevatedButton, 'Masuk'), findsOneWidget);
  });

  testWidgets('empty submit shows validation, does not call controller', (tester) async {
    final spy = SpyAuthController();
    await tester.pumpWidget(ProviderScope(
      overrides: [authControllerProvider.overrideWith(() => spy)],
      child: const MaterialApp(home: LoginScreen()),
    ));
    await tester.tap(find.widgetWithText(ElevatedButton, 'Masuk'));
    await tester.pump();
    expect(spy.loginCalls, 0);
    expect(find.text('Email wajib diisi'), findsOneWidget);
  });

  testWidgets('valid submit calls controller.login with email', (tester) async {
    final spy = SpyAuthController();
    await tester.pumpWidget(ProviderScope(
      overrides: [authControllerProvider.overrideWith(() => spy)],
      child: const MaterialApp(home: LoginScreen()),
    ));
    await tester.enterText(find.byKey(const Key('login_email')), 'a@b.id');
    await tester.enterText(find.byKey(const Key('login_password')), 'secret');
    await tester.tap(find.widgetWithText(ElevatedButton, 'Masuk'));
    await tester.pump();
    expect(spy.loginCalls, 1);
    expect(spy.lastEmail, 'a@b.id');
  });
}
