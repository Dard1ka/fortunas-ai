import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/client.dart';
import '../api/errors.dart';
import '../api/models.dart';

/// Controllers untuk fitur loyalty customer: Home, Points, Promo.
/// Pola mengikuti customer_qr_controller.dart (AutoDisposeNotifier, load→state).

// ── Home ─────────────────────────────────────────────────────────
class CustomerHomeState {
  final bool loading;
  final CustomerHomeResponse? home;
  final String? errorMessage;
  const CustomerHomeState({this.loading = false, this.home, this.errorMessage});

  CustomerHomeState copyWith(
          {bool? loading, CustomerHomeResponse? home, String? errorMessage, bool clearError = false}) =>
      CustomerHomeState(
        loading: loading ?? this.loading,
        home: home ?? this.home,
        errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
      );
}

class CustomerHomeController extends AutoDisposeNotifier<CustomerHomeState> {
  @override
  CustomerHomeState build() => const CustomerHomeState();

  Future<void> load() async {
    state = state.copyWith(loading: true, clearError: true);
    try {
      final home = await ref.read(apiProvider).customerHome();
      state = state.copyWith(loading: false, home: home);
    } catch (e) {
      state = state.copyWith(loading: false, errorMessage: humanizeError(e));
    }
  }
}

final customerHomeControllerProvider =
    NotifierProvider.autoDispose<CustomerHomeController, CustomerHomeState>(
        CustomerHomeController.new);

// ── Points ───────────────────────────────────────────────────────
class CustomerPointsState {
  final bool loading;
  final PointsBalanceResponse? points;
  final String? errorMessage;
  const CustomerPointsState({this.loading = false, this.points, this.errorMessage});

  CustomerPointsState copyWith(
          {bool? loading, PointsBalanceResponse? points, String? errorMessage, bool clearError = false}) =>
      CustomerPointsState(
        loading: loading ?? this.loading,
        points: points ?? this.points,
        errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
      );
}

class CustomerPointsController extends AutoDisposeNotifier<CustomerPointsState> {
  @override
  CustomerPointsState build() => const CustomerPointsState();

  Future<void> load() async {
    state = state.copyWith(loading: true, clearError: true);
    try {
      final p = await ref.read(apiProvider).customerPoints();
      state = state.copyWith(loading: false, points: p);
    } catch (e) {
      state = state.copyWith(loading: false, errorMessage: humanizeError(e));
    }
  }
}

final customerPointsControllerProvider =
    NotifierProvider.autoDispose<CustomerPointsController, CustomerPointsState>(
        CustomerPointsController.new);

// ── Promo ────────────────────────────────────────────────────────
class CustomerPromoState {
  final bool loading;
  final bool generating;
  final List<PromoInstance> promos;
  final PromoGenerateResponse? lastGenerated; // untuk animasi spin
  final String? errorMessage;
  const CustomerPromoState({
    this.loading = false,
    this.generating = false,
    this.promos = const [],
    this.lastGenerated,
    this.errorMessage,
  });

  CustomerPromoState copyWith({
    bool? loading,
    bool? generating,
    List<PromoInstance>? promos,
    PromoGenerateResponse? lastGenerated,
    String? errorMessage,
    bool clearError = false,
    bool clearGenerated = false,
  }) =>
      CustomerPromoState(
        loading: loading ?? this.loading,
        generating: generating ?? this.generating,
        promos: promos ?? this.promos,
        lastGenerated: clearGenerated ? null : (lastGenerated ?? this.lastGenerated),
        errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
      );
}

class CustomerPromoController extends AutoDisposeNotifier<CustomerPromoState> {
  @override
  CustomerPromoState build() => const CustomerPromoState();

  Future<void> load() async {
    state = state.copyWith(loading: true, clearError: true);
    try {
      final list = await ref.read(apiProvider).customerPromos();
      state = state.copyWith(loading: false, promos: list.promos);
    } catch (e) {
      state = state.copyWith(loading: false, errorMessage: humanizeError(e));
    }
  }

  /// Generate promo untuk [tenantId]. Return response (untuk trigger spin) atau null bila gagal.
  Future<PromoGenerateResponse?> generate(int tenantId) async {
    state = state.copyWith(generating: true, clearError: true, clearGenerated: true);
    try {
      final resp = await ref
          .read(apiProvider)
          .customerGeneratePromo(PromoGenerateRequest(tenantId: tenantId));
      state = state.copyWith(generating: false, lastGenerated: resp);
      await load(); // segarkan daftar promo
      return resp;
    } catch (e) {
      state = state.copyWith(generating: false, errorMessage: humanizeError(e));
      return null;
    }
  }

  void clearGenerated() => state = state.copyWith(clearGenerated: true);
}

final customerPromoControllerProvider =
    NotifierProvider.autoDispose<CustomerPromoController, CustomerPromoState>(
        CustomerPromoController.new);
