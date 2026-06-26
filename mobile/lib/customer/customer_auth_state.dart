import '../api/models.dart';

class CustomerAuthState {
  final CustomerProfile? profile;
  final bool submitting;
  final String? errorMessage;

  const CustomerAuthState({this.profile, this.submitting = false, this.errorMessage});

  bool get loggedIn => profile != null;

  CustomerAuthState copyWith({
    CustomerProfile? profile,
    bool? submitting,
    String? errorMessage,
    bool clearProfile = false,
    bool clearError = false,
  }) {
    return CustomerAuthState(
      profile: clearProfile ? null : (profile ?? this.profile),
      submitting: submitting ?? this.submitting,
      errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
    );
  }
}
