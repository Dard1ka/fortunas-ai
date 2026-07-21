import 'package:dio/dio.dart';
import 'package:fortunas_ai/api/client.dart';
import 'package:fortunas_ai/api/models.dart';
import 'package:fortunas_ai/auth/token_store.dart';

class FakeTokenStore implements TokenStore {
  String? value;
  FakeTokenStore([this.value]);
  @override
  Future<String?> read() async => value;
  @override
  Future<void> write(String token) async => value = token;
  @override
  Future<void> delete() async => value = null;
}

class FakeApi extends FortunasApi {
  FakeApi() : super();
  AuthResponse? loginResult;
  AuthResponse? registerResult;
  UmkmAccount? meResult;
  Object? loginError;
  Object? registerError;
  Object? meError;
  int loginCalls = 0;

  // Override so widget tests never hit a real socket (ProfileScreen._checkHealth).
  @override
  Future<Map<String, dynamic>> health() async => {'status': 'ok'};

  @override
  Future<AuthResponse> login(String email, String password) async {
    loginCalls++;
    if (loginError != null) throw loginError!;
    return loginResult!;
  }

  @override
  Future<AuthResponse> register({
    required String email,
    required String password,
    required String businessName,
  }) async {
    if (registerError != null) throw registerError!;
    return registerResult!;
  }

  @override
  Future<UmkmAccount> me() async {
    if (meError != null) throw meError!;
    return meResult!;
  }

  DpaPayload? dpaResult;
  Object? dpaError;
  DpaPayload? updateResult;
  Object? updateError;
  int updateCalls = 0;
  DpaUpdateRequest? lastUpdate;

  @override
  Future<DpaPayload> getDpa() async {
    if (dpaError != null) throw dpaError!;
    return dpaResult ?? const DpaPayload();
  }

  @override
  Future<DpaPayload> updateDpa(DpaUpdateRequest req) async {
    updateCalls++;
    lastUpdate = req;
    if (updateError != null) throw updateError!;
    return updateResult!;
  }

  DailyReportResponse? reportResult;
  Object? reportError;

  @override
  Future<DailyReportResponse> reportDaily({CancelToken? cancelToken}) async {
    if (reportError != null) throw reportError!;
    return reportResult!;
  }

  CheckoutConfirmResponse? checkoutResult;
  Object? checkoutError;
  CheckoutConfirmRequest? lastCheckout;

  @override
  Future<CheckoutConfirmResponse> checkoutConfirm(CheckoutConfirmRequest req,
      {CancelToken? cancelToken}) async {
    lastCheckout = req;
    if (checkoutError != null) throw checkoutError!;
    return checkoutResult!;
  }

  CustomerBootstrapResponse? customerBootstrapResult;
  Object? customerBootstrapError;
  CustomerBootstrapRequest? lastCustomerBootstrap;

  @override
  Future<CustomerBootstrapResponse> customerBootstrap(CustomerBootstrapRequest req,
      {CancelToken? cancelToken}) async {
    lastCustomerBootstrap = req;
    if (customerBootstrapError != null) throw customerBootstrapError!;
    return customerBootstrapResult!;
  }

  QrSessionResponse? customerQrSessionResult;
  Object? customerQrSessionError;
  int customerQrSessionCallCount = 0;

  @override
  Future<QrSessionResponse> customerQrSession({CancelToken? cancelToken}) async {
    customerQrSessionCallCount++;
    if (customerQrSessionError != null) throw customerQrSessionError!;
    return customerQrSessionResult!;
  }

  QrValidateResponse? scanValidateResult;
  Object? scanValidateError;
  QrValidateRequest? lastScanValidate;

  @override
  Future<QrValidateResponse> scanValidate(QrValidateRequest req,
      {CancelToken? cancelToken}) async {
    lastScanValidate = req;
    if (scanValidateError != null) throw scanValidateError!;
    return scanValidateResult!;
  }

  ProductListResponse? listProductsResult;
  ProductItem? createProductResult;
  ProductItem? setStockResult;
  Object? setStockError;
  int? lastCreateStock;
  (int, int?)? lastSetStock;

  @override
  Future<ProductListResponse> listProducts({CancelToken? cancelToken}) async =>
      listProductsResult ?? const ProductListResponse(products: [], count: 0);

  @override
  Future<ProductItem> createProduct({
    required String name,
    required String description,
    required List<int> imageBytes,
    required String imageFilename,
    int? stock,
    int? categoryId,
    CancelToken? cancelToken,
  }) async {
    lastCreateStock = stock;
    lastCreateCategoryIdOnProduct = categoryId;
    return createProductResult!;
  }

  @override
  Future<ProductItem> setStock(int productId, int? stock, {CancelToken? cancelToken}) async {
    lastSetStock = (productId, stock);
    if (setStockError != null) throw setStockError!;
    return setStockResult!;
  }

  CategoryListResponse? listCategoriesResult;
  Category? createCategoryResult;
  Object? createCategoryError;
  String? lastCreateCategoryName;
  Map<String, dynamic>? deleteCategoryResult;
  (int, int?)? lastSetProductCategory;
  ProductItem? setProductCategoryResult;
  int? lastCreateCategoryIdOnProduct;

  @override
  Future<CategoryListResponse> listCategories({CancelToken? cancelToken}) async =>
      listCategoriesResult ?? const CategoryListResponse();

  @override
  Future<Category> createCategory(String name, {CancelToken? cancelToken}) async {
    lastCreateCategoryName = name;
    if (createCategoryError != null) throw createCategoryError!;
    return createCategoryResult!;
  }

  @override
  Future<Map<String, dynamic>> deleteCategory(int categoryId, {CancelToken? cancelToken}) async =>
      deleteCategoryResult ?? {"deleted": true, "reassigned": 0};

  @override
  Future<ProductItem> setProductCategory(int productId, int? categoryId, {CancelToken? cancelToken}) async {
    lastSetProductCategory = (productId, categoryId);
    return setProductCategoryResult!;
  }
}
