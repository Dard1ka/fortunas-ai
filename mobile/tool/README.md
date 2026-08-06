# mobile/tool/

Dev tooling that isn't part of the shipped app. `parser_check.dart` was here
first (a smoke test for the voice transaction parser); `font_coverage_gate.py`
and this README were added alongside it for the same reason: a script that
lives in the repo is reproducible, a fact that lives only in a chat log or a
session scratchpad is gone the moment that session ends.

## Why Inter is subset

`mobile/assets/fonts/Inter.ttf` ships as a bundled asset (see the "Fonts are
BUNDLED as assets" comment in `lib/theme/tokens.dart`) so the app renders
offline with no runtime font fetch. The full Google Inter variable font
carries Latin, Cyrillic, Greek, and Vietnamese coverage — but this app's UI
is Bahasa Indonesia only, and Cyrillic/Greek/Vietnamese glyphs are dead
weight on every page load. On a budget Android phone over 4G, Inter alone
was **856 KB raw / 448 KB gzip**, the single largest asset in the critical
path. Subsetting it to Latin-only coverage was the highest-value, lowest-risk
saving available (it changes no behaviour, unlike the WasmGC route which was
deliberately deferred elsewhere in this plan).

`JetBrainsMono.ttf` (89 KB gzip) and `SpaceGrotesk.ttf` (62 KB gzip) are
**not** subset — they're already small enough that the risk of a coverage
regression isn't worth the saving.

## The mistake this tooling exists to prevent

The first subsetting pass used a hand-written unicode-range list (copied
from a generic "Latin" preset) and checked it against a hand-picked list of
characters the plan's author expected the UI to use. Both lists were wrong:
the range list silently dropped two glyphs the app actually renders (`⚠`
U+26A0 in `orders_screen.dart`, `✓` U+2713 in `scan_screen.dart`) while
including one glyph (`∕` U+2215) that was never in Inter's cmap to begin
with and is used nowhere in the app. Two rounds of independent review were
needed to find and close that gap, because a missing glyph produces no
compiler error and no failing test — it's silent tofu on a real screen.

`font_coverage_gate.py` closes this mechanically: it scans the actual Dart
source for every non-ASCII character that's genuinely rendered (not just
present in a comment), and diffs that set against whatever font you point it
at. No hand-written list to drift out of sync with the source, ever again.

## Current Inter subset: exact command and coverage rationale

Original, unsubsetted font: `git show 17ddcda:mobile/assets/fonts/Inter.ttf`
(876,576 bytes). Command used to produce the current
`mobile/assets/fonts/Inter.ttf`:

```bash
pip install fonttools brotli   # if not already installed
pyftsubset path/to/Inter.original.ttf \
  --output-file=assets/fonts/Inter.ttf \
  --unicodes="U+0000-00FF,U+0100-017F,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+2074,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+26A0,U+2713,U+FEFF,U+FFFD" \
  --layout-features="*" \
  --no-hinting \
  --desubroutinize
```

Result: 856 KB → 274 KB raw, 448 KB → 134.5 KB gzip (saved ≈0.306 MB gzip on
first load). The variable weight axis (`fvar` wght 100–900, opsz 14–32, 9
named instances; `gvar` variation count equals `maxp.numGlyphs` — every
retained glyph kept its weight-deformation data) survives subsetting intact;
re-verify this with fontTools after any future re-subset, don't assume it
carries over.

Why each range is in the list:

| Range | Reason |
|---|---|
| `U+0000-00FF` | Basic Latin + Latin-1 Supplement. Digits, ASCII punctuation, Indonesian text, and Western-European accented Latin (é, ü, ñ, ç, ×, ·, §) for backend-supplied product/customer names. **Derived from source scan + backend-text reasoning.** |
| `U+0100-017F` | Latin Extended-A, full block. Covers Central/Eastern European and Turkic accented Latin (š, ł, ą, ğ, ş, đ, ...) that could appear in backend-supplied free text a shop owner types. 127/128 codepoints present in the original font (only the Unicode-deprecated U+0149 is absent). **Derived from backend-text reasoning**, not the source scan (the scan alone can't see database content). |
| `U+02BB-02BC`, `U+02C6`, `U+02DA`, `U+02DC` | Spacing modifier letters (turned comma/apostrophe, circumflex, ring, tilde). Not found in the source scan; retained at near-zero cost from the original baseline list. **Not re-derived** — candidates for removal in a future tightening pass. |
| `U+2000-206F` | General Punctuation. Covers em dash `—` and ellipsis `…`, both confirmed rendered by the source scan (briefing/checkout/history/customer_home screens). **Derived from source scan.** |
| `U+2074`, `U+20AC` (€), `U+2122` (™) | Superscript four, Euro sign, trademark sign. None found in the source scan (app only formats Rupiah via `intl`). Retained at near-zero cost as a defensive margin for backend text or future currency display. **Not re-derived.** |
| `U+2191`, `U+2193` | Up/down arrows. Not found anywhere in the source scan. Retained at near-zero cost. **Not re-derived** — a candidate for removal. |
| `U+2212` (−) | Minus sign, for numeric display. Not hit by a literal string in the scan. Retained at near-zero cost. |
| `U+2215` (∕) | Division slash. **Confirmed absent from Inter's cmap even in the original, unsubsetted font**, and used nowhere in the app. Including it in `--unicodes` is a pure no-op. Kept only for continuity with the original list; this is the exact "included what didn't matter" mistake from round one, now explicitly labelled inert instead of silently carried forward. |
| `U+26A0` (⚠) | Warning sign. **Confirmed rendered** at `orders_screen.dart:162` (refund notice). Mandatory — this is the first of the two regressions the fix round closed. |
| `U+2713` (✓) | Check mark. **Confirmed rendered** at `scan_screen.dart:138` (member-registered notice). Mandatory — the second regression closed. |
| `U+FEFF` | Zero-width no-break space / BOM. Not found in the source scan. Retained as a harmless format-control glyph. |
| `U+FFFD` (�) | Replacement character. **Confirmed absent from the original Inter cmap** (same status as U+2215 above) — so it costs and buys nothing either way. Retained only for continuity with the original list; there is no functional "decode failures stay visible" benefit here since the glyph was never available to provide that benefit in the first place. |

`intl`-formatted output was checked explicitly and needs nothing beyond
Basic Latin: `NumberFormat.currency(locale: 'id_ID', symbol: 'Rp ', decimalDigits: 0)`
uses a literal ASCII `"Rp "` symbol and a `.` thousands separator with zero
decimal digits; `DateFormat('d MMM yyyy · HH:mm')` renders ASCII month
abbreviations in both `id_ID` and the `en` fallback.

## Two pre-existing emoji gaps (not fixable by subsetting)

`🎉` U+1F389 (`customer_promo_screen.dart`, `scan_screen.dart`) and `👋`
U+1F44B (`customer_home_screen.dart`) are rendered by the app but were
**never present in Inter even before any subsetting happened** — Inter is a
text typeface with no emoji coverage at all. Rendering these relies on the
platform's system emoji font (Noto Color Emoji / Apple Color Emoji)
regardless of what ships in `Inter.ttf`. This is an existing, independent
characteristic of the font (and arguably of not having a color-emoji
fallback configured), unrelated to and unaffected by subsetting. Both are
allowlisted in `font_coverage_gate.py`'s `KNOWN_PRE_EXISTING_GAPS` so the
gate passes cleanly against Inter today instead of needing a human to
remember they're expected failures.

## How to re-run the gate

```bash
cd mobile
python tool/font_coverage_gate.py                                  # checks Inter.ttf (default)
python tool/font_coverage_gate.py --font assets/fonts/JetBrainsMono.ttf
python tool/font_coverage_gate.py --font assets/fonts/SpaceGrotesk.ttf
```

Requires `pip install fonttools`. Exits 0 if every character the Dart source
actually renders is present in the target font's cmap (or is an allowlisted,
verified pre-existing gap); exits 1 and prints the missing codepoints
otherwise. Font paths are resolved relative to `mobile/` unless absolute, so
it works from the repo root or from inside `mobile/`.

Re-run this after re-subsetting any bundled font, or before bundling a new
one, so a future coverage regression is a failing command, not a screenshot
someone happens to notice.

### A finding this generic check surfaced immediately (informational, not acted on)

Running the gate against `JetBrainsMono.ttf` and `SpaceGrotesk.ttf` — which
were never touched by the Inter subsetting work and are explicitly out of
scope for this repo change — shows both are also missing `✓`/`⚠` (and
`SpaceGrotesk` is missing both). That's expected in isolation: neither font
was ever meant to carry those glyphs. But `scan_screen.dart:138` renders its
`✓` via `style: display(...)`, i.e. with `fontFamily: 'SpaceGrotesk'`
specifically (see `lib/theme/tokens.dart`'s `display()` helper) — so that
one call site names a font that has never had a check-mark glyph, on a
screen unrelated to and pre-dating this task's font-subsetting work. Whether
Flutter's CanvasKit renderer silently falls back to another bundled custom
font (e.g. Inter, which does have `✓` now) for a glyph missing from an
explicitly-named `fontFamily`, or shows tofu, was not verified empirically
in this round — that screen requires an authenticated backend session to
reach, and resolving it would mean either a Dart change or new test file,
both out of scope here. Recorded as a known open question for whoever picks
up UI polish next, not something this round fixed.

## Follow-up not done in this round

Wiring `font_coverage_gate.py` into CI (`.github/workflows/ci.yml` or
equivalent) would need a Python + `pip install fonttools` setup step added
to the mobile CI job before `flutter test` runs. That's a CI config change,
explicitly out of scope for this round — noted here so it isn't lost.
