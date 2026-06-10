import 'package:flutter/foundation.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:speech_to_text/speech_recognition_result.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;

/// Wraps the `speech_to_text` plugin into a clean controller surface.
/// React equivalent: frontend/src/voice/useSpeechRecognition.js
///
/// Privacy note (same as Web Speech API): Android routes audio to Google
/// Cloud STT; iOS 15+ runs on-device. Documented in AI_CONTEXT §4b.
///
/// ── How the transcript stays correct across manual edits ──────────────
/// The engine delivers its FULL cumulative session text on every result
/// (web especially), and we cannot edit the engine's internal buffer. So:
///
///   transcript = _committed + (_session with _engineBase prefix removed)
///
///   • _committed  — text the user has locked in (edits, prior segments);
///                   immune to the engine re-sending its buffer.
///   • _session    — the engine's current full cumulative text (REPLACE
///                   each result → interim refinement "16"→"160"→"16000"
///                   works without fragmenting).
///   • _engineBase — the engine text captured at the last edit. We subtract
///                   it as a prefix, so only NEW speech after the edit is
///                   appended. Deleting a word then re-saying it (even the
///                   same words) no longer duplicates — and there is NO
///                   engine restart, so no audio gap.
class SpeechController extends ChangeNotifier {
  final stt.SpeechToText _stt = stt.SpeechToText();

  bool _isSupported = false;
  bool _isListening = false;
  bool _initialized = false;
  bool _disposed = false;

  // Nullable + null-coalescing reads keep this crash-proof even across a
  // hot reload that preserves an older controller instance.
  String? _committed;
  String? _engineBase;
  String? _session;
  String? _error;

  void _safeNotify() {
    if (_disposed) return;
    notifyListeners();
  }

  bool get isSupported => _isSupported;
  bool get isListening => _isListening;
  String? get error => _error;

  /// Current full transcript = committed text + new speech since last edit.
  String get transcript {
    final committed = _committed ?? '';
    final session = _session ?? '';
    final base = _engineBase ?? '';

    String delta;
    if (base.isEmpty || session.startsWith(base)) {
      delta = session.substring(base.length);
    } else {
      // Engine revised earlier text — subtract the longest common prefix.
      delta = session.substring(_commonPrefixLen(session, base));
    }

    final c = committed.trim();
    final d = delta.trim();
    if (c.isEmpty) return d;
    if (d.isEmpty) return c;
    return '$c $d';
  }

  static int _commonPrefixLen(String a, String b) {
    final n = a.length < b.length ? a.length : b.length;
    var i = 0;
    while (i < n && a.codeUnitAt(i) == b.codeUnitAt(i)) {
      i++;
    }
    return i;
  }

  Future<bool> init() async {
    // Request mic permission. On web this is a no-op / handled by the
    // browser's getUserMedia prompt when recognition starts, so don't
    // hard-block on a non-granted status there.
    try {
      final micPerm = await Permission.microphone.request();
      if (!kIsWeb && !micPerm.isGranted) {
        _error = 'Izin mikrofon belum diberikan. Aktifkan di pengaturan.';
        _isSupported = false;
        _safeNotify();
        return false;
      }
    } catch (_) {
      /* permission_handler may be unavailable on web — continue */
    }

    try {
      _isSupported = await _stt.initialize(
        onError: (err) {
          _error = _humanizeSttError(err.errorMsg);
          _isListening = false;
          _safeNotify();
        },
        onStatus: (status) {
          if (status == 'done' || status == 'notListening') {
            _isListening = false; // keep the transcript; just mark stopped
            _safeNotify();
          }
        },
        debugLogging: kDebugMode,
      );
    } catch (e) {
      _error = e.toString();
      _isSupported = false;
    }
    _initialized = true;
    _safeNotify();
    return _isSupported;
  }

  Future<void> start() async {
    if (!_initialized || !_isSupported) {
      final ok = await init();
      if (!ok) return;
    }
    _committed = '';
    _engineBase = '';
    _session = '';
    _error = null;
    _isListening = true;
    _safeNotify();

    try {
      await _stt.listen(
        localeId: 'id_ID', // the value that reliably detects Indonesian here
        listenOptions: stt.SpeechListenOptions(
          partialResults: true,
          listenMode: stt.ListenMode.dictation,
          cancelOnError: false,
          // Keep capturing through natural pauses so a whole sentence is
          // transcribed instead of cutting off after a short silence.
          listenFor: const Duration(minutes: 5),
          pauseFor: const Duration(seconds: 20),
        ),
        onResult: _onResult,
      );
    } catch (e) {
      _error = _humanizeSttError(e.toString());
      _isListening = false;
      _safeNotify();
    }
  }

  String _humanizeSttError(String raw) {
    final m = raw.toLowerCase();
    if (m.contains('not-allowed') || m.contains('not_allowed') || m.contains('denied')) {
      return 'Akses mikrofon ditolak. Izinkan mikrofon di browser, lalu coba lagi.';
    }
    if (m.contains('no-speech') || m.contains('no_speech')) {
      return 'Tidak ada suara terdeteksi. Bicara lebih dekat ke mikrofon.';
    }
    if (m.contains('language') || m.contains('locale')) {
      return 'Bahasa Indonesia belum tersedia di perangkat ini. Pakai input ketik.';
    }
    if (m.contains('network')) {
      return 'Pengenalan suara butuh koneksi internet. Cek jaringan atau pakai input ketik.';
    }
    if (m.contains('audio') || m.contains('capture')) {
      return 'Mikrofon tidak terdeteksi. Cek perangkat audio.';
    }
    return 'Mikrofon bermasalah ($raw). Coba pakai input ketik.';
  }

  Future<void> stop() async {
    try {
      await _stt.stop();
    } catch (_) {/* already stopped / disposed */}
    _isListening = false;
    // Fold the live delta into committed so the final transcript is stable.
    _committed = transcript;
    _engineBase = _session ?? '';
    _safeNotify();
  }

  void reset() {
    _committed = '';
    _engineBase = '';
    _session = '';
    _error = null;
    _safeNotify();
  }

  /// Remove the last word (space-delimited) from the transcript.
  /// No engine restart — we just move the engine's current text into the
  /// baseline so only NEW speech after this point is appended.
  void deleteLastWord() {
    final words = transcript.split(RegExp(r'\s+'))
      ..removeWhere((w) => w.isEmpty);
    if (words.isEmpty) return;
    words.removeLast();
    _committed = words.join(' ');
    _engineBase = _session ?? ''; // subtract everything spoken so far
    _safeNotify();
  }

  void _onResult(SpeechRecognitionResult result) {
    final words = result.recognizedWords;
    final base = _engineBase ?? '';
    // If the engine's buffer shrank or diverged from our baseline (e.g. it
    // started a fresh internal segment), fold the current delta into
    // committed and reset the baseline so nothing is lost or duplicated.
    if (base.isNotEmpty && !words.startsWith(base) && words.length < base.length) {
      _committed = transcript; // capture committed + current delta
      _engineBase = '';
    }
    _session = words;
    _safeNotify();
  }

  @override
  void dispose() {
    _disposed = true;
    try {
      _stt.cancel();
    } catch (_) {/* ignore */}
    super.dispose();
  }
}
