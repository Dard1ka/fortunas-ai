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

// ─── helpers ──────────────────────────────────────────────────
List<String> _stringList(dynamic v) {
  if (v is List) {
    return v.map((e) => e?.toString() ?? '').where((s) => s.isNotEmpty).toList();
  }
  return const [];
}
