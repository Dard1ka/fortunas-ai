import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../api/client.dart';
import '../auth/auth_controller.dart';
import '../theme/tokens.dart';
import '../ui/icon_set.dart';
import '../ui/pill.dart';
import '../ui/screen_header.dart';

/// ProfileScreen — AI status, data storage, team, settings.
/// React equivalent: frontend/src/screens/ProfileScreen.jsx
class ProfileScreen extends ConsumerStatefulWidget {
  const ProfileScreen({super.key});

  @override
  ConsumerState<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends ConsumerState<ProfileScreen> {
  bool? _online;
  String? _errorMessage;

  static const _team = [
    ('Gregorius Darrel Andika Setya', 'Backend · Frontend · Pipeline'),
    ('Filo Alvian Ongky',             'Tim Riset'),
    ('Go Steven Sanjaya',             'Tim Riset'),
    ('Michael Ivan Santoso',          'Tim Riset'),
  ];

  @override
  void initState() {
    super.initState();
    _checkHealth();
  }

  Future<void> _checkHealth() async {
    try {
      await ref.read(apiProvider).health();
      if (mounted) setState(() => _online = true);
    } catch (e) {
      if (mounted) {
        setState(() {
          _online = false;
          _errorMessage = 'Tidak dapat terhubung ke backend.';
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.only(bottom: 30),
      children: [
        const ScreenHeader(subtitle: 'Pengaturan'),
        Padding(
          padding: const EdgeInsets.fromLTRB(18, 4, 18, 14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Pill.text('SAYA', background: FortunasColors.sky, monoFont: true),
              const SizedBox(height: 10),
              Text('Fortunas AI · v2.2',
                style: display(fontSize: 22, letterSpacing: -0.4, height: 1.2)),
              const SizedBox(height: 4),
              Text(
                'Status engine, info tim, dan pengaturan tampilan.',
                style: body(fontSize: 12.5, color: FortunasColors.ink3),
              ),
            ],
          ),
        ),

        Builder(builder: (context) {
          final account = ref.watch(authControllerProvider).account;
          return _Card(kicker: 'AKUN', children: [
            _Row(label: 'BISNIS', value: account?.tenantName ?? '—'),
            _Row(label: 'EMAIL', value: account?.email ?? '—'),
            _Row(label: 'PREFIX', value: account?.tablePrefix ?? '—', useMonoFont: true),
          ]);
        }),
        Padding(
          padding: const EdgeInsets.fromLTRB(18, 0, 18, 14),
          child: OutlinedButton(
            onPressed: () => ref.read(authControllerProvider.notifier).logout(),
            child: const Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.logout, size: 18),
                SizedBox(width: 8),
                Text('Keluar'),
              ],
            ),
          ),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(18, 0, 18, 14),
          child: ElevatedButton(
            key: const Key('profile_dpa_button'),
            onPressed: () => context.push('/dpa'),
            child: const Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.shield_outlined, size: 18),
                SizedBox(width: 8),
                Text('Atur Pagar AI'),
              ],
            ),
          ),
        ),

        _Card(kicker: 'AI ENGINE', children: [
          _Row(label: 'MODEL', value: 'Qwen3:8b · Ollama lokal'),
          _Row(
            label: 'STATUS',
            valueWidget: _online == null
              ? Text('Memeriksa…', style: body(fontSize: 12.5))
              : Text(
                  _online! ? 'Online' : 'Offline',
                  style: body(
                    fontSize: 12.5,
                    weight: FontWeight.w600,
                    color: _online! ? FortunasColors.success : FortunasColors.error,
                  ),
                ),
          ),
          _Row(label: 'BAHASA', value: 'Bahasa Indonesia + multibahasa'),
        ]),

        _Card(kicker: 'PENYIMPANAN DATA', children: const [
          _Row(label: 'AUDIT', value: 'Google Sheets staging', useMonoFont: true),
          _Row(label: 'WAREHOUSE', value: 'BigQuery · online_retail', useMonoFont: true),
          _Row(label: 'VECTOR DB', value: 'ChromaDB · umkm_knowledge', useMonoFont: true),
        ]),

        _Card(
          kicker: 'TIM FORTUNAS AI',
          children: [
            for (final m in _team) _Row(label: m.$2.toUpperCase(), value: m.$1),
          ],
        ),

        // Compliance banner
        Padding(
          padding: const EdgeInsets.fromLTRB(18, 6, 18, 28),
          child: Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: FortunasColors.violet,
              border: Border.all(color: FortunasColors.ink, width: 1.5),
              borderRadius: BorderRadius.circular(14),
              boxShadow: popShadow(offset: 2),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const AppIcon(name: 'bolt', size: 18, color: FortunasColors.lime),
                const SizedBox(width: 12),
                Expanded(
                  child: Text.rich(
                    TextSpan(
                      children: [
                        TextSpan(
                          text: 'Data tidak meninggalkan server.',
                          style: body(fontSize: 11.5, weight: FontWeight.w700, color: Colors.white, height: 1.55),
                        ),
                        TextSpan(
                          text: ' LLM lokal via Ollama. Sesuai UU PDP No. 27/2022.',
                          style: body(fontSize: 11.5, color: Colors.white, height: 1.55),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),

        if (_errorMessage != null)
          Padding(
            padding: const EdgeInsets.fromLTRB(18, 0, 18, 14),
            child: Text(_errorMessage!, style: body(fontSize: 12, color: FortunasColors.error)),
          ),
      ],
    );
  }
}

class _Card extends StatelessWidget {
  final String kicker;
  final List<Widget> children;
  const _Card({required this.kicker, required this.children});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(18, 0, 18, 12),
      child: Container(
        padding: const EdgeInsets.fromLTRB(16, 14, 16, 6),
        decoration: BoxDecoration(
          color: FortunasColors.surface,
          border: Border.all(color: FortunasColors.ink, width: 1.5),
          borderRadius: BorderRadius.circular(18),
          boxShadow: popShadow(offset: 2),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(kicker, style: mono(fontSize: 10, color: FortunasColors.ink3, letterSpacing: 0.8)),
            const SizedBox(height: 10),
            ...children,
          ],
        ),
      ),
    );
  }
}

class _Row extends StatelessWidget {
  final String label;
  final String? value;
  final Widget? valueWidget;
  final bool useMonoFont;
  const _Row({required this.label, this.value, this.valueWidget, this.useMonoFont = false});

  @override
  Widget build(BuildContext context) {
    final valueStyle = useMonoFont
        ? mono(fontSize: 12.5, color: FortunasColors.ink2, letterSpacing: 0.2)
        : body(fontSize: 12.5, color: FortunasColors.ink2, height: 1.5);

    return Container(
      padding: const EdgeInsets.symmetric(vertical: 8),
      decoration: const BoxDecoration(
        border: Border(top: BorderSide(color: FortunasColors.borderSoft, width: 1)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 110,
            child: Text(
              label,
              style: mono(fontSize: 10.5, color: FortunasColors.ink3, letterSpacing: 0.4),
            ),
          ),
          Expanded(
            child: valueWidget ?? Text(value ?? '', style: valueStyle),
          ),
        ],
      ),
    );
  }
}
