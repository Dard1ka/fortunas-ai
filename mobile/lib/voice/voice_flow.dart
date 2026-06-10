import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../api/client.dart';
import '../api/models.dart';
import '../screens/history_screen.dart' show recentVoiceKey;
import '../theme/tokens.dart';
import '../ui/icon_set.dart';
import '../ui/pill.dart';
import 'speech_controller.dart';
import 'transaction_parser.dart';
import 'voice_idle.dart';
import 'voice_listening.dart';
import 'voice_parsed.dart';
import 'voice_success.dart';

enum VoiceState { idle, listening, parsing, parsed, success }

/// VoiceFlow — full screen modal that orchestrates the voice-to-transaction
/// state machine: idle → listening → parsing → parsed → success.
/// React equivalent: frontend/src/voice/VoiceFlow.jsx
class VoiceFlow extends ConsumerStatefulWidget {
  const VoiceFlow({super.key});

  @override
  ConsumerState<VoiceFlow> createState() => _VoiceFlowState();
}

class _VoiceFlowState extends ConsumerState<VoiceFlow> {
  VoiceState _state = VoiceState.idle;
  ParsedTransaction? _tx;
  String? _error;
  bool _submitting = false;
  bool _forceTyped = false; // user chose to type instead of speak
  late final SpeechController _speech;
  final _fallbackCtl = TextEditingController();
  Timer? _autoCloseTimer;

  /// Use the typed input path when the mic isn't supported OR the user
  /// explicitly switched to manual typing.
  bool get _useTyped => !_speech.isSupported || _forceTyped;

  @override
  void initState() {
    super.initState();
    _speech = SpeechController();
    _speech.addListener(_onSpeechUpdate);
    // Rebuild as the user types (typed fallback) so the confirm button
    // enables/disables based on transcript content.
    _fallbackCtl.addListener(_onSpeechUpdate);
    // Kick off init (also handles mic permission prompt).
    _speech.init();
  }

  @override
  void dispose() {
    _autoCloseTimer?.cancel();
    _speech.removeListener(_onSpeechUpdate);
    _speech.dispose();
    _fallbackCtl.dispose();
    super.dispose();
  }

  void _onSpeechUpdate() {
    if (!mounted) return;
    setState(() {}); // re-render transcript when speech state changes
  }

  Future<void> _startListening() async {
    setState(() {
      _error = null;
      _tx = null;
      _forceTyped = false;
      _fallbackCtl.clear();
      _state = VoiceState.listening;
    });
    if (_speech.isSupported) await _speech.start();
  }

  /// Stop the mic but stay on the listening screen so the user can review
  /// the transcript before confirming.
  Future<void> _stopListening() async {
    if (_speech.isSupported && _speech.isListening) await _speech.stop();
    if (mounted) setState(() {});
  }

  void _switchToTyped() {
    _speech.stop();
    setState(() => _forceTyped = true);
  }

  /// Delete the last word from the current transcript (counted by spaces).
  void _deleteLastWord() {
    if (_useTyped) {
      final words = _fallbackCtl.text.trim().split(RegExp(r'\s+'))
        ..removeWhere((w) => w.isEmpty);
      if (words.isNotEmpty) words.removeLast();
      final next = words.join(' ');
      _fallbackCtl.value = TextEditingValue(
        text: next,
        selection: TextSelection.collapsed(offset: next.length),
      );
      setState(() {});
    } else {
      _speech.deleteLastWord();
    }
  }

  Future<void> _stopAndParse() async {
    if (_speech.isSupported && _speech.isListening) await _speech.stop();
    final transcript =
        (_useTyped ? _fallbackCtl.text : _speech.transcript).trim();

    setState(() => _state = VoiceState.parsing);

    // Smart on-device parsing — segments the utterance into one or more
    // line items. Brief delay keeps the "AI mengurai…" feedback visible.
    await Future<void>.delayed(const Duration(milliseconds: 650));
    var parsed = TransactionParser.parse(transcript);

    if (!mounted) return;
    // Always advance to A04. If nothing could be extracted, hand over one
    // blank, editable item so the user can fill it in instead of being
    // bounced back to the listening screen.
    if (parsed.items.isEmpty) {
      parsed = parsed.copyWith(
        items: const [LineItem(product: '', qty: 1, unitPrice: 0)],
      );
    }
    setState(() {
      _tx = parsed;
      _state = VoiceState.parsed;
    });
  }

  Future<void> _confirmSave() async {
    final tx = _tx;
    if (tx == null || tx.items.isEmpty) return;
    setState(() {
      _submitting = true;
      _error = null;
    });

    // Best-effort: push each line item to the backend. The app is also a
    // standalone simulator, so network failure does NOT block the save —
    // items are always persisted to local history.
    final api = ref.read(apiProvider);
    for (final payload in tx.toTransactionPayloads()) {
      try {
        await api.voiceTransaction(payload);
      } catch (_) {
        /* offline / backend down — still saved locally below */
      }
    }

    await _persistToHistory(tx);
    if (!mounted) return;
    setState(() {
      _submitting = false;
      _state = VoiceState.success;
    });
    _autoCloseTimer = Timer(const Duration(milliseconds: 2400), () {
      if (mounted && context.canPop()) context.pop();
    });
  }

  Future<void> _persistToHistory(ParsedTransaction tx) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getString(recentVoiceKey);
      final List existing = raw != null ? (jsonDecode(raw) as List) : [];
      final savedAt = DateTime.now().toUtc().toIso8601String();
      // One history row per line item (history list stays single-item shape).
      final entries = [
        for (final payload in tx.toTransactionPayloads())
          {...payload, 'savedAt': savedAt}
      ];
      final next = [...entries, ...existing].take(30).toList();
      await prefs.setString(recentVoiceKey, jsonEncode(next));
    } catch (_) {
      /* non-fatal */
    }
  }

  void _reset() {
    setState(() {
      _error = null;
      _tx = null;
      _forceTyped = false;
      _fallbackCtl.clear();
      _state = VoiceState.idle;
    });
    _speech.reset();
  }

  String _titleForState() {
    switch (_state) {
      case VoiceState.idle:      return 'TAMBAH TRANSAKSI';
      case VoiceState.listening: return 'MENDENGAR…';
      case VoiceState.parsing:   return 'AI MEMBACA…';
      case VoiceState.parsed:    return 'KONFIRMASI';
      case VoiceState.success:   return 'TERSIMPAN';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: FortunasColors.bg,
      body: SafeArea(
        child: Column(
          children: [
            _Header(
              title: _titleForState(),
              isSuccess: _state == VoiceState.success,
              onClose: () => context.canPop() ? context.pop() : null,
            ),
            Expanded(child: _buildBody()),
          ],
        ),
      ),
    );
  }

  Widget _buildBody() {
    switch (_state) {
      case VoiceState.idle:
        return VoiceIdle(
          onStart: _startListening,
          supported: _speech.isSupported,
        );
      case VoiceState.listening:
      case VoiceState.parsing:
        final useTyped = _useTyped;
        final transcript = useTyped ? _fallbackCtl.text : _speech.transcript;
        return VoiceListening(
          state: _state == VoiceState.parsing ? 'parsing' : 'listening',
          transcript: transcript,
          supported: !useTyped,
          isListening: _speech.isListening,
          canConfirm: true, // always allow advancing to the review screen (A04)
          micError: useTyped ? null : _speech.error,
          textController: useTyped ? _fallbackCtl : null,
          onStop: _stopListening,
          onConfirm: _stopAndParse,
          onSwitchToTyped: _speech.isSupported && !_forceTyped ? _switchToTyped : null,
          onBackspace: _deleteLastWord,
        );
      case VoiceState.parsed:
        return VoiceParsed(
          tx: _tx!,
          submitting: _submitting,
          error: _error,
          onChange: (next) => setState(() => _tx = next),
          onRetry: _reset,
          onConfirm: _confirmSave,
        );
      case VoiceState.success:
        return VoiceSuccess(tx: _tx);
    }
  }
}

class _Header extends StatelessWidget {
  final String title;
  final bool isSuccess;
  final VoidCallback? onClose;

  const _Header({required this.title, required this.isSuccess, this.onClose});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(18, 12, 18, 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Material(
            color: Colors.transparent,
            child: InkWell(
              onTap: onClose,
              borderRadius: BorderRadius.circular(12),
              child: Container(
                width: 36, height: 36,
                decoration: BoxDecoration(
                  color: FortunasColors.surface,
                  border: Border.all(color: FortunasColors.ink, width: 1.5),
                  borderRadius: BorderRadius.circular(12),
                  boxShadow: popShadow(offset: 2),
                ),
                child: const Center(child: AppIcon(name: 'close', size: 16, color: FortunasColors.ink)),
              ),
            ),
          ),
          Pill.text(
            title,
            small: true, monoFont: true,
            background: isSuccess ? FortunasColors.lime : FortunasColors.surface,
          ),
          const SizedBox(width: 36),
        ],
      ),
    );
  }
}
