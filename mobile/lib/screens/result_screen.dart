import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../api/client.dart';
import '../api/errors.dart';
import '../api/models.dart';
import '../theme/tokens.dart';
import '../ui/pill.dart';

/// ResultScreen — fetches POST /ask, renders summary + findings + recs.
/// React equivalent: frontend/src/screens/ResultScreen.jsx
class ResultScreen extends ConsumerStatefulWidget {
  final String question;
  const ResultScreen({super.key, required this.question});

  @override
  ConsumerState<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends ConsumerState<ResultScreen> {
  AskResponse? _data;
  String? _error;
  bool _loading = true;
  String _phase = 'query';   // query → insight
  late final CancelToken _cancel;

  @override
  void initState() {
    super.initState();
    _cancel = CancelToken();
    if (widget.question.isEmpty) {
      // bounce back home on empty
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) context.go('/');
      });
      return;
    }
    _fetch();
    // Heuristic phase flip — backend /ask is not streaming.
    Future.delayed(const Duration(milliseconds: 1200), () {
      if (mounted && _loading) setState(() => _phase = 'insight');
    });
  }

  @override
  void dispose() {
    _cancel.cancel('disposed');
    super.dispose();
  }

  Future<void> _fetch() async {
    try {
      final r = await ref.read(apiProvider).ask(widget.question, cancelToken: _cancel);
      if (!mounted) return;
      setState(() {
        _data = r;
        _loading = false;
        _error = null;
      });
    } catch (e) {
      if (e is DioException && e.type == DioExceptionType.cancel) return;
      if (!mounted) return;
      setState(() {
        _error = humanizeError(e);
        _loading = false;
      });
    }
  }

  static const _phaseLabels = {
    'query':   'Mengambil data dari BigQuery…',
    'insight': 'Membuat insight dengan AI…',
  };

  @override
  Widget build(BuildContext context) {
    final llm = _data?.llmOutput;
    return ListView(
      padding: const EdgeInsets.only(bottom: 30),
      children: [
        // Top bar: back + status pill
        Padding(
          padding: const EdgeInsets.fromLTRB(18, 14, 18, 8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              TextButton.icon(
                onPressed: () => context.canPop() ? context.pop() : context.go('/'),
                icon: const Icon(Icons.arrow_back, size: 18, color: FortunasColors.ink2),
                label: Text('Kembali',
                  style: body(fontSize: 13, weight: FontWeight.w600, color: FortunasColors.ink2),
                ),
                style: TextButton.styleFrom(padding: const EdgeInsets.symmetric(horizontal: 4)),
              ),
              if (llm != null)
                Pill.text(
                  '${_data!.rows.length} BARIS',
                  small: true,
                  monoFont: true,
                  background: FortunasColors.lime,
                ),
            ],
          ),
        ),

        // Question card
        Padding(
          padding: const EdgeInsets.fromLTRB(18, 4, 18, 12),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
            decoration: BoxDecoration(
              color: FortunasColors.surface,
              border: Border.all(color: FortunasColors.ink, width: 1.5),
              borderRadius: BorderRadius.circular(18),
              boxShadow: popShadow(offset: 2),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('PERTANYAAN', style: mono(fontSize: 10, color: FortunasColors.ink3, letterSpacing: 0.8)),
                const SizedBox(height: 6),
                Text(
                  '"${widget.question}"',
                  style: display(
                    fontSize: 15, weight: FontWeight.w500,
                    height: 1.4, letterSpacing: -0.15,
                  ),
                ),
              ],
            ),
          ),
        ),

        if (_loading) _LoadingCard(phase: _phaseLabels[_phase] ?? '…'),

        if (_error != null && !_loading)
          Padding(
            padding: const EdgeInsets.fromLTRB(18, 0, 18, 18),
            child: Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: FortunasColors.peachSoft,
                border: Border.all(color: FortunasColors.ink, width: 1.5),
                borderRadius: BorderRadius.circular(14),
              ),
              child: Text(_error!, style: body(fontSize: 13, color: FortunasColors.ink2)),
            ),
          ),

        if (!_loading && _error == null && llm != null) ...[
          // Violet summary card
          Padding(
            padding: const EdgeInsets.fromLTRB(18, 0, 18, 12),
            child: Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                color: FortunasColors.violet,
                border: Border.all(color: FortunasColors.ink, width: 1.5),
                borderRadius: BorderRadius.circular(18),
                boxShadow: popShadow(offset: 2),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'RINGKASAN · ${_data!.mappedAnalysis.toUpperCase()}',
                    style: mono(
                      fontSize: 10,
                      color: Color(0xBFFFFFFF),
                      letterSpacing: 0.8,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    llm.summary,
                    style: display(
                      fontSize: 16, weight: FontWeight.w500, height: 1.5,
                      color: Colors.white, letterSpacing: -0.15,
                    ),
                  ),
                ],
              ),
            ),
          ),

          if (llm.topFindings.isNotEmpty)
            Padding(
              padding: const EdgeInsets.fromLTRB(18, 0, 18, 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('TEMUAN', style: mono(fontSize: 10, color: FortunasColors.ink3, letterSpacing: 0.8)),
                  const SizedBox(height: 8),
                  for (var i = 0; i < llm.topFindings.length; i++) ...[
                    _NumberedCard(index: i + 1, text: llm.topFindings[i]),
                    const SizedBox(height: 8),
                  ],
                ],
              ),
            ),

          if (llm.recommendation.isNotEmpty)
            Padding(
              padding: const EdgeInsets.fromLTRB(18, 0, 18, 12),
              child: Container(
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(
                  color: FortunasColors.lime,
                  border: Border.all(color: FortunasColors.ink, width: 1.5),
                  borderRadius: BorderRadius.circular(18),
                  boxShadow: popShadow(offset: 2),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'REKOMENDASI',
                      style: mono(fontSize: 10, color: FortunasColors.ink, letterSpacing: 0.8),
                    ),
                    const SizedBox(height: 10),
                    for (final r in llm.recommendation) ...[
                      _RecRow(text: r),
                      const SizedBox(height: 8),
                    ],
                  ],
                ),
              ),
            ),
        ],
      ],
    );
  }
}

class _LoadingCard extends StatelessWidget {
  final String phase;
  const _LoadingCard({required this.phase});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(18, 0, 18, 18),
      child: Container(
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          color: FortunasColors.surface,
          border: Border.all(color: FortunasColors.ink, width: 1.5),
          borderRadius: BorderRadius.circular(18),
          boxShadow: popShadow(offset: 2),
        ),
        child: Row(
          children: [
            SizedBox(
              width: 24, height: 24,
              child: CircularProgressIndicator(
                strokeWidth: 2.5,
                valueColor: const AlwaysStoppedAnimation(FortunasColors.violet),
                backgroundColor: FortunasColors.violetSoft,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                phase,
                style: display(fontSize: 14, weight: FontWeight.w600, letterSpacing: -0.2, height: 1.3),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _NumberedCard extends StatelessWidget {
  final int index;
  final String text;
  const _NumberedCard({required this.index, required this.text});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: FortunasColors.surfaceSoft,
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
              child: Text('$index', style: mono(fontSize: 10, color: FortunasColors.lime, letterSpacing: 0)),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(child: Text(text, style: body(fontSize: 12.5, color: FortunasColors.ink2, height: 1.5))),
        ],
      ),
    );
  }
}

class _RecRow extends StatelessWidget {
  final String text;
  const _RecRow({required this.text});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: const Color(0x8CFFFFFF),
        border: Border.all(color: FortunasColors.ink, width: 1.5),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.arrow_forward, size: 15, color: FortunasColors.ink),
          const SizedBox(width: 10),
          Expanded(
            child: Text(text, style: body(fontSize: 12.5, weight: FontWeight.w500, color: FortunasColors.ink)),
          ),
        ],
      ),
    );
  }
}
