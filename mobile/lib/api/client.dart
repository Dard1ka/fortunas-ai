import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart' hide Category;
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

  Future<QrSessionResponse> customerQrSession({CancelToken? cancelToken}) async {
    final r = await _dio.post('/customer/qr/session', cancelToken: cancelToken);
    return QrSessionResponse.fromJson((r.data as Map).cast<String, dynamic>());
  }

  Future<QrValidateResponse> scanValidate(QrValidateRequest req,
      {CancelToken? cancelToken}) async {
    final r = await _dio.post('/umkm/customer/scan/validate',
        data: req.toJson(), cancelToken: cancelToken);
    return QrValidateResponse.fromJson((r.data as Map).cast<String, dynamic>());
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

  // ── Customer loyalty / points / promo / home ──
  Future<CustomerHomeResponse> customerHome({CancelToken? cancelToken}) async {
    final r = await _dio.get('/customer/home', cancelToken: cancelToken);
    return CustomerHomeResponse.fromJson((r.data as Map).cast<String, dynamic>());
  }

  Future<PointsBalanceResponse> customerPoints({CancelToken? cancelToken}) async {
    final r = await _dio.get('/customer/points', cancelToken: cancelToken);
    return PointsBalanceResponse.fromJson((r.data as Map).cast<String, dynamic>());
  }

  Future<PromoListResponse> customerPromos({CancelToken? cancelToken}) async {
    final r = await _dio.get('/customer/promos', cancelToken: cancelToken);
    return PromoListResponse.fromJson((r.data as Map).cast<String, dynamic>());
  }

  Future<PromoGenerateResponse> customerGeneratePromo(PromoGenerateRequest req,
      {CancelToken? cancelToken}) async {
    final r = await _dio.post('/customer/promos/generate',
        data: req.toJson(), cancelToken: cancelToken);
    return PromoGenerateResponse.fromJson((r.data as Map).cast<String, dynamic>());
  }

  Future<CustomerTransactionsResponse> customerTransactions({CancelToken? cancelToken}) async {
    final r = await _dio.get('/customer/transactions', cancelToken: cancelToken);
    return CustomerTransactionsResponse.fromJson((r.data as Map).cast<String, dynamic>());
  }

  // ── Produk UMKM (katalog) ──
  Future<ProductListResponse> listProducts({CancelToken? cancelToken}) async {
    final r = await _dio.get('/umkm/products', cancelToken: cancelToken);
    return ProductListResponse.fromJson((r.data as Map).cast<String, dynamic>());
  }

  /// Buat produk baru. Gambar WAJIB (backend menolak tanpa image).
  Future<ProductItem> createProduct({
    required String name,
    required String description,
    required List<int> imageBytes,
    required String imageFilename,
    int? stock,
    int? categoryId,
    CancelToken? cancelToken,
  }) async {
    final form = FormData.fromMap({
      'name': name,
      'description': description,
      'image': MultipartFile.fromBytes(imageBytes, filename: imageFilename),
      if (stock != null) 'stock': stock.toString(),
      if (categoryId != null) 'category_id': categoryId.toString(),
    });
    final r = await _dio.post('/umkm/products', data: form, cancelToken: cancelToken);
    return ProductItem.fromJson((r.data as Map).cast<String, dynamic>());
  }

  Future<void> deleteProduct(int productId, {CancelToken? cancelToken}) async {
    await _dio.delete('/umkm/products/$productId', cancelToken: cancelToken);
  }

  /// Set/restock stok. null = jadikan tak-dilacak.
  Future<ProductItem> setStock(int productId, int? stock, {CancelToken? cancelToken}) async {
    final r = await _dio.patch('/umkm/products/$productId/stock',
        data: {'stock': stock}, cancelToken: cancelToken);
    return ProductItem.fromJson((r.data as Map).cast<String, dynamic>());
  }

  // ── Kategori produk UMKM ──
  Future<CategoryListResponse> listCategories({CancelToken? cancelToken}) async {
    final r = await _dio.get('/umkm/categories', cancelToken: cancelToken);
    return CategoryListResponse.fromJson((r.data as Map).cast<String, dynamic>());
  }

  Future<Category> createCategory(String name, {CancelToken? cancelToken}) async {
    final r = await _dio.post('/umkm/categories', data: {'name': name}, cancelToken: cancelToken);
    return Category.fromJson((r.data as Map).cast<String, dynamic>());
  }

  Future<Map<String, dynamic>> deleteCategory(int categoryId, {CancelToken? cancelToken}) async {
    final r = await _dio.delete('/umkm/categories/$categoryId', cancelToken: cancelToken);
    return (r.data as Map).cast<String, dynamic>();
  }

  Future<ProductItem> setProductCategory(int productId, int? categoryId, {CancelToken? cancelToken}) async {
    final r = await _dio.patch('/umkm/products/$productId/category',
        data: {'category_id': categoryId}, cancelToken: cancelToken);
    return ProductItem.fromJson((r.data as Map).cast<String, dynamic>());
  }

  /// Auto-kategori AI untuk semua produk yang belum berkategori.
  /// Return {status, categorized, total_uncategorized}.
  Future<Map<String, dynamic>> autoCategorizeProducts({CancelToken? cancelToken}) async {
    final r = await _dio.post('/umkm/products/auto-categorize', cancelToken: cancelToken);
    return (r.data as Map).cast<String, dynamic>();
  }

  /// Riwayat transaksi milik UMKM ini dari BigQuery (per-tenant).
  /// Return {transactions:[...], count, source}. Empty saat BQ belum aktif.
  Future<Map<String, dynamic>> listUmkmTransactions(
      {int limit = 200, CancelToken? cancelToken}) async {
    final r = await _dio.get('/umkm/transactions',
        queryParameters: {'limit': limit}, cancelToken: cancelToken);
    return (r.data as Map).cast<String, dynamic>();
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
