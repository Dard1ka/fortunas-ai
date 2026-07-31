import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

/// Penyimpanan lokal riwayat transaksi terpadu (kasir manual + voice).
///
/// Kedua alur (checkout kasir & voice) menulis satu [TxRecord] per transaksi ke
/// key yang sama, ditandai [TxRecord.method]. Layar Riwayat membaca daftar ini,
/// menampilkan badge metode, dan detail item saat baris di-tap.
const recentTxKey = 'fortunas.recentTx.v1';
const _maxTxRecords = 50;

/// Key penyimpanan lokal DIPISAH per-UMKM (tenantId) supaya riwayat dua akun di
/// perangkat yang sama tidak bertabrakan. tenantId null → key global (fallback).
String _keyFor(int? tenantId) =>
    tenantId == null ? recentTxKey : '$recentTxKey.$tenantId';

/// Metode transaksi.
class TxMethod {
  static const kasir = 'kasir';
  static const voice = 'voice';
  static const server = 'server'; // sumber BigQuery (metode asli tak tersimpan)
}

class TxItem {
  final String product;
  final int qty;
  final int unitPrice;
  final int total;

  const TxItem({
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

  factory TxItem.fromJson(Map<String, dynamic> j) {
    final q = (j['qty'] as num?)?.toInt() ?? 1;
    final p = (j['unit_price'] as num?)?.toInt() ?? 0;
    return TxItem(
      product: j['product']?.toString() ?? '',
      qty: q,
      unitPrice: p,
      total: (j['total'] as num?)?.toInt() ?? q * p,
    );
  }
}

class TxRecord {
  final String invoice;
  final String method; // TxMethod.kasir | TxMethod.voice
  final String customer;
  final int total;
  final DateTime? savedAt;
  final List<TxItem> items;

  const TxRecord({
    required this.invoice,
    required this.method,
    required this.customer,
    required this.total,
    required this.savedAt,
    required this.items,
  });

  bool get isVoice => method == TxMethod.voice;
  int get itemCount => items.fold(0, (s, it) => s + it.qty);

  Map<String, dynamic> toJson() => {
        'invoice': invoice,
        'method': method,
        'customer': customer,
        'total': total,
        'saved_at': savedAt?.toUtc().toIso8601String(),
        'items': items.map((it) => it.toJson()).toList(),
      };

  factory TxRecord.fromJson(Map<String, dynamic> j) => TxRecord(
        invoice: j['invoice']?.toString() ?? '',
        method: j['method']?.toString() == TxMethod.voice
            ? TxMethod.voice
            : TxMethod.kasir,
        customer: j['customer']?.toString() ?? '',
        total: (j['total'] as num?)?.toInt() ?? 0,
        savedAt: DateTime.tryParse(j['saved_at']?.toString() ?? ''),
        items: (j['items'] as List? ?? const [])
            .whereType<Map<String, dynamic>>()
            .map(TxItem.fromJson)
            .toList(),
      );
}

/// Tambahkan satu transaksi ke depan daftar (terbaru dulu), dibatasi [_maxTxRecords].
/// Non-fatal: kegagalan penyimpanan diabaikan agar tak mengganggu alur transaksi.
Future<void> addTxRecord(TxRecord record, {int? tenantId}) async {
  try {
    final prefs = await SharedPreferences.getInstance();
    final key = _keyFor(tenantId);
    final raw = prefs.getString(key);
    final List existing = raw != null ? (jsonDecode(raw) as List) : [];
    final next = [record.toJson(), ...existing].take(_maxTxRecords).toList();
    await prefs.setString(key, jsonEncode(next));
  } catch (_) {
    /* non-fatal */
  }
}

Future<List<TxRecord>> loadTxRecords({int? tenantId}) async {
  try {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_keyFor(tenantId));
    if (raw == null) return const [];
    final list = jsonDecode(raw) as List;
    return list
        .whereType<Map<String, dynamic>>()
        .map(TxRecord.fromJson)
        .toList();
  } catch (_) {
    return const [];
  }
}
