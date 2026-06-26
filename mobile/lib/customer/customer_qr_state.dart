import '../api/models.dart';

class CustomerQrState {
  final QrSessionResponse? session;
  final bool loading;
  final String? errorMessage;

  const CustomerQrState({this.session, this.loading = false, this.errorMessage});

  bool get hasQr => session != null && session!.qrToken.isNotEmpty;

  CustomerQrState copyWith({
    QrSessionResponse? session,
    bool? loading,
    String? errorMessage,
    bool clearError = false,
    bool clearSession = false,
  }) {
    return CustomerQrState(
      session: clearSession ? null : (session ?? this.session),
      loading: loading ?? this.loading,
      errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
    );
  }
}
