import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../auth/auth_controller.dart';
import '../auth/token_store.dart';
import 'auth_interceptor.dart';
import 'models.dart';

/// Default backend base URL. Override at run time via:
///   flutter run --dart-define=FORTUNAS_API=http://10.0.2.2:8000
///
/// Notes:
/// - Android emulator: `10.0.2.2` maps to host's `localhost`.
/// - iOS simulator: `localhost` works directly.
/// - Physical phone on same WiFi: use PC's LAN IP (e.g. http://192.168.40.6:8000).
const _defaultBaseUrl = String.fromEnvironment(
  'FORTUNAS_API',
  defaultValue: 'http://127.0.0.1:8000',
);

class FortunasApi {
  final Dio _dio;

  FortunasApi({
    String? baseUrl,
    String? Function()? getToken,
    void Function()? onUnauthorized,
  }) : _dio = Dio(BaseOptions(
          baseUrl: baseUrl ?? _defaultBaseUrl,
          connectTimeout: const Duration(seconds: 10),
          receiveTimeout: const Duration(seconds: 120),
          sendTimeout:    const Duration(seconds: 10),
          headers: const {'Content-Type': 'application/json'},
        )) {
    if (getToken != null) {
      _dio.interceptors.add(
        AuthInterceptor(getToken: getToken, onUnauthorized: onUnauthorized),
      );
    }
    if (kDebugMode) {
      _dio.interceptors.add(LogInterceptor(
        request: false,
        requestBody: false,
        responseHeader: false,
        responseBody: false,
        error: true,
      ));
    }
  }

  Future<Map<String, dynamic>> health() async {
    final r = await _dio.get('/health');
    return (r.data as Map).cast<String, dynamic>();
  }

  Future<AuthResponse> login(String email, String password) async {
    final r = await _dio.post('/auth/login',
        data: {'email': email, 'password': password});
    return AuthResponse.fromJson((r.data as Map).cast<String, dynamic>());
  }

  Future<AuthResponse> register({
    required String email,
    required String password,
    required String businessName,
  }) async {
    final r = await _dio.post('/auth/register', data: {
      'email': email,
      'password': password,
      'business_name': businessName,
    });
    return AuthResponse.fromJson((r.data as Map).cast<String, dynamic>());
  }

  Future<UmkmAccount> me() async {
    final r = await _dio.get('/auth/me');
    return UmkmAccount.fromJson((r.data as Map).cast<String, dynamic>());
  }

  Future<AskResponse> ask(String question, {CancelToken? cancelToken}) async {
    final r = await _dio.post(
      '/ask',
      data: {'question': question},
      cancelToken: cancelToken,
    );
    return AskResponse.fromJson((r.data as Map).cast<String, dynamic>());
  }

  Future<DailyReportResponse> reportDaily({CancelToken? cancelToken}) async {
    final r = await _dio.get('/report/daily', cancelToken: cancelToken);
    return DailyReportResponse.fromJson((r.data as Map).cast<String, dynamic>());
  }

  Future<CheckoutConfirmResponse> checkoutConfirm(CheckoutConfirmRequest req,
      {CancelToken? cancelToken}) async {
    final r = await _dio.post('/checkout/confirm',
        data: req.toJson(), cancelToken: cancelToken);
    return CheckoutConfirmResponse.fromJson((r.data as Map).cast<String, dynamic>());
  }

  Future<CustomerBootstrapResponse> customerBootstrap(CustomerBootstrapRequest req,
      {CancelToken? cancelToken}) async {
    final r = await _dio.post('/customer/auth/bootstrap',
        data: req.toJson(), cancelToken: cancelToken);
    return CustomerBootstrapResponse.fromJson((r.data as Map).cast<String, dynamic>());
  }

  Future<DailyReportResponse> reportDailyRun({CancelToken? cancelToken}) async {
    final r = await _dio.post('/report/daily/run', cancelToken: cancelToken);
    return DailyReportResponse.fromJson((r.data as Map).cast<String, dynamic>());
  }

  Future<VoiceParseResponse> voiceParse(String transcript) async {
    final r = await _dio.post('/voice/parse', data: {'transcript': transcript});
    return VoiceParseResponse.fromJson((r.data as Map).cast<String, dynamic>());
  }

  Future<VoiceTransactionResponse> voiceTransaction(Map<String, dynamic> payload) async {
    final r = await _dio.post('/voice/transaction', data: payload);
    return VoiceTransactionResponse.fromJson((r.data as Map).cast<String, dynamic>());
  }

  Future<DpaPayload> getDpa() async {
    final r = await _dio.get('/umkm/dpa');
    return DpaPayload.fromJson((r.data as Map).cast<String, dynamic>());
  }

  Future<DpaPayload> updateDpa(DpaUpdateRequest req) async {
    final r = await _dio.put('/umkm/dpa', data: req.toJson());
    return DpaPayload.fromJson((r.data as Map).cast<String, dynamic>());
  }
}

/// Singleton Riverpod provider for the API client.
/// Passes the in-memory token so AuthInterceptor can attach Bearer headers.
/// onUnauthorized triggers logout via authControllerProvider (lazy read —
/// Dart allows this circular import because both refs are inside closures).
final apiProvider = Provider<FortunasApi>(
  (ref) => FortunasApi(
    getToken: () => ref.read(tokenProvider),
    onUnauthorized: () => ref.read(authControllerProvider.notifier).logout(),
  ),
);
