import 'package:flutter/material.dart';

import '../theme/tokens.dart';
import '../ui/pill.dart';
import 'big_mic_button.dart';

/// VoiceIdle — CTA + sample phrasing.
/// React equivalent: frontend/src/voice/VoiceIdle.jsx
class VoiceIdle extends StatelessWidget {
  final VoidCallback onStart;
  final bool supported;

  const VoiceIdle({super.key, required this.onStart, this.supported = true});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(24, 20, 24, 80),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Pill.text('NEW · VOICE INPUT', monoFont: true),
          const SizedBox(height: 14),
          Text.rich(
            textAlign: TextAlign.center,
            TextSpan(
              children: [
                TextSpan(
                  text: 'Catat transaksi ',
                  style: display(fontSize: 26, letterSpacing: -0.8, height: 1.1),
                ),
                TextSpan(
                  text: 'tanpa ngetik.',
                  style: display(
                    fontSize: 26, letterSpacing: -0.8, height: 1.1,
                    color: FortunasColors.violet,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),
          ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 280),
            child: Text(
              'Sebut nomor invoice, produk, jumlah, dan harga. AI akan memformat sendiri.',
              textAlign: TextAlign.center,
              style: body(fontSize: 13.5, color: FortunasColors.ink3),
            ),
          ),
          const SizedBox(height: 28),
          BigMicButton(state: 'idle', onTap: onStart),
          const SizedBox(height: 16),
          Text(
            'KETUK TOMBOL UNTUK MULAI',
            style: mono(fontSize: 11, color: FortunasColors.ink3, letterSpacing: 0.4),
          ),
          if (!supported) ...[
            const SizedBox(height: 16),
            ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 320),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  color: FortunasColors.peachSoft,
                  border: Border.all(color: FortunasColors.ink, width: 1.5),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  'Speech recognition tidak tersedia di device ini. Pakai keyboard di langkah berikutnya.',
                  style: body(fontSize: 11.5, color: FortunasColors.ink2, height: 1.45),
                  textAlign: TextAlign.center,
                ),
              ),
            ),
          ],
          const SizedBox(height: 28),
          ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 320),
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: FortunasColors.surface,
                border: Border.all(color: FortunasColors.borderSoft, width: 1.5),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('CONTOH UCAPAN',
                    style: mono(fontSize: 9.5, color: FortunasColors.ink3, letterSpacing: 0.8),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    '"Invoice INV-2024, sabun cuci, qty 10, harga delapan ribu lima ratus."',
                    style: body(fontSize: 12.5, color: FortunasColors.ink2, height: 1.55),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
