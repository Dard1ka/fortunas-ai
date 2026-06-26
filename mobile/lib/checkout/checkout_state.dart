import '../api/models.dart';

/// Immutable UI state for the Checkout (Kasir) screen.
/// - form mode: [result] is null.
/// - success mode: [result] populated after a confirmed checkout.
class CheckoutState {
  final List<CheckoutLineItem> items;
  final bool submitting;
  final CheckoutConfirmResponse? result;
  final String? errorMessage;

  const CheckoutState({
    this.items = const [],
    this.submitting = false,
    this.result,
    this.errorMessage,
  });

  CheckoutState copyWith({
    List<CheckoutLineItem>? items,
    bool? submitting,
    CheckoutConfirmResponse? result,
    String? errorMessage,
    bool clearResult = false,
    bool clearError = false,
  }) {
    return CheckoutState(
      items: items ?? this.items,
      submitting: submitting ?? this.submitting,
      result: clearResult ? null : (result ?? this.result),
      errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
    );
  }
}
