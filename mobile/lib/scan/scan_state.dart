import '../api/models.dart';

class ScanState {
  final QrValidateResponse? result;
  final bool submitting;
  final String? errorMessage;

  const ScanState({this.result, this.submitting = false, this.errorMessage});

  bool get hasResult => result != null;

  ScanState copyWith({
    QrValidateResponse? result,
    bool? submitting,
    String? errorMessage,
    bool clearResult = false,
    bool clearError = false,
  }) {
    return ScanState(
      result: clearResult ? null : (result ?? this.result),
      submitting: submitting ?? this.submitting,
      errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
    );
  }
}
