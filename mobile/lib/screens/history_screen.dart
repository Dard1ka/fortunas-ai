import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../api/client.dart';
import '../api/models.dart';
import '../auth/auth_controller.dart';
import '../history/tx_store.dart';
import '../theme/tokens.dart';
import '../ui/pill.dart';
import '../ui/screen_header.dart';

/// HistoryScreen — riwayat transaksi terpadu (kasir manual + voice) + briefing.
/// Transaksi disimpan lokal lewat [loadTxRecords]; tap baris → detail item.
class HistoryScreen extends ConsumerStatefulWidget {
  const HistoryScreen({super.key});

  @override
  ConsumerState<HistoryScreen> createState() => _HistoryScreenState();
}

/// Key lama penyimpanan voice per-line-item. Dipertahankan karena masih dipakai
/// voice_flow.dart (riwayat terpadu kini pakai [recentTxKey] di tx_store.dart).
const recentVoiceKey = 'fortunas.recentVoice.v1';

class _HistoryScreenState extends ConsumerState<HistoryScreen> {
  List<TxRecord> _txs = const [];
  bool _loadingTxs = true;
  String _txSource = ''; // 'server' (BigQuery) | 'local' (cache offline) | ''
  List<DailyReportEntry> _briefings = const [];
  bool _loadingBriefings = true;

  static final _rpFormat = NumberFormat.currency(
    locale: 'id_ID', symbol: 'Rp ', decimalDigits: 0,
  );
  // Tanpa arg locale 'id_ID': locale data belum di-inisialisasi
  // (initializeDateFormatting tak dipanggil), dan DateFormat berlocale akan
  // melempar LocaleDataException saat .format() → layar Riwayat blank/crash.
  static final _dateFormat = DateFormat('d MMM yyyy · HH:mm');

  @override
  void initState() {
    super.initState();
    _loadTxs();
    _loadBriefings();
  }

  Future<void> _loadTxs() async {
    final tenantId = ref.read(authControllerProvider).account?.tenantId;
    if (mounted) setState(() => _loadingTxs = true);

    // Sumber utama: BigQuery per-UMKM (lintas perangkat). Kalau kosong / gagal
    // (mis. BQ belum aktif di dev), fallback ke cache lokal per-UMKM.
    List<TxRecord> txs = const [];
    String source = '';
    try {
      final resp = await ref.read(apiProvider).listUmkmTransactions();
      final list = (resp['transactions'] as List? ?? const []);
      if (list.isNotEmpty) {
        txs = list
            .whereType<Map<String, dynamic>>()
            .map(_serverTxToRecord)
            .toList();
        source = 'server';
      }
    } catch (_) {
      /* jatuh ke fallback lokal */
    }
    if (txs.isEmpty) {
      txs = await loadTxRecords(tenantId: tenantId);
      if (txs.isNotEmpty) source = 'local';
    }

    if (mounted) {
      setState(() {
        _txs = txs;
        _txSource = source;
        _loadingTxs = false;
      });
    }
  }

  /// Map satu transaksi dari response server (BigQuery) → TxRecord untuk UI.
  static TxRecord _serverTxToRecord(Map<String, dynamic> j) {
    final items = (j['items'] as List? ?? const [])
        .whereType<Map<String, dynamic>>()
        .map((it) => TxItem(
              product: it['product']?.toString() ?? '',
              qty: (it['qty'] as num?)?.toInt() ?? 0,
              unitPrice: (it['unit_price'] as num?)?.toInt() ?? 0,
              total: (it['total'] as num?)?.toInt(),
            ))
        .toList();
    return TxRecord(
      invoice: j['invoice']?.toString() ?? '',
      method: TxMethod.server,
      customer: j['customer']?.toString() ?? '',
      total: (j['total'] as num?)?.toInt() ?? 0,
      savedAt: DateTime.tryParse(j['invoice_date']?.toString() ?? ''),
      items: items,
    );
  }

  Future<void> _loadBriefings() async {
    try {
      final r = await ref.read(apiProvider).reportDaily();
      if (!mounted) return;
      setState(() {
        _briefings = r.history;
        _loadingBriefings = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _loadingBriefings = false);
    }
  }

  void _openDetail(TxRecord tx) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => _TxDetailSheet(tx: tx, rpFormat: _rpFormat, dateFormat: _dateFormat),
    );
  }

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: _loadTxs,
      child: ListView(
        padding: const EdgeInsets.only(bottom: 130), // ruang bottom nav mengambang
        children: [
          const ScreenHeader(subtitle: 'Riwayat'),
          Padding(
            padding: const EdgeInsets.fromLTRB(18, 4, 18, 14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Pill.text('RIWAYAT', background: FortunasColors.peach, monoFont: true),
                const SizedBox(height: 10),
                Text('Aktivitas terakhir',
                    style: display(fontSize: 22, letterSpacing: -0.4, height: 1.2)),
                const SizedBox(height: 4),
                Text(
                  'Semua transaksi (kasir & voice) + briefing harian tersimpan.',
                  style: body(fontSize: 12.5, color: FortunasColors.ink3),
                ),
              ],
            ),
          ),

          // Transaksi terpadu (kasir manual + voice)
          Padding(
            padding: const EdgeInsets.fromLTRB(18, 0, 18, 18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(children: [
                  Text('TRANSAKSI (${_txs.length})',
                      style: mono(fontSize: 10, color: FortunasColors.ink3, letterSpacing: 0.8)),
                  const Spacer(),
                  if (_txSource.isNotEmpty) _SourceChip(source: _txSource),
                ]),
                const SizedBox(height: 10),
                if (_loadingTxs && _txs.isEmpty)
                  const _EmptyHint(text: 'Memuat riwayat…')
                else if (_txs.isEmpty)
                  const _EmptyHint(
                      text: 'Belum ada transaksi. Catat lewat Kasir atau tombol mic di bawah.'),
                for (final tx in _txs.take(30)) ...[
                  _TxRow(
                    tx: tx,
                    rpFormat: _rpFormat,
                    dateFormat: _dateFormat,
                    onTap: () => _openDetail(tx),
                  ),
                  const SizedBox(height: 8),
                ],
              ],
            ),
          ),

          // Briefing history
          Padding(
            padding: const EdgeInsets.fromLTRB(18, 0, 18, 24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('BRIEFING HARIAN (${_briefings.length})',
                    style: mono(fontSize: 10, color: FortunasColors.ink3, letterSpacing: 0.8)),
                const SizedBox(height: 10),
                if (_loadingBriefings)
                  const _EmptyHint(text: 'Memuat…')
                else if (_briefings.isEmpty)
                  const _EmptyHint(
                      text: 'Belum ada briefing tersimpan. Jalankan dari layar Briefing.')
                else
                  for (final b in _briefings) ...[
                    _BriefingRow(entry: b),
                    const SizedBox(height: 8),
                  ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Badge metode transaksi: Kasir (lime) / Voice (violet) / Tercatat (server, sky).
/// Data dari BigQuery tak menyimpan metode asli → ditandai "Tercatat".
class _MethodBadge extends StatelessWidget {
  final String method;
  const _MethodBadge({required this.method});

  @override
  Widget build(BuildContext context) {
    late final Color bg;
    late final Color fg;
    late final IconData icon;
    late final String label;
    switch (method) {
      case TxMethod.voice:
        bg = FortunasColors.violetSoft; fg = FortunasColors.violetDeep;
        icon = Icons.mic; label = 'Voice';
        break;
      case TxMethod.server:
        bg = FortunasColors.sky; fg = FortunasColors.ink;
        icon = Icons.cloud_done; label = 'Tercatat';
        break;
      default: // kasir
        bg = FortunasColors.lime; fg = FortunasColors.ink;
        icon = Icons.point_of_sale; label = 'Kasir';
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: bg,
        border: Border.all(color: FortunasColors.ink, width: 1),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Icon(icon, size: 11, color: fg),
        const SizedBox(width: 4),
        Text(label, style: body(fontSize: 10, weight: FontWeight.w700, color: fg)),
      ]),
    );
  }
}

/// Penanda sumber data riwayat: server (BigQuery) atau lokal (cache offline).
class _SourceChip extends StatelessWidget {
  final String source; // 'server' | 'local'
  const _SourceChip({required this.source});

  @override
  Widget build(BuildContext context) {
    final isServer = source == 'server';
    final label = isServer ? 'dari server' : 'offline · lokal';
    final icon = isServer ? Icons.cloud_done : Icons.smartphone;
    final fg = isServer ? FortunasColors.violetDeep : FortunasColors.ink3;
    return Row(mainAxisSize: MainAxisSize.min, children: [
      Icon(icon, size: 11, color: fg),
      const SizedBox(width: 3),
      Text(label, style: mono(fontSize: 9.5, color: fg, letterSpacing: 0.3)),
    ]);
  }
}

class _TxRow extends StatelessWidget {
  final TxRecord tx;
  final NumberFormat rpFormat;
  final DateFormat dateFormat;
  final VoidCallback onTap;
  const _TxRow(
      {required this.tx, required this.rpFormat, required this.dateFormat, required this.onTap});

  String get _summary {
    if (tx.items.isEmpty) return '—';
    final first = tx.items.first;
    final label = '${first.product} · ${first.qty}×';
    final more = tx.items.length - 1;
    return more > 0 ? '$label +$more lainnya' : label;
  }

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        decoration: BoxDecoration(
          color: FortunasColors.surface,
          border: Border.all(color: FortunasColors.ink, width: 1.5),
          borderRadius: BorderRadius.circular(14),
          boxShadow: popShadow(offset: 2),
        ),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Row(children: [
                    _MethodBadge(method: tx.method),
                    const SizedBox(width: 8),
                    Flexible(
                      child: Text(_summary,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: display(
                              fontSize: 13.5,
                              weight: FontWeight.w600,
                              letterSpacing: -0.15,
                              height: 1.2)),
                    ),
                  ]),
                  const SizedBox(height: 4),
                  Text(
                    '${tx.invoice.isEmpty ? '—' : tx.invoice} · '
                    '${tx.savedAt != null ? dateFormat.format(tx.savedAt!.toLocal()) : '—'}',
                    style: mono(fontSize: 10.5, color: FortunasColors.ink3, letterSpacing: 0.2),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(rpFormat.format(tx.total),
                    style: display(
                        fontSize: 13,
                        weight: FontWeight.w700,
                        color: FortunasColors.violet,
                        letterSpacing: 0)),
                const SizedBox(height: 2),
                const Icon(Icons.chevron_right, size: 16, color: FortunasColors.ink4),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

/// Bottom sheet detail transaksi: metode, invoice, pelanggan, daftar item, total.
class _TxDetailSheet extends StatelessWidget {
  final TxRecord tx;
  final NumberFormat rpFormat;
  final DateFormat dateFormat;
  const _TxDetailSheet({required this.tx, required this.rpFormat, required this.dateFormat});

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      top: false,
      child: Container(
        margin: const EdgeInsets.all(12),
        padding: const EdgeInsets.fromLTRB(18, 16, 18, 18),
        decoration: BoxDecoration(
          color: FortunasColors.bg,
          border: Border.all(color: FortunasColors.ink, width: 1.5),
          borderRadius: BorderRadius.circular(18),
          boxShadow: popShadow(offset: 3),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              _MethodBadge(method: tx.method),
              const Spacer(),
              IconButton(
                key: const Key('tx_detail_close'),
                onPressed: () => Navigator.pop(context),
                icon: const Icon(Icons.close, size: 20),
                visualDensity: VisualDensity.compact,
              ),
            ]),
            const SizedBox(height: 6),
            Text('Detail Transaksi',
                style: display(fontSize: 19, letterSpacing: -0.3)),
            const SizedBox(height: 4),
            Text(
              '${tx.invoice.isEmpty ? '—' : tx.invoice} · '
              '${tx.savedAt != null ? dateFormat.format(tx.savedAt!.toLocal()) : '—'}',
              style: mono(fontSize: 10.5, color: FortunasColors.ink3, letterSpacing: 0.2),
            ),
            if (tx.customer.isNotEmpty) ...[
              const SizedBox(height: 2),
              Text('Pelanggan: ${tx.customer}',
                  style: body(fontSize: 12, color: FortunasColors.ink2)),
            ],
            const SizedBox(height: 14),
            Text('ITEM (${tx.items.length})',
                style: mono(fontSize: 10, color: FortunasColors.ink3, letterSpacing: 0.8)),
            const SizedBox(height: 8),
            Flexible(
              child: SingleChildScrollView(
                child: Column(
                  children: [
                    for (final it in tx.items) ...[
                      _DetailItemRow(item: it, rpFormat: rpFormat),
                      const SizedBox(height: 6),
                    ],
                  ],
                ),
              ),
            ),
            const SizedBox(height: 6),
            const Divider(color: FortunasColors.borderSoft, height: 18),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Total', style: display(fontSize: 15, letterSpacing: -0.2)),
                Text(rpFormat.format(tx.total),
                    style: display(
                        fontSize: 17, weight: FontWeight.w800, color: FortunasColors.violet)),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _DetailItemRow extends StatelessWidget {
  final TxItem item;
  final NumberFormat rpFormat;
  const _DetailItemRow({required this.item, required this.rpFormat});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: FortunasColors.surface,
        border: Border.all(color: FortunasColors.ink, width: 1.2),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(item.product,
                    style: body(fontSize: 13, weight: FontWeight.w700, color: FortunasColors.ink)),
                const SizedBox(height: 2),
                Text('${item.qty} × ${rpFormat.format(item.unitPrice)}',
                    style: mono(fontSize: 10.5, color: FortunasColors.ink3)),
              ],
            ),
          ),
          Text(rpFormat.format(item.total),
              style: body(fontSize: 13, weight: FontWeight.w700, color: FortunasColors.ink)),
        ],
      ),
    );
  }
}

class _BriefingRow extends StatelessWidget {
  final DailyReportEntry entry;
  const _BriefingRow({required this.entry});

  @override
  Widget build(BuildContext context) {
    final summary = entry.executiveSummary;
    final preview = summary.length > 220 ? '${summary.substring(0, 220)}…' : summary;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: FortunasColors.surface,
        border: Border.all(color: FortunasColors.ink, width: 1.5),
        borderRadius: BorderRadius.circular(14),
        boxShadow: popShadow(offset: 2),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(entry.date,
                  style: display(fontSize: 14, weight: FontWeight.w600, letterSpacing: -0.2, height: 1.2)),
              Text(
                '${entry.sections.length} analisis',
                style: mono(fontSize: 10, color: FortunasColors.ink3, letterSpacing: 0.4),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(preview, style: body(fontSize: 12.5, color: FortunasColors.ink2, height: 1.45)),
        ],
      ),
    );
  }
}

class _EmptyHint extends StatelessWidget {
  final String text;
  const _EmptyHint({required this.text});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        color: FortunasColors.surfaceSoft,
        border: Border.all(color: FortunasColors.borderSoft, width: 1.5),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(text, style: body(fontSize: 12.5, color: FortunasColors.ink3, height: 1.5)),
    );
  }
}
