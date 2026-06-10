import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../api/client.dart';
import '../api/models.dart';
import '../theme/tokens.dart';
import '../ui/icon_set.dart';
import '../ui/pill.dart';
import '../ui/screen_header.dart';

/// HistoryScreen — local voice transactions + saved briefings.
/// React equivalent: frontend/src/screens/HistoryScreen.jsx
class HistoryScreen extends ConsumerStatefulWidget {
  const HistoryScreen({super.key});

  @override
  ConsumerState<HistoryScreen> createState() => _HistoryScreenState();
}

const recentVoiceKey = 'fortunas.recentVoice.v1';

class _HistoryScreenState extends ConsumerState<HistoryScreen> {
  List<_VoiceTxEntry> _voiceTx = const [];
  List<DailyReportEntry> _briefings = const [];
  bool _loadingBriefings = true;

  static final _rpFormat = NumberFormat.currency(
    locale: 'id_ID', symbol: 'Rp ', decimalDigits: 0,
  );
  static final _dateFormat = DateFormat('d MMM yyyy · HH:mm', 'id_ID');

  @override
  void initState() {
    super.initState();
    _loadVoice();
    _loadBriefings();
  }

  Future<void> _loadVoice() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(recentVoiceKey);
    if (raw == null) return;
    try {
      final list = jsonDecode(raw) as List;
      final parsed = list
          .whereType<Map<String, dynamic>>()
          .map(_VoiceTxEntry.fromJson)
          .toList();
      if (mounted) setState(() => _voiceTx = parsed);
    } catch (_) { /* ignore malformed */ }
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

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.only(bottom: 30),
      children: [
        const ScreenHeader(subtitle: 'Riwayat'),
        Padding(
          padding: const EdgeInsets.fromLTRB(18, 4, 18, 14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Pill.text('RIWAYAT', background: FortunasColors.peach, monoFont: true),
              const SizedBox(height: 10),
              Text('Aktivitas terakhir', style: display(fontSize: 22, letterSpacing: -0.4, height: 1.2)),
              const SizedBox(height: 4),
              Text(
                'Transaksi voice + briefing harian yang tersimpan.',
                style: body(fontSize: 12.5, color: FortunasColors.ink3),
              ),
            ],
          ),
        ),

        // Voice transactions
        Padding(
          padding: const EdgeInsets.fromLTRB(18, 0, 18, 18),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('TRANSAKSI VOICE (${_voiceTx.length})',
                style: mono(fontSize: 10, color: FortunasColors.ink3, letterSpacing: 0.8)),
              const SizedBox(height: 10),
              if (_voiceTx.isEmpty)
                _EmptyHint(text: 'Belum ada transaksi voice. Tekan tombol mic di bawah untuk mulai.'),
              for (final tx in _voiceTx.take(10)) ...[
                _VoiceTxRow(tx: tx, rpFormat: _rpFormat, dateFormat: _dateFormat),
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
                _EmptyHint(text: 'Memuat…')
              else if (_briefings.isEmpty)
                _EmptyHint(text: 'Belum ada briefing tersimpan. Jalankan dari layar Briefing.')
              else
                for (final b in _briefings) ...[
                  _BriefingRow(entry: b),
                  const SizedBox(height: 8),
                ],
            ],
          ),
        ),
      ],
    );
  }
}

class _VoiceTxEntry {
  final String invoice, product, customer, country;
  final int qty, unitPrice, total;
  final DateTime? savedAt;

  _VoiceTxEntry({
    required this.invoice, required this.product, required this.qty,
    required this.unitPrice, required this.total,
    required this.customer, required this.country, required this.savedAt,
  });

  factory _VoiceTxEntry.fromJson(Map<String, dynamic> j) => _VoiceTxEntry(
    invoice: j['invoice']?.toString() ?? '',
    product: j['product']?.toString() ?? '',
    qty: (j['qty'] as num?)?.toInt() ?? 0,
    unitPrice: (j['unit_price'] as num?)?.toInt() ?? 0,
    total: (j['total'] as num?)?.toInt() ?? 0,
    customer: j['customer']?.toString() ?? '',
    country: j['country']?.toString() ?? 'Indonesia',
    savedAt: DateTime.tryParse(j['savedAt']?.toString() ?? ''),
  );
}

class _VoiceTxRow extends StatelessWidget {
  final _VoiceTxEntry tx;
  final NumberFormat rpFormat;
  final DateFormat dateFormat;
  const _VoiceTxRow({required this.tx, required this.rpFormat, required this.dateFormat});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: FortunasColors.surface,
        border: Border.all(color: FortunasColors.ink, width: 1.5),
        borderRadius: BorderRadius.circular(14),
        boxShadow: popShadow(offset: 2),
      ),
      child: Row(
        children: [
          Container(
            width: 36, height: 36,
            decoration: BoxDecoration(
              color: FortunasColors.violetSoft,
              border: Border.all(color: FortunasColors.ink, width: 1.5),
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Center(
              child: AppIcon(name: 'mic', size: 16, color: FortunasColors.violetDeep),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  '${tx.product} · ${tx.qty}×',
                  style: display(
                    fontSize: 13.5, weight: FontWeight.w600, letterSpacing: -0.15, height: 1.2,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  '${tx.invoice} · ${tx.savedAt != null ? dateFormat.format(tx.savedAt!.toLocal()) : '—'}',
                  style: mono(fontSize: 10.5, color: FortunasColors.ink3, letterSpacing: 0.2),
                ),
              ],
            ),
          ),
          Text(
            rpFormat.format(tx.total),
            style: display(fontSize: 13, weight: FontWeight.w700, color: FortunasColors.violet, letterSpacing: 0),
          ),
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
              Text(entry.date, style: display(fontSize: 14, weight: FontWeight.w600, letterSpacing: -0.2, height: 1.2)),
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
        border: Border.all(color: FortunasColors.borderSoft, width: 1.5, style: BorderStyle.solid),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(text, style: body(fontSize: 12.5, color: FortunasColors.ink3, height: 1.5)),
    );
  }
}
