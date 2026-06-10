import 'package:flutter/material.dart';

import '../theme/tokens.dart';
import 'typed_transcript.dart';
import 'waveform.dart';

/// VoiceListening — transcript card + waveform + stop button.
/// Also shows parsing overlay when state == 'parsing'.
/// React equivalent: frontend/src/voice/VoiceListening.jsx
class VoiceListening extends StatelessWidget {
  /// 'listening' | 'parsing'
  final String state;
  final String transcript;
  final bool supported;
  final bool isListening;
  final bool canConfirm;
  final String? micError;
  final TextEditingController? textController;
  final VoidCallback onStop;
  final VoidCallback onConfirm;
  final VoidCallback? onSwitchToTyped;
  final VoidCallback? onBackspace;

  const VoiceListening({
    super.key,
    required this.state,
    required this.transcript,
    required this.onStop,
    required this.onConfirm,
    this.isListening = true,
    this.canConfirm = false,
    this.micError,
    this.supported = true,
    this.textController,
    this.onSwitchToTyped,
    this.onBackspace,
  });

  @override
  Widget build(BuildContext context) {
    final parsing = state == 'parsing';
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(22, 20, 22, 0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Live transcript card
              Container(
                padding: const EdgeInsets.fromLTRB(18, 18, 18, 20),
                decoration: BoxDecoration(
                  color: FortunasColors.surface,
                  border: Border.all(color: FortunasColors.ink, width: 1.5),
                  borderRadius: BorderRadius.circular(18),
                  boxShadow: popShadow(offset: 2),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            _PulsingDot(color: parsing ? FortunasColors.violet : FortunasColors.error),
                            const SizedBox(width: 8),
                            Text(
                              parsing ? 'MENGURAI…' : 'LIVE TRANSKRIP',
                              style: mono(fontSize: 10, color: FortunasColors.ink3, letterSpacing: 0.8),
                            ),
                          ],
                        ),
                        Text('id-ID', style: mono(fontSize: 10, color: FortunasColors.ink3, letterSpacing: 0)),
                      ],
                    ),
                    const SizedBox(height: 10),
                    if (supported)
                      TypedTranscript(text: transcript)
                    else
                      TextField(
                        controller: textController,
                        maxLines: 4,
                        style: body(fontSize: 14, color: FortunasColors.ink),
                        decoration: InputDecoration(
                          hintText:
                              'Ketik transaksi: Invoice INV-2024, sabun cuci, qty 10, harga 8500',
                          hintStyle: body(fontSize: 13, color: FortunasColors.ink3),
                          filled: true,
                          fillColor: FortunasColors.surfaceSoft,
                          enabledBorder: OutlineInputBorder(
                            borderSide: const BorderSide(color: FortunasColors.ink, width: 1.5),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          focusedBorder: OutlineInputBorder(
                            borderSide: const BorderSide(color: FortunasColors.violet, width: 1.5),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                        ),
                      ),
                  ],
                ),
              ),

              if (supported) ...[
                const SizedBox(height: 14),
                // Backspace — delete the last spoken word.
                Align(
                  alignment: Alignment.centerRight,
                  child: _BackspaceButton(
                    enabled: !parsing && transcript.trim().isNotEmpty && onBackspace != null,
                    onTap: onBackspace,
                  ),
                ),
                const SizedBox(height: 10),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                  decoration: BoxDecoration(
                    color: FortunasColors.ink,
                    border: Border.all(color: FortunasColors.ink, width: 1.5),
                    borderRadius: BorderRadius.circular(18),
                    boxShadow: popShadow(offset: 2),
                  ),
                  child: Waveform(active: !parsing, color: FortunasColors.lime),
                ),
              ],

              if (parsing) ...[
                const SizedBox(height: 14),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                  decoration: BoxDecoration(
                    color: FortunasColors.violetSoft,
                    border: Border.all(color: FortunasColors.violet, width: 1.5),
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: Row(
                    children: [
                      const SizedBox(
                        width: 24, height: 24,
                        child: CircularProgressIndicator(
                          strokeWidth: 2.5,
                          valueColor: AlwaysStoppedAnimation(FortunasColors.violet),
                          backgroundColor: FortunasColors.violetSoft,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text('AI mengurai transaksi…',
                              style: display(fontSize: 13.5, weight: FontWeight.w600, letterSpacing: -0.2),
                            ),
                            const SizedBox(height: 2),
                            Text('Local LLM · Qwen3:8b',
                              style: body(fontSize: 11.5, color: FortunasColors.ink3),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ),

        // ── Mic error banner ─────────────────────────────────────
        if (micError != null)
          Padding(
            padding: const EdgeInsets.fromLTRB(22, 16, 22, 0),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
              decoration: BoxDecoration(
                color: FortunasColors.peachSoft,
                border: Border.all(color: FortunasColors.ink, width: 1.5),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                children: [
                  const Icon(Icons.error_outline, size: 18, color: FortunasColors.ink),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(micError!,
                        style: body(fontSize: 12.5, color: FortunasColors.ink2, height: 1.4)),
                  ),
                ],
              ),
            ),
          ),

        // ── Switch to manual typing (escape hatch) ───────────────
        if (supported && onSwitchToTyped != null)
          Padding(
            padding: const EdgeInsets.fromLTRB(22, 14, 22, 0),
            child: Center(
              child: Material(
                color: Colors.transparent,
                child: InkWell(
                  onTap: onSwitchToTyped,
                  borderRadius: BorderRadius.circular(10),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.keyboard_outlined, size: 16, color: FortunasColors.violetDeep),
                        const SizedBox(width: 8),
                        Text('Mic tidak jalan? Ketik manual',
                            style: body(fontSize: 12.5, weight: FontWeight.w600, color: FortunasColors.violetDeep)),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),

        const Spacer(),

        // ── Stop recording button (only while mic is active) ─────
        if (supported) ...[
          Padding(
            padding: const EdgeInsets.fromLTRB(22, 0, 22, 8),
            child: Center(
              child: Material(
                color: Colors.transparent,
                child: InkWell(
                  onTap: (parsing || !isListening) ? null : onStop,
                  borderRadius: BorderRadius.circular(28),
                  child: Container(
                    width: 56, height: 56,
                    decoration: BoxDecoration(
                      color: (parsing || !isListening)
                          ? FortunasColors.ink4
                          : FortunasColors.error,
                      shape: BoxShape.circle,
                      border: Border.all(color: FortunasColors.ink, width: 2),
                      boxShadow: popShadow(offset: 3),
                    ),
                    child: const Center(
                      child: SizedBox(
                        width: 16, height: 16,
                        child: DecoratedBox(
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.all(Radius.circular(3)),
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(22, 0, 22, 10),
            child: Center(
              child: Text(
                parsing
                    ? 'MOHON TUNGGU…'
                    : isListening
                        ? 'KETUK TOMBOL STOP SAAT SELESAI'
                        : 'REKAMAN BERHENTI · KONFIRMASI DI BAWAH',
                style: mono(fontSize: 11, color: FortunasColors.ink3, letterSpacing: 0.4),
              ),
            ),
          ),
        ],

        // ── Confirm button → parse & go to A04 ───────────────────
        Padding(
          padding: EdgeInsets.fromLTRB(22, supported ? 0 : 8, 22, 22),
          child: _ConfirmButton(
            enabled: canConfirm && !parsing,
            parsing: parsing,
            onTap: onConfirm,
          ),
        ),
      ],
    );
  }
}

class _BackspaceButton extends StatelessWidget {
  final bool enabled;
  final VoidCallback? onTap;
  const _BackspaceButton({required this.enabled, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Opacity(
      opacity: enabled ? 1.0 : 0.45,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: enabled ? onTap : null,
          borderRadius: BorderRadius.circular(10),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: FortunasColors.surface,
              border: Border.all(color: FortunasColors.ink, width: 1.5),
              borderRadius: BorderRadius.circular(10),
              boxShadow: popShadow(offset: 2),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.backspace_outlined, size: 15, color: FortunasColors.ink),
                const SizedBox(width: 7),
                Text('Hapus kata',
                    style: body(fontSize: 12, weight: FontWeight.w600, color: FortunasColors.ink)),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _ConfirmButton extends StatelessWidget {
  final bool enabled;
  final bool parsing;
  final VoidCallback onTap;

  const _ConfirmButton({
    required this.enabled,
    required this.parsing,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Opacity(
      opacity: enabled ? 1.0 : 0.5,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: enabled ? onTap : null,
          borderRadius: BorderRadius.circular(16),
          child: Container(
            padding: const EdgeInsets.symmetric(vertical: 16),
            decoration: BoxDecoration(
              color: FortunasColors.ink,
              border: Border.all(color: FortunasColors.ink, width: 1.5),
              borderRadius: BorderRadius.circular(16),
              boxShadow: popShadow(offset: 4),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                if (parsing)
                  const SizedBox(
                    width: 18, height: 18,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor: AlwaysStoppedAnimation(FortunasColors.lime),
                    ),
                  )
                else
                  const Icon(Icons.check, size: 18, color: FortunasColors.lime),
                const SizedBox(width: 8),
                Text(
                  parsing ? 'Mengurai…' : 'Konfirmasi & Lihat Barang',
                  style: body(fontSize: 14, weight: FontWeight.w700, color: FortunasColors.lime),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _PulsingDot extends StatefulWidget {
  final Color color;
  const _PulsingDot({required this.color});

  @override
  State<_PulsingDot> createState() => _PulsingDotState();
}

class _PulsingDotState extends State<_PulsingDot>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: Tween<double>(begin: 0.4, end: 1.0).animate(_ctrl),
      child: Container(
        width: 8, height: 8,
        decoration: BoxDecoration(color: widget.color, shape: BoxShape.circle),
      ),
    );
  }
}
