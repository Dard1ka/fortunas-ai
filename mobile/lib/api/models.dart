/// API DTOs — manual JSON serialization (no codegen) to keep the
/// dependency footprint small. Mirrors `app/schemas.py` on the backend.
library;

class LlmOutput {
  final String summary;
  final List<String> topFindings;
  final List<String> recommendation;
  final String dataConfidence;
  final List<String> ragSources;

  LlmOutput({
    required this.summary,
    required this.topFindings,
    required this.recommendation,
    this.dataConfidence = 'low',
    this.ragSources = const [],
  });

  factory LlmOutput.fromJson(Map<String, dynamic> j) => LlmOutput(
    summary: j['summary']?.toString() ?? '',
    topFindings: _stringList(j['top_findings']),
    recommendation: _stringList(j['recommendation']),
    dataConfidence: j['data_confidence']?.toString() ?? 'low',
    ragSources: _stringList(j['rag_sources']),
  );
}

class AskResponse {
  final String question;
  final String mappedAnalysis;
  final String status;
  final String message;
  final List<String> agentTrace;
  final List<Map<String, dynamic>> rows;
  final LlmOutput? llmOutput;

  AskResponse({
    required this.question,
    required this.mappedAnalysis,
    required this.status,
    required this.message,
    required this.agentTrace,
    required this.rows,
    this.llmOutput,
  });

  factory AskResponse.fromJson(Map<String, dynamic> j) => AskResponse(
    question: j['question']?.toString() ?? '',
    mappedAnalysis: j['mapped_analysis']?.toString() ?? '',
    status: j['status']?.toString() ?? '',
    message: j['message']?.toString() ?? '',
    agentTrace: _stringList(j['agent_trace']),
    rows: (j['rows'] as List? ?? const []).cast<Map<String, dynamic>>(),
    llmOutput: j['llm_output'] is Map
        ? LlmOutput.fromJson(j['llm_output'] as Map<String, dynamic>)
        : null,
  );
}

class BriefingSection {
  final String analysisType;
  final String label;
  final String status;
  final String summary;
  final List<String> topFindings;
  final List<String> recommendation;
  final int rowCount;
  final String? dataConfidence;
  final List<String> ragSources;

  BriefingSection({
    required this.analysisType,
    required this.label,
    required this.status,
    required this.summary,
    required this.topFindings,
    required this.recommendation,
    required this.rowCount,
    this.dataConfidence,
    this.ragSources = const [],
  });

  factory BriefingSection.fromJson(Map<String, dynamic> j) => BriefingSection(
    analysisType: j['analysis_type']?.toString() ?? '',
    label: j['label']?.toString() ?? '',
    status: j['status']?.toString() ?? '',
    summary: j['summary']?.toString() ?? '',
    topFindings: _stringList(j['top_findings']),
    recommendation: _stringList(j['recommendation']),
    rowCount: (j['row_count'] as num?)?.toInt() ?? 0,
    dataConfidence: j['data_confidence']?.toString(),
    ragSources: _stringList(j['rag_sources']),
  );
}

class DailyReportEntry {
  final String generatedAt;
  final String date;
  final String executiveSummary;
  final List<BriefingSection> sections;

  DailyReportEntry({
    required this.generatedAt,
    required this.date,
    required this.executiveSummary,
    required this.sections,
  });

  factory DailyReportEntry.fromJson(Map<String, dynamic> j) => DailyReportEntry(
    generatedAt: j['generated_at']?.toString() ?? '',
    date: j['date']?.toString() ?? '',
    executiveSummary: j['executive_summary']?.toString() ?? '',
    sections: (j['sections'] as List? ?? const [])
        .whereType<Map<String, dynamic>>()
        .map(BriefingSection.fromJson)
        .toList(),
  );
}

class DailyReportResponse {
  final String status;
  final String message;
  final DailyReportEntry? latest;
  final List<DailyReportEntry> history;

  DailyReportResponse({
    required this.status,
    required this.message,
    this.latest,
    required this.history,
  });

  factory DailyReportResponse.fromJson(Map<String, dynamic> j) => DailyReportResponse(
    status: j['status']?.toString() ?? '',
    message: j['message']?.toString() ?? '',
    latest: j['latest'] is Map
        ? DailyReportEntry.fromJson(j['latest'] as Map<String, dynamic>)
        : null,
    history: (j['history'] as List? ?? const [])
        .whereType<Map<String, dynamic>>()
        .map(DailyReportEntry.fromJson)
        .toList(),
  );
}

class VoiceParseResponse {
  final String invoice;
  final String product;
  final int qty;
  final int unitPrice;
  final int total;
  final String customer;
  final String country;
  final double confidence;
  final String source;

  VoiceParseResponse({
    required this.invoice,
    required this.product,
    required this.qty,
    required this.unitPrice,
    required this.total,
    required this.customer,
    required this.country,
    required this.confidence,
    required this.source,
  });

  factory VoiceParseResponse.fromJson(Map<String, dynamic> j) => VoiceParseResponse(
    invoice: j['invoice']?.toString() ?? '',
    product: j['product']?.toString() ?? '',
    qty: (j['qty'] as num?)?.toInt() ?? 0,
    unitPrice: (j['unit_price'] as num?)?.toInt() ?? 0,
    total: (j['total'] as num?)?.toInt() ?? 0,
    customer: j['customer']?.toString() ?? '',
    country: (j['country']?.toString().isEmpty ?? true) ? 'Indonesia' : j['country'].toString(),
    confidence: (j['confidence'] as num?)?.toDouble() ?? 0.0,
    source: j['source']?.toString() ?? '',
  );

  VoiceParseResponse copyWith({
    String? invoice, String? product, int? qty, int? unitPrice,
    int? total, String? customer, String? country,
  }) => VoiceParseResponse(
    invoice: invoice ?? this.invoice,
    product: product ?? this.product,
    qty: qty ?? this.qty,
    unitPrice: unitPrice ?? this.unitPrice,
    total: total ?? this.total,
    customer: customer ?? this.customer,
    country: country ?? this.country,
    confidence: confidence,
    source: source,
  );

  Map<String, dynamic> toTransactionPayload() => {
    'invoice': invoice,
    'product': product,
    'qty': qty,
    'unit_price': unitPrice,
    'total': total,
    'customer': customer,
    'country': country,
  };
}

/// A single line item within a voice transaction (one product).
class LineItem {
  final String product;
  final int qty;
  final int unitPrice;

  const LineItem({
    required this.product,
    required this.qty,
    required this.unitPrice,
  });

  int get total => qty * unitPrice;

  LineItem copyWith({String? product, int? qty, int? unitPrice}) => LineItem(
        product: product ?? this.product,
        qty: qty ?? this.qty,
        unitPrice: unitPrice ?? this.unitPrice,
      );

  Map<String, dynamic> toJson() => {
        'product': product,
        'qty': qty,
        'unit_price': unitPrice,
        'total': total,
      };

  factory LineItem.fromJson(Map<String, dynamic> j) => LineItem(
        product: j['product']?.toString() ?? '',
        qty: (j['qty'] as num?)?.toInt() ?? 1,
        unitPrice: (j['unit_price'] as num?)?.toInt() ?? 0,
      );
}

/// A parsed voice transaction that can contain MULTIPLE line items, all
/// sharing one invoice / customer / country. Produced by the on-device
/// [TransactionParser] (smart multi-item segmentation).
class ParsedTransaction {
  final String invoice;
  final String customer;
  final String country;
  final List<LineItem> items;
  final double confidence;
  final String source; // 'local-parser' | 'backend'

  const ParsedTransaction({
    required this.invoice,
    required this.customer,
    required this.country,
    required this.items,
    this.confidence = 0.0,
    this.source = 'local-parser',
  });

  int get grandTotal => items.fold(0, (sum, it) => sum + it.total);
  int get itemCount => items.length;
  int get totalQty => items.fold(0, (sum, it) => sum + it.qty);

  ParsedTransaction copyWith({
    String? invoice,
    String? customer,
    String? country,
    List<LineItem>? items,
  }) =>
      ParsedTransaction(
        invoice: invoice ?? this.invoice,
        customer: customer ?? this.customer,
        country: country ?? this.country,
        items: items ?? this.items,
        confidence: confidence,
        source: source,
      );

  /// One backend payload per line item (the backend stores single rows).
  List<Map<String, dynamic>> toTransactionPayloads() => [
        for (final it in items)
          {
            'invoice': invoice,
            'product': it.product,
            'qty': it.qty,
            'unit_price': it.unitPrice,
            'total': it.total,
            'customer': customer,
            'country': country,
          }
      ];
}

class VoiceTransactionResponse {
  final bool ok;
  final String status;
  final String reply;
  final String? invoice;
  final int? rowNumber;

  VoiceTransactionResponse({
    required this.ok,
    required this.status,
    required this.reply,
    this.invoice,
    this.rowNumber,
  });

  factory VoiceTransactionResponse.fromJson(Map<String, dynamic> j) => VoiceTransactionResponse(
    ok: j['ok'] == true,
    status: j['status']?.toString() ?? '',
    reply: j['reply']?.toString() ?? '',
    invoice: j['invoice']?.toString(),
    rowNumber: (j['row_number'] as num?)?.toInt(),
  );
}

// ── UMKM Auth (mirror app/api/routes/auth.py) ──
class AuthResponse {
  final String accessToken;
  final String tokenType;
  final int tenantId;
  final String tenantName;
  final String tablePrefix;

  const AuthResponse({
    required this.accessToken,
    this.tokenType = 'bearer',
    required this.tenantId,
    required this.tenantName,
    required this.tablePrefix,
  });

  factory AuthResponse.fromJson(Map<String, dynamic> j) => AuthResponse(
        accessToken: j['access_token']?.toString() ?? '',
        tokenType: j['token_type']?.toString() ?? 'bearer',
        tenantId: (j['tenant_id'] as num?)?.toInt() ?? 0,
        tenantName: j['tenant_name']?.toString() ?? '',
        tablePrefix: j['table_prefix']?.toString() ?? '',
      );
}

class UmkmAccount {
  final String email;
  final int tenantId;
  final String tenantName;
  final String tablePrefix;
  final Map<String, dynamic> businessProfile;

  const UmkmAccount({
    this.email = '',
    this.tenantId = 0,
    this.tenantName = '',
    this.tablePrefix = '',
    this.businessProfile = const {},
  });

  factory UmkmAccount.fromJson(Map<String, dynamic> j) => UmkmAccount(
        email: j['email']?.toString() ?? '',
        tenantId: (j['tenant_id'] as num?)?.toInt() ?? 0,
        tenantName: j['tenant_name']?.toString() ?? '',
        tablePrefix: j['table_prefix']?.toString() ?? '',
        businessProfile: j['business_profile'] is Map
            ? (j['business_profile'] as Map).cast<String, dynamic>()
            : const {},
      );
}

// ═══════════════════════════════════════════════════════════════
// v5.0 MVP contracts — mirror app/schemas.py
// ═══════════════════════════════════════════════════════════════

// ── Customer Auth & Profile ──
class CustomerProfile {
  final String customerUserId;
  final String username;
  final String phoneNumber;
  final String birthDate;
  final String createdAt;

  const CustomerProfile({
    required this.customerUserId,
    required this.username,
    this.phoneNumber = '',
    this.birthDate = '',
    this.createdAt = '',
  });

  factory CustomerProfile.fromJson(Map<String, dynamic> j) => CustomerProfile(
        customerUserId: j['customer_user_id']?.toString() ?? '',
        username: j['username']?.toString() ?? '',
        phoneNumber: j['phone_number']?.toString() ?? '',
        birthDate: j['birth_date']?.toString() ?? '',
        createdAt: j['created_at']?.toString() ?? '',
      );
}

class CustomerBootstrapRequest {
  final String firebaseIdToken;
  final String username;
  final String birthDate;

  const CustomerBootstrapRequest({
    required this.firebaseIdToken,
    required this.username,
    required this.birthDate,
  });

  Map<String, dynamic> toJson() => {
        'firebase_id_token': firebaseIdToken,
        'username': username,
        'birth_date': birthDate,
      };
}

class CustomerBootstrapResponse {
  final String accessToken;
  final String tokenType;
  final String role;
  final bool isNewUser;
  final CustomerProfile profile;

  const CustomerBootstrapResponse({
    required this.accessToken,
    this.tokenType = 'bearer',
    this.role = 'customer',
    this.isNewUser = false,
    required this.profile,
  });

  factory CustomerBootstrapResponse.fromJson(Map<String, dynamic> j) =>
      CustomerBootstrapResponse(
        accessToken: j['access_token']?.toString() ?? '',
        tokenType: j['token_type']?.toString() ?? 'bearer',
        role: j['role']?.toString() ?? 'customer',
        isNewUser: j['is_new_user'] == true,
        profile: j['profile'] is Map
            ? CustomerProfile.fromJson((j['profile'] as Map).cast<String, dynamic>())
            : const CustomerProfile(customerUserId: '', username: ''),
      );
}

class CustomerProfileUpdate {
  final String? username;
  final String? birthDate;

  const CustomerProfileUpdate({this.username, this.birthDate});

  Map<String, dynamic> toJson() => {
        if (username != null) 'username': username,
        if (birthDate != null) 'birth_date': birthDate,
      };
}

// ── QR Identity + Validate ──
class QrSessionResponse {
  final String qrToken;
  final String nonce;
  final String issuedAt;
  final String expiresAt;
  final int ttlSeconds;

  const QrSessionResponse({
    required this.qrToken,
    required this.nonce,
    required this.issuedAt,
    required this.expiresAt,
    this.ttlSeconds = 90,
  });

  factory QrSessionResponse.fromJson(Map<String, dynamic> j) => QrSessionResponse(
        qrToken: j['qr_token']?.toString() ?? '',
        nonce: j['nonce']?.toString() ?? '',
        issuedAt: j['issued_at']?.toString() ?? '',
        expiresAt: j['expires_at']?.toString() ?? '',
        ttlSeconds: (j['ttl_seconds'] as num?)?.toInt() ?? 90,
      );
}

class QrValidateRequest {
  final String customerQrToken;
  const QrValidateRequest({required this.customerQrToken});
  Map<String, dynamic> toJson() => {'customer_qr_token': customerQrToken};
}

class QrValidateResponse {
  final bool valid;
  final String? customerUserId;
  final String? username;
  final bool isNewMember;
  final String? memberSince;
  final String? reason;

  const QrValidateResponse({
    required this.valid,
    this.customerUserId,
    this.username,
    this.isNewMember = false,
    this.memberSince,
    this.reason,
  });

  factory QrValidateResponse.fromJson(Map<String, dynamic> j) => QrValidateResponse(
        valid: j['valid'] == true,
        customerUserId: j['customer_user_id']?.toString(),
        username: j['username']?.toString(),
        isNewMember: j['is_new_member'] == true,
        memberSince: j['member_since']?.toString(),
        reason: j['reason']?.toString(),
      );
}

// ── Checkout (multi-item) ──
class CheckoutLineItem {
  final String product;
  final int qty;
  final int unitPrice;
  final int total;

  const CheckoutLineItem({
    required this.product,
    required this.qty,
    required this.unitPrice,
    int? total,
  }) : total = total ?? qty * unitPrice;

  Map<String, dynamic> toJson() => {
        'product': product,
        'qty': qty,
        'unit_price': unitPrice,
        'total': total,
      };

  factory CheckoutLineItem.fromJson(Map<String, dynamic> j) {
    final q = (j['qty'] as num?)?.toInt() ?? 1;
    final p = (j['unit_price'] as num?)?.toInt() ?? 0;
    return CheckoutLineItem(
      product: j['product']?.toString() ?? '',
      qty: q,
      unitPrice: p,
      total: (j['total'] as num?)?.toInt() ?? q * p,
    );
  }
}

class CheckoutConfirmRequest {
  final List<CheckoutLineItem> items;
  final String customer;
  final String country;
  final String? invoice;
  final String? customerQrToken;
  final String? promoCode;

  const CheckoutConfirmRequest({
    required this.items,
    this.customer = '',
    this.country = 'Indonesia',
    this.invoice,
    this.customerQrToken,
    this.promoCode,
  });

  int get grandTotal => items.fold(0, (sum, it) => sum + it.total);

  Map<String, dynamic> toJson() => {
        'items': [for (final it in items) it.toJson()],
        'customer': customer,
        'country': country,
        if (invoice != null) 'invoice': invoice,
        if (customerQrToken != null) 'customer_qr_token': customerQrToken,
        if (promoCode != null) 'promo_code': promoCode,
      };
}

class CheckoutConfirmResponse {
  final bool ok;
  final String status;
  final String reply;
  final String? invoice;
  final int itemCount;
  final int grandTotal;
  final String? customerUserId;
  final bool isNewMember;
  final String? memberSince;
  final int? pointsEarned;
  final String? promoRedeemed;

  const CheckoutConfirmResponse({
    required this.ok,
    required this.status,
    required this.reply,
    this.invoice,
    this.itemCount = 0,
    this.grandTotal = 0,
    this.customerUserId,
    this.isNewMember = false,
    this.memberSince,
    this.pointsEarned,
    this.promoRedeemed,
  });

  factory CheckoutConfirmResponse.fromJson(Map<String, dynamic> j) =>
      CheckoutConfirmResponse(
        ok: j['ok'] == true,
        status: j['status']?.toString() ?? '',
        reply: j['reply']?.toString() ?? '',
        invoice: j['invoice']?.toString(),
        itemCount: (j['item_count'] as num?)?.toInt() ?? 0,
        grandTotal: (j['grand_total'] as num?)?.toInt() ?? 0,
        customerUserId: j['customer_user_id']?.toString(),
        isNewMember: j['is_new_member'] == true,
        memberSince: j['member_since']?.toString(),
        pointsEarned: (j['points_earned'] as num?)?.toInt(),
        promoRedeemed: j['promo_redeemed']?.toString(),
      );
}

// ── DPA Policy ──
class DpaPayload {
  final String rawText;
  final List<String> allowedRules;
  final List<String> forbiddenRules;
  final String? policySummary;
  final int version;
  final String? verifiedAt;
  final String? updatedAt;

  const DpaPayload({
    this.rawText = '',
    this.allowedRules = const [],
    this.forbiddenRules = const [],
    this.policySummary,
    this.version = 0,
    this.verifiedAt,
    this.updatedAt,
  });

  factory DpaPayload.fromJson(Map<String, dynamic> j) => DpaPayload(
        rawText: j['raw_text']?.toString() ?? '',
        allowedRules: _stringList(j['allowed_rules']),
        forbiddenRules: _stringList(j['forbidden_rules']),
        policySummary: j['policy_summary']?.toString(),
        version: (j['version'] as num?)?.toInt() ?? 0,
        verifiedAt: j['verified_at']?.toString(),
        updatedAt: j['updated_at']?.toString(),
      );
}

class DpaUpdateRequest {
  final String rawText;
  final List<String> allowedRules;
  final List<String> forbiddenRules;
  final String password;

  const DpaUpdateRequest({
    required this.rawText,
    this.allowedRules = const [],
    this.forbiddenRules = const [],
    required this.password,
  });

  Map<String, dynamic> toJson() => {
        'raw_text': rawText,
        'allowed_rules': allowedRules,
        'forbidden_rules': forbiddenRules,
        'password': password,
      };
}

// ── Device Token (FCM — v5.1) ──
class DeviceTokenRequest {
  final String fcmToken;
  final String platform; // android | ios | web
  final String? userType; // customer | umkm

  const DeviceTokenRequest({
    required this.fcmToken,
    required this.platform,
    this.userType,
  });

  Map<String, dynamic> toJson() => {
        'fcm_token': fcmToken,
        'platform': platform,
        if (userType != null) 'user_type': userType,
      };
}

// ── Loyalty + Points + Promo (MVP-thin) ──
class SpinWheelSegment {
  final int discountAmount;
  final double probability;
  const SpinWheelSegment({required this.discountAmount, required this.probability});

  Map<String, dynamic> toJson() =>
      {'discount_amount': discountAmount, 'probability': probability};

  factory SpinWheelSegment.fromJson(Map<String, dynamic> j) => SpinWheelSegment(
        discountAmount: (j['discount_amount'] as num?)?.toInt() ?? 0,
        probability: (j['probability'] as num?)?.toDouble() ?? 0.0,
      );
}

class PointsEarningRule {
  final String type; // per_amount | per_invoice
  final int pointsPerAmount;
  final int pointsPerInvoice;
  const PointsEarningRule({
    this.type = 'per_amount',
    this.pointsPerAmount = 10000,
    this.pointsPerInvoice = 1,
  });

  Map<String, dynamic> toJson() => {
        'type': type,
        'points_per_amount': pointsPerAmount,
        'points_per_invoice': pointsPerInvoice,
      };

  factory PointsEarningRule.fromJson(Map<String, dynamic> j) => PointsEarningRule(
        type: j['type']?.toString() ?? 'per_amount',
        pointsPerAmount: (j['points_per_amount'] as num?)?.toInt() ?? 10000,
        pointsPerInvoice: (j['points_per_invoice'] as num?)?.toInt() ?? 1,
      );
}

class LoyaltySettings {
  final int minPointsToGeneratePromo;
  final List<SpinWheelSegment> spinWheel;
  final int promoValidDays;
  final PointsEarningRule pointsEarningRule;

  const LoyaltySettings({
    this.minPointsToGeneratePromo = 30,
    this.spinWheel = const [],
    this.promoValidDays = 7,
    this.pointsEarningRule = const PointsEarningRule(),
  });

  Map<String, dynamic> toJson() => {
        'min_points_to_generate_promo': minPointsToGeneratePromo,
        'spin_wheel': [for (final s in spinWheel) s.toJson()],
        'promo_valid_days': promoValidDays,
        'points_earning_rule': pointsEarningRule.toJson(),
      };

  factory LoyaltySettings.fromJson(Map<String, dynamic> j) => LoyaltySettings(
        minPointsToGeneratePromo:
            (j['min_points_to_generate_promo'] as num?)?.toInt() ?? 30,
        spinWheel: (j['spin_wheel'] as List? ?? const [])
            .whereType<Map<String, dynamic>>()
            .map(SpinWheelSegment.fromJson)
            .toList(),
        promoValidDays: (j['promo_valid_days'] as num?)?.toInt() ?? 7,
        pointsEarningRule: j['points_earning_rule'] is Map
            ? PointsEarningRule.fromJson(
                (j['points_earning_rule'] as Map).cast<String, dynamic>())
            : const PointsEarningRule(),
      );
}

class PointsLedgerEntry {
  final String eventType;
  final int pointsDelta;
  final String? invoice;
  final String? promoId;
  final int? tenantId;
  final String createdAt;

  const PointsLedgerEntry({
    required this.eventType,
    required this.pointsDelta,
    this.invoice,
    this.promoId,
    this.tenantId,
    this.createdAt = '',
  });

  factory PointsLedgerEntry.fromJson(Map<String, dynamic> j) => PointsLedgerEntry(
        eventType: j['event_type']?.toString() ?? '',
        pointsDelta: (j['points_delta'] as num?)?.toInt() ?? 0,
        invoice: j['invoice']?.toString(),
        promoId: j['promo_id']?.toString(),
        tenantId: (j['tenant_id'] as num?)?.toInt(),
        createdAt: j['created_at']?.toString() ?? '',
      );
}

class PointsBalanceResponse {
  final String customerUserId;
  final int balance;
  final List<PointsLedgerEntry> recent;

  const PointsBalanceResponse({
    required this.customerUserId,
    this.balance = 0,
    this.recent = const [],
  });

  factory PointsBalanceResponse.fromJson(Map<String, dynamic> j) =>
      PointsBalanceResponse(
        customerUserId: j['customer_user_id']?.toString() ?? '',
        balance: (j['balance'] as num?)?.toInt() ?? 0,
        recent: (j['recent'] as List? ?? const [])
            .whereType<Map<String, dynamic>>()
            .map(PointsLedgerEntry.fromJson)
            .toList(),
      );
}

class PromoInstance {
  final String promoId;
  final int tenantId;
  final String name;
  final String code;
  final String description;
  final int discountAmount;
  final String? targetProduct;
  final String status;
  final int pointsCost;
  final String generatedAt;
  final String expiresAt;
  final String? redeemedAt;
  final String? qrPayload;

  const PromoInstance({
    required this.promoId,
    required this.tenantId,
    required this.name,
    required this.code,
    this.description = '',
    required this.discountAmount,
    this.targetProduct,
    this.status = 'generated',
    this.pointsCost = 0,
    this.generatedAt = '',
    this.expiresAt = '',
    this.redeemedAt,
    this.qrPayload,
  });

  factory PromoInstance.fromJson(Map<String, dynamic> j) => PromoInstance(
        promoId: j['promo_id']?.toString() ?? '',
        tenantId: (j['tenant_id'] as num?)?.toInt() ?? 0,
        name: j['name']?.toString() ?? '',
        code: j['code']?.toString() ?? '',
        description: j['description']?.toString() ?? '',
        discountAmount: (j['discount_amount'] as num?)?.toInt() ?? 0,
        targetProduct: j['target_product']?.toString(),
        status: j['status']?.toString() ?? 'generated',
        pointsCost: (j['points_cost'] as num?)?.toInt() ?? 0,
        generatedAt: j['generated_at']?.toString() ?? '',
        expiresAt: j['expires_at']?.toString() ?? '',
        redeemedAt: j['redeemed_at']?.toString(),
        qrPayload: j['qr_payload']?.toString(),
      );
}

class PromoGenerateRequest {
  final int tenantId;
  const PromoGenerateRequest({required this.tenantId});
  Map<String, dynamic> toJson() => {'tenant_id': tenantId};
}

class PromoGenerateResponse {
  final PromoInstance promo;
  final SpinWheelSegment spinResult;
  const PromoGenerateResponse({required this.promo, required this.spinResult});

  factory PromoGenerateResponse.fromJson(Map<String, dynamic> j) =>
      PromoGenerateResponse(
        promo: PromoInstance.fromJson((j['promo'] as Map).cast<String, dynamic>()),
        spinResult:
            SpinWheelSegment.fromJson((j['spin_result'] as Map).cast<String, dynamic>()),
      );
}

class PromoListResponse {
  final List<PromoInstance> promos;
  const PromoListResponse({this.promos = const []});

  factory PromoListResponse.fromJson(Map<String, dynamic> j) => PromoListResponse(
        promos: (j['promos'] as List? ?? const [])
            .whereType<Map<String, dynamic>>()
            .map(PromoInstance.fromJson)
            .toList(),
      );
}

// ─── helpers ──────────────────────────────────────────────────
List<String> _stringList(dynamic v) {
  if (v is List) {
    return v.map((e) => e?.toString() ?? '').where((s) => s.isNotEmpty).toList();
  }
  return const [];
}
