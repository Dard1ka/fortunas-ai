import '../api/models.dart';

enum AuthStatus { unknown, unauthenticated, authenticated }

class AuthState {
  final AuthStatus status;
  final UmkmAccount? account;
  final bool submitting;
  final String? errorMessage;

  const AuthState({
    this.status = AuthStatus.unknown,
    this.account,
    this.submitting = false,
    this.errorMessage,
  });

  AuthState copyWith({
    AuthStatus? status,
    UmkmAccount? account,
    bool? submitting,
    String? errorMessage,
    bool clearError = false,
    bool clearAccount = false,
  }) {
    return AuthState(
      status: status ?? this.status,
      account: clearAccount ? null : (account ?? this.account),
      submitting: submitting ?? this.submitting,
      errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
    );
  }
}
