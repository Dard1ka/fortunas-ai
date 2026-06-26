import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/client.dart';
import '../api/errors.dart';
import '../api/models.dart';
import '../theme/tokens.dart';
import '../ui/icon_set.dart';
import '../ui/pill.dart';
import '../ui/screen_header.dart';
import 'briefing_kpi.dart';

/// Fixed height per KPI row so a full-width singleton card keeps the same
/// vertical rhythm as the 2-column rows. Bump if `_KpiCard` overflows in tests.
const double _kpiRowHeight = 116.0;

/// BriefingScreen — daily executive summary + KPI grid + findings.
/// React equivalent: frontend/src/screens/BriefingScreen.jsx
class BriefingScreen extends ConsumerStatefulWidget {
  const BriefingScreen({super.key});

  @override
  ConsumerState<BriefingScreen> createState() => _BriefingScreenState();
}

class _BriefingScreenState extends ConsumerState<BriefingScreen> {
  DailyReportEntry? _latest;
  String? _error;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _fetch();
  }

  Future<void> _fetch() async {
    try {
      final r = await ref.read(apiProvider).reportDaily();
      if (!mounted) return;
      setState(() {
        _latest = r.latest;
        _loading = false;
        _error = null;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = humanizeError(e);
        _loading = false;
      });
    }
  }

  static const _iconFor = {
    'repeat_customer': 'user',
    'high_value_customer': 'coin',
    'peak_hour': 'clock',
    'bundle_opportunity': 'bag',
    'top_product': 'flame',
  };
  static const _colorFor = {
    'repeat_customer': FortunasColors.violet,
    'high_value_customer': FortunasColors.sky,
    'peak_hour': FortunasColors.lime,
    'bundle_opportunity': FortunasColors.peach,
    'top_product': FortunasColors.warning,
  };

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.only(bottom: 130),
      children: [
        const ScreenHeader(),
        Padding(
          padding: const EdgeInsets.fromLTRB(18, 4, 18, 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Pill.text('BRIEFING · HARI INI', monoFont: true),
              const SizedBox(height: 10),
              Text(
                _loading
                    ? 'Memuat briefing harian…'
                    : (_latest != null ? 'Briefing ${_latest!.date}' : 'Belum ada briefing tersimpan'),
                style: display(fontSize: 22, letterSpacing: -0.4, height: 1.2),
              ),
              const SizedBox(height: 4),
              Text(
                _loading
                    ? 'Mengambil data terakhir dari server…'
                    : (_latest != null
                        ? '${_latest!.sections.length} analisis selesai.'
                        : 'Jalankan POST /report/daily/run dari Swagger atau klik "Mulai Briefing" di sesi sebelumnya untuk mengisi.'),
                style: body(fontSize: 12.5, color: FortunasColors.ink3),
              ),
            ],
          ),
        ),
        if (_error != null) _ErrorBanner(message: _error!, onRetry: _fetch),
        if (_loading) _SkeletonBriefing(),
        if (!_loading && _latest != null) ..._buildContent(_latest!),
      ],
    );
  }

  Widget _kpiCardFor(BriefingSection s) => _KpiCard(
        section: s,
        iconName: _iconFor[s.analysisType] ?? 'chart',
        accent: _colorFor[s.analysisType] ?? FortunasColors.violet,
      );

  List<Widget> _buildContent(DailyReportEntry latest) {
    final findings = <String>[];
    for (final s in latest.sections) {
      for (final f in s.topFindings) {
        if (!findings.contains(f)) findings.add(f);
      }
    }

    return [
      // Executive summary dark card
      Padding(
        padding: const EdgeInsets.fromLTRB(18, 0, 18, 12),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(20),
          child: Container(
            decoration: BoxDecoration(
              color: FortunasColors.ink,
              borderRadius: BorderRadius.circular(20),
              boxShadow: popShadow(),
            ),
            padding: const EdgeInsets.fromLTRB(18, 18, 18, 20),
            child: Stack(
              children: [
                Positioned(
                  right: -30, top: -30,
                  child: Container(
                    width: 110, height: 110,
                    decoration: BoxDecoration(
                      color: FortunasColors.lime.withValues(alpha: 0.15),
                      shape: BoxShape.circle,
                    ),
                  ),
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'EXECUTIVE SUMMARY',
                      style: mono(fontSize: 10, color: FortunasColors.lime, letterSpacing: 0.8),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      latest.executiveSummary,
                      style: display(
                        fontSize: 15, weight: FontWeight.w500, height: 1.5,
                        color: Colors.white, letterSpacing: -0.15,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),

      // KPI rows — 2 columns; an odd trailing card spans full width.
      Padding(
        padding: const EdgeInsets.symmetric(horizontal: 18),
        child: Column(
          children: [
            for (final (i, row) in pairRows(latest.sections).indexed) ...[
              if (i > 0) const SizedBox(height: 10),
              SizedBox(
                height: _kpiRowHeight,
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    for (var j = 0; j < row.length; j++) ...[
                      if (j > 0) const SizedBox(width: 10),
                      Expanded(child: _kpiCardFor(row[j])),
                    ],
                  ],
                ),
              ),
            ],
          ],
        ),
      ),

      // Top findings
      Padding(
        padding: const EdgeInsets.fromLTRB(18, 18, 18, 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'TEMUAN UTAMA',
              style: mono(fontSize: 10, color: FortunasColors.ink3, letterSpacing: 0.8),
            ),
            const SizedBox(height: 10),
            for (var i = 0; i < findings.take(3).length; i++) ...[
              _FindingRow(index: i + 1, text: findings[i]),
              const SizedBox(height: 8),
            ],
          ],
        ),
      ),
    ];
  }
}

class _KpiCard extends StatelessWidget {
  final BriefingSection section;
  final String iconName;
  final Color accent;
  const _KpiCard({required this.section, required this.iconName, required this.accent});

  String get _shortKpi {
    final f = section.topFindings.isNotEmpty ? section.topFindings.first : section.summary;
    final match = RegExp(r'(\d[\d.,]*\s*(?:%|jam|orang|trx|item)?)').firstMatch(f);
    if (match != null) return match.group(1)!.trim();
    final tok = section.label.split(' ');
    return tok.length > 1 ? tok[1] : '—';
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: FortunasColors.surface,
        border: Border.all(color: FortunasColors.ink, width: 1.5),
        borderRadius: BorderRadius.circular(16),
        boxShadow: popShadow(offset: 2),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Container(
                width: 28, height: 28,
                decoration: BoxDecoration(
                  color: accent,
                  border: Border.all(color: FortunasColors.ink, width: 1.5),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Center(
                  child: AppIcon(name: iconName, size: 15, color: FortunasColors.ink),
                ),
              ),
              Text(
                section.rowCount > 0 ? '${section.rowCount} row' : '—',
                style: mono(fontSize: 10, color: FortunasColors.success, letterSpacing: 0.4),
              ),
            ],
          ),
          const Spacer(),
          Text(_shortKpi, style: display(fontSize: 18, letterSpacing: -0.4, height: 1.1)),
          const SizedBox(height: 2),
          Text(
            section.label.toUpperCase(),
            style: mono(fontSize: 9.5, color: FortunasColors.ink3, letterSpacing: 0.6),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }
}

class _FindingRow extends StatelessWidget {
  final int index;
  final String text;
  const _FindingRow({required this.index, required this.text});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: FortunasColors.surfaceSoft,
        border: Border.all(color: FortunasColors.borderHair),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 22, height: 22,
            decoration: BoxDecoration(
              color: FortunasColors.ink,
              borderRadius: BorderRadius.circular(6),
            ),
            child: Center(
              child: Text(
                '$index',
                style: mono(fontSize: 10, color: FortunasColors.lime, letterSpacing: 0),
              ),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              text,
              style: body(fontSize: 12.5, color: FortunasColors.ink2, height: 1.5),
            ),
          ),
        ],
      ),
    );
  }
}

class _ErrorBanner extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;
  const _ErrorBanner({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(18, 0, 18, 12),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: FortunasColors.peachSoft,
          border: Border.all(color: FortunasColors.ink, width: 1.5),
          borderRadius: BorderRadius.circular(14),
        ),
        child: Row(
          children: [
            Expanded(child: Text(message, style: body(fontSize: 13))),
            const SizedBox(width: 8),
            TextButton(onPressed: onRetry, child: const Text('Coba lagi')),
          ],
        ),
      ),
    );
  }
}

class _SkeletonBriefing extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 18),
      child: Column(
        children: [
          Container(height: 120, decoration: _skBox()),
          const SizedBox(height: 12),
          Row(children: [
            Expanded(child: Container(height: 100, decoration: _skBox())),
            const SizedBox(width: 10),
            Expanded(child: Container(height: 100, decoration: _skBox())),
          ]),
          const SizedBox(height: 10),
          Row(children: [
            Expanded(child: Container(height: 100, decoration: _skBox())),
            const SizedBox(width: 10),
            Expanded(child: Container(height: 100, decoration: _skBox())),
          ]),
        ],
      ),
    );
  }

  BoxDecoration _skBox() => BoxDecoration(
    color: FortunasColors.surfaceSoft,
    borderRadius: BorderRadius.circular(12),
  );
}
