import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/client.dart';
import '../api/errors.dart';
import '../api/models.dart';
import 'dpa_rules.dart';
import 'dpa_state.dart';

class DpaController extends Notifier<DpaState> {
  @override
  DpaState build() => const DpaState();

  FortunasApi get _api => ref.read(apiProvider);

  Future<void> load() async {
    state = state.copyWith(
      loading: true,
      clearLoadError: true,
      clearError: true,
      draftRawText: '',
      draftAllowed: const [],
      draftForbidden: const [],
    );
    try {
      final payload = await _api.getDpa();
      state = state.copyWith(loading: false, payload: payload, editing: false);
    } catch (e) {
      state = state.copyWith(loading: false, loadError: humanizeError(e));
    }
  }

  void startEdit() {
    final p = state.payload ?? const DpaPayload();
    state = state.copyWith(
      editing: true,
      draftRawText: p.rawText,
      draftAllowed: List<String>.from(p.allowedRules),
      draftForbidden: List<String>.from(p.forbiddenRules),
      clearError: true,
    );
  }

  void cancelEdit() => state = state.copyWith(editing: false, clearError: true);

  void setRawText(String value) => state = state.copyWith(draftRawText: value);

  void addAllowed(String value) =>
      state = state.copyWith(draftAllowed: addRule(state.draftAllowed, value));

  void removeAllowed(int index) =>
      state = state.copyWith(draftAllowed: removeRuleAt(state.draftAllowed, index));

  void addForbidden(String value) =>
      state = state.copyWith(draftForbidden: addRule(state.draftForbidden, value));

  void removeForbidden(int index) =>
      state = state.copyWith(draftForbidden: removeRuleAt(state.draftForbidden, index));

  Future<bool> save(String password) async {
    state = state.copyWith(submitting: true, clearError: true);
    try {
      final updated = await _api.updateDpa(DpaUpdateRequest(
        rawText: state.draftRawText,
        allowedRules: state.draftAllowed,
        forbiddenRules: state.draftForbidden,
        password: password,
      ));
      state = state.copyWith(submitting: false, payload: updated, editing: false);
      return true;
    } catch (e) {
      state = state.copyWith(submitting: false, errorMessage: humanizeError(e));
      return false;
    }
  }
}

final dpaControllerProvider =
    NotifierProvider<DpaController, DpaState>(DpaController.new);
