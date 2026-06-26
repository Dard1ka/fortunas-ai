import '../api/models.dart';

/// Immutable UI state for the DPA screen.
/// - read mode: [payload] populated, [editing] false.
/// - edit mode: [editing] true, drafts hold the in-progress edit.
class DpaState {
  final bool loading;
  final DpaPayload? payload;
  final bool editing;
  final String draftRawText;
  final List<String> draftAllowed;
  final List<String> draftForbidden;
  final bool submitting;
  final String? errorMessage;
  final String? loadError;

  const DpaState({
    this.loading = false,
    this.payload,
    this.editing = false,
    this.draftRawText = '',
    this.draftAllowed = const [],
    this.draftForbidden = const [],
    this.submitting = false,
    this.errorMessage,
    this.loadError,
  });

  /// True when no policy has ever been saved (server returns version 0).
  bool get isEmpty => (payload?.version ?? 0) == 0;

  DpaState copyWith({
    bool? loading,
    DpaPayload? payload,
    bool? editing,
    String? draftRawText,
    List<String>? draftAllowed,
    List<String>? draftForbidden,
    bool? submitting,
    String? errorMessage,
    String? loadError,
    bool clearError = false,
    bool clearLoadError = false,
  }) {
    return DpaState(
      loading: loading ?? this.loading,
      payload: payload ?? this.payload,
      editing: editing ?? this.editing,
      draftRawText: draftRawText ?? this.draftRawText,
      draftAllowed: draftAllowed ?? this.draftAllowed,
      draftForbidden: draftForbidden ?? this.draftForbidden,
      submitting: submitting ?? this.submitting,
      errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
      loadError: clearLoadError ? null : (loadError ?? this.loadError),
    );
  }
}
