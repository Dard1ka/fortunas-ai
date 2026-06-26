import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../theme/tokens.dart';
import '../ui/example_chip.dart';
import '../ui/mode_tabs.dart';
import '../ui/pill.dart';
import '../ui/screen_header.dart';

/// HomeScreen — Tanya AI (primary entry).
/// React equivalent: frontend/src/screens/HomeScreen.jsx (line 6-123 in
/// _decoded_assets/9bbcc94e-…jsx).
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  String _tab = 'tanya';
  final _textController = TextEditingController();

  @override
  void dispose() {
    _textController.dispose();
    super.dispose();
  }

  void _submit([String? overrideText]) {
    final q = (overrideText ?? _textController.text).trim();
    if (q.isEmpty) return;
    context.go('/result?q=${Uri.encodeQueryComponent(q)}');
  }

  void _openVoice() => context.push('/voice');

  void _openCheckout() => context.push('/checkout');

  void _openScan() => context.push('/scan');

  static const _exampleQuestions = [
    'Siapa pelanggan paling setia bulan ini?',
    'Jam berapa toko paling rame?',
    'Produk apa yang sering dibeli bareng?',
  ];

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.only(bottom: 30),
      children: [
        const ScreenHeader(),

        // ── Hero ────────────────────────────────────
        Padding(
          padding: const EdgeInsets.fromLTRB(18, 4, 18, 14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Pill.text('Analytics tanpa ribet'),
              const SizedBox(height: 12),
              Text.rich(
                TextSpan(
                  children: [
                    TextSpan(
                      text: 'Pahami bisnismu, ',
                      style: display(
                        fontSize: 26, weight: FontWeight.w700,
                        letterSpacing: -0.9, height: 1.08,
                      ),
                    ),
                    TextSpan(
                      text: 'bukan cuma buka tokonya.',
                      style: display(
                        fontSize: 26, weight: FontWeight.w700,
                        letterSpacing: -0.9, height: 1.08,
                        color: FortunasColors.violetDeep,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Tanya pakai suara atau ketik — AI lokal langsung kasih jawaban + rekomendasi.',
                style: body(fontSize: 13, color: FortunasColors.ink3),
              ),
            ],
          ),
        ),

        // ── Mode tabs ───────────────────────────────
        Align(
          alignment: Alignment.centerLeft,
          child: ModeTabs(
            value: _tab,
            onChanged: (v) => setState(() => _tab = v),
            tabs: const [
              (id: 'tanya',    label: 'Tanya'),
              (id: 'briefing', label: 'Briefing'),
              (id: 'harian',   label: 'Harian'),
            ],
          ),
        ),

        // ── Input row ───────────────────────────────
        Padding(
          padding: const EdgeInsets.fromLTRB(18, 18, 18, 0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                decoration: BoxDecoration(
                  color: FortunasColors.surface,
                  border: Border.all(color: FortunasColors.ink, width: 2),
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: popShadow(offset: 4),
                ),
                padding: const EdgeInsets.all(6),
                child: Row(
                  children: [
                    _MicButton(onTap: _openVoice),
                    const SizedBox(width: 8),
                    Expanded(
                      child: TextField(
                        controller: _textController,
                        onSubmitted: (_) => _submit(),
                        textInputAction: TextInputAction.send,
                        style: body(
                          fontSize: 14, color: FortunasColors.ink,
                        ),
                        decoration: InputDecoration(
                          hintText: 'Tanya apa aja soal bisnismu...',
                          hintStyle: body(
                            fontSize: 14, color: FortunasColors.ink4,
                          ),
                          isDense: true,
                          border: InputBorder.none,
                          enabledBorder: InputBorder.none,
                          focusedBorder: InputBorder.none,
                          contentPadding: const EdgeInsets.symmetric(
                            horizontal: 4, vertical: 8,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    _SendButton(onTap: _submit),
                  ],
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'TIP · Tekan ikon mic untuk pakai suara',
                style: mono(
                  fontSize: 10, color: FortunasColors.ink3, letterSpacing: 0.4,
                ),
              ),
            ],
          ),
        ),

        // ── Examples ────────────────────────────────
        Padding(
          padding: const EdgeInsets.fromLTRB(18, 18, 18, 0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'CONTOH PERTANYAAN',
                style: mono(
                  fontSize: 10, color: FortunasColors.ink3, letterSpacing: 0.8,
                ),
              ),
              const SizedBox(height: 10),
              for (final q in _exampleQuestions) ...[
                ExampleChip(text: q, onTap: () => _submit(q)),
                const SizedBox(height: 8),
              ],
            ],
          ),
        ),

        // ── Quick action: Tambah Transaksi ──────────
        Padding(
          padding: const EdgeInsets.fromLTRB(18, 10, 18, 0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'AKSI CEPAT',
                style: mono(
                  fontSize: 10, color: FortunasColors.ink3, letterSpacing: 0.8,
                ),
              ),
              const SizedBox(height: 10),
              _QuickActionCard(
                title: 'Tambah Transaksi',
                subtitle: 'Voice langsung aktif · Hands-free',
                icon: Icons.add,
                iconBg: FortunasColors.lime,
                onTap: _openVoice,
              ),
              const SizedBox(height: 10),
              _QuickActionCard(
                title: 'Kasir',
                subtitle: 'Catat penjualan multi-item',
                icon: Icons.point_of_sale,
                iconBg: FortunasColors.sky,
                onTap: _openCheckout,
              ),
              const SizedBox(height: 10),
              _QuickActionCard(
                key: const Key('home_scan'),
                title: 'Scan QR Pelanggan',
                subtitle: 'Daftarkan pelanggan jadi member',
                icon: Icons.qr_code_scanner,
                iconBg: FortunasColors.lime,
                onTap: _openScan,
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _MicButton extends StatelessWidget {
  final VoidCallback onTap;
  const _MicButton({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(14),
        child: Container(
          width: 42, height: 42,
          decoration: BoxDecoration(
            color: FortunasColors.violet,
            border: Border.all(color: FortunasColors.ink, width: 1.5),
            borderRadius: BorderRadius.circular(14),
            boxShadow: popShadow(offset: 2),
          ),
          child: const Icon(Icons.mic, color: Colors.white, size: 20),
        ),
      ),
    );
  }
}

class _SendButton extends StatelessWidget {
  final VoidCallback onTap;
  const _SendButton({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(14),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          decoration: BoxDecoration(
            color: FortunasColors.violet,
            border: Border.all(color: FortunasColors.ink, width: 1.5),
            borderRadius: BorderRadius.circular(14),
            boxShadow: popShadow(offset: 2),
          ),
          child: const Icon(Icons.arrow_forward, color: Colors.white, size: 16),
        ),
      ),
    );
  }
}

class _QuickActionCard extends StatelessWidget {
  final String title;
  final String subtitle;
  final IconData icon;
  final Color iconBg;
  final VoidCallback onTap;
  const _QuickActionCard({
    super.key,
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.iconBg,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(FortunasRadius.lg),
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: FortunasColors.ink,
            border: Border.all(color: FortunasColors.ink, width: 1.5),
            borderRadius: BorderRadius.circular(FortunasRadius.lg),
            boxShadow: popShadow(offset: 3),
          ),
          child: Row(
            children: [
              Container(
                width: 40, height: 40,
                decoration: BoxDecoration(
                  color: iconBg,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, color: FortunasColors.ink, size: 22),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(title,
                        style: display(
                          fontSize: 14, weight: FontWeight.w600,
                          color: Colors.white, letterSpacing: -0.3, height: 1.2,
                        )),
                    const SizedBox(height: 2),
                    Text(subtitle, style: body(fontSize: 11, color: const Color(0xB3FFFFFF))),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right, color: Colors.white, size: 18),
            ],
          ),
        ),
      ),
    );
  }
}
