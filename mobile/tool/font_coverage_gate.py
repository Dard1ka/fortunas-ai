#!/usr/bin/env python3
"""
mobile/tool/font_coverage_gate.py

Gate: every non-ASCII character *rendered* by mobile/lib/**/*.dart must be
present in the cmap of a bundled font -- or explicitly allowlisted below as
a known, pre-existing gap in that font.

Why this exists
----------------
mobile/assets/fonts/Inter.ttf ships as a Latin-only subset (see README.md in
this directory for the full history and the exact pyftsubset command). An
earlier subsetting pass used a hand-written unicode-range list and silently
dropped two glyphs the app actually renders (warning U+26A0 and check mark
U+2713) while including one glyph (U+2215) the font never had in the first
place. That class of bug is invisible until a human happens to notice tofu
on a real screen -- there is no compiler error, no failing test.

This script closes the bug mechanically instead of by memory: it derives
the "must be covered" set directly from the Dart source (never from a
hand-maintained list) and fails loudly, with a non-zero exit code, if the
target font is missing anything the source actually renders. Re-run it
after re-subsetting any bundled font, or point it at a *new* font before
bundling it for the first time.

Usage
-----
    python tool/font_coverage_gate.py                        # checks Inter.ttf (default)
    python tool/font_coverage_gate.py --font assets/fonts/JetBrainsMono.ttf
    python tool/font_coverage_gate.py --font assets/fonts/SpaceGrotesk.ttf

Run from anywhere -- font paths are resolved relative to the mobile/
directory (this script's parent) unless given as absolute paths.

Requires: fontTools (`pip install fonttools`). Not wired into CI yet -- the
mobile CI job has no Python setup step; see the "Follow-up" section of
README.md in this directory.
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

try:
    from fontTools.ttLib import TTFont
except ImportError:
    print("ERROR: fontTools is required. Install with: pip install fonttools", file=sys.stderr)
    sys.exit(2)

MOBILE_ROOT = Path(__file__).resolve().parent.parent
DART_ROOT = MOBILE_ROOT / "lib"

# Codepoints that are known, pre-existing gaps -- confirmed absent from a
# font *before* any subsetting ever touched it, so no subsetting decision
# could have added or removed them. Verified directly against the original,
# unsubsetted Inter.ttf (commit 17ddcda) with fontTools.
#
# Do not add an entry here just because a font "should" have a glyph --
# verify with fontTools that it was genuinely never present, the same way
# these two were, before allowlisting it. An allowlist entry that isn't
# actually true defeats the entire point of this gate.
KNOWN_PRE_EXISTING_GAPS: dict[int, str] = {
    0x1F389: (
        "party popper emoji - confirmed absent from Inter.ttf even before "
        "subsetting (commit 17ddcda). Inter is a text typeface with no emoji "
        "coverage; rendering relies on the platform's system emoji font "
        "(Noto Color Emoji / Apple Color Emoji) regardless of what this repo "
        "bundles. Used at customer_promo_screen.dart, scan_screen.dart."
    ),
    0x1F44B: (
        "waving hand emoji - same reasoning as U+1F389 above. Used at "
        "customer_home_screen.dart."
    ),
}


def _record(occurrences, cp, category, path, line_no, ctx):
    occurrences[cp][category].append((str(path), line_no, ctx))


def scan_file(path: Path, occurrences) -> None:
    """
    Hand-rolled Dart lexer state machine -- not a full parser, but correct
    on the cases that matter: it tracks, character by character, whether the
    cursor is inside a line comment (// or ///), a block comment (/* ... */),
    or a string literal (single/double/triple-quoted, raw, with ${...}
    interpolation switching back to code-mode inside the braces).

    This is deliberately NOT a per-line "does this line start with //"
    filter. That kind of filter misses a trailing inline comment such as
        String _phase = 'query';   // query -> insight
    in result_screen.dart, where a naive line-anchored check would treat the
    whole line -- including the arrow after `//` -- as rendered code. A
    character-by-character scan gets this right without guessing.

    Where a construct is still genuinely ambiguous, this scan errs toward
    marking a character as rendered: a few extra glyphs cost near nothing in
    a subset; a rendered glyph wrongly marked as comment-only is the failure
    mode that ships tofu to a real screen.
    """
    text = path.read_text(encoding="utf-8")
    n = len(text)
    i = 0
    line_no = 1
    mode_stack: list = ["code"]

    def line_context() -> str:
        start = text.rfind("\n", 0, i) + 1
        end = text.find("\n", i)
        if end == -1:
            end = n
        return text[start:end]

    while i < n:
        c = text[i]
        mode = mode_stack[-1]

        if c == "\n":
            if mode == "line_comment":
                mode_stack.pop()
            line_no += 1
            i += 1
            continue

        if mode == "code":
            prev = text[i - 1] if i > 0 else ""
            if c == "r" and i + 1 < n and text[i + 1] in ('"', "'") and not (prev.isalnum() or prev == "_"):
                quote = text[i + 1]
                triple = text[i + 1:i + 4] == quote * 3
                mode_stack.append(("string", quote, triple, True))
                i += 4 if triple else 2
                continue
            if text[i:i + 2] == "//":
                mode_stack.append("line_comment")
                i += 2
                continue
            if text[i:i + 2] == "/*":
                mode_stack.append("block_comment")
                i += 2
                continue
            if c in ('"', "'"):
                triple = text[i:i + 3] == c * 3
                mode_stack.append(("string", c, triple, False))
                i += 3 if triple else 1
                continue
            if ord(c) > 127:
                _record(occurrences, ord(c), "code-bare", path, line_no, line_context())
            i += 1
            continue

        if mode == "line_comment":
            if ord(c) > 127:
                _record(occurrences, ord(c), "comment", path, line_no, line_context())
            i += 1
            continue

        if mode == "block_comment":
            if text[i:i + 2] == "*/":
                mode_stack.pop()
                i += 2
                continue
            if ord(c) > 127:
                _record(occurrences, ord(c), "comment", path, line_no, line_context())
            i += 1
            continue

        if isinstance(mode, tuple) and mode[0] == "string":
            _, quote, triple, raw = mode
            if not raw and c == "\\":
                i += 1
                if i < n:
                    nc = text[i]
                    if ord(nc) > 127:
                        _record(occurrences, ord(nc), "string", path, line_no, line_context())
                    if nc == "\n":
                        line_no += 1
                    i += 1
                continue
            if triple:
                if text[i:i + 3] == quote * 3:
                    mode_stack.pop()
                    i += 3
                    continue
            else:
                if c == quote:
                    mode_stack.pop()
                    i += 1
                    continue
                if c == "\n":
                    # Unterminated single-line string -- shouldn't happen in
                    # valid Dart. Don't hang: pop back to code-mode.
                    mode_stack.pop()
                    line_no += 1
                    i += 1
                    continue
            if c == "$" and i + 1 < n and text[i + 1] == "{":
                mode_stack.append(("interp", 1))
                i += 2
                continue
            if ord(c) > 127:
                _record(occurrences, ord(c), "string", path, line_no, line_context())
            i += 1
            continue

        if isinstance(mode, tuple) and mode[0] == "interp":
            _, depth = mode
            if c == "{":
                mode_stack[-1] = ("interp", depth + 1)
                i += 1
                continue
            if c == "}":
                if depth == 1:
                    mode_stack.pop()
                else:
                    mode_stack[-1] = ("interp", depth - 1)
                i += 1
                continue
            if c in ('"', "'"):
                triple = text[i:i + 3] == c * 3
                mode_stack.append(("string", c, triple, False))
                i += 3 if triple else 1
                continue
            if text[i:i + 2] == "//":
                mode_stack.append("line_comment")
                i += 2
                continue
            if ord(c) > 127:
                _record(occurrences, ord(c), "code-bare", path, line_no, line_context())
            i += 1
            continue

        # Unknown mode -- should never happen; don't hang.
        i += 1


def scan_source(dart_root: Path):
    occurrences = defaultdict(lambda: defaultdict(list))
    files = sorted(dart_root.rglob("*.dart"))
    for f in files:
        scan_file(f, occurrences)
    rendered = {cp for cp, cats in occurrences.items() if "string" in cats or "code-bare" in cats}
    return occurrences, rendered, files


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument(
        "--font", default="assets/fonts/Inter.ttf",
        help="Font to check, relative to mobile/ unless absolute. Default: assets/fonts/Inter.ttf",
    )
    ap.add_argument(
        "--lib-root", default=None,
        help="Override the Dart source root to scan (default: mobile/lib).",
    )
    ap.add_argument(
        "--allow", action="append", default=[], metavar="U+XXXX",
        help="Extra codepoint to allowlist as an expected gap for this run only, "
             "e.g. --allow U+2603. Repeatable. Prefer adding a permanent, documented "
             "entry to KNOWN_PRE_EXISTING_GAPS in this file over using this flag "
             "routinely -- it exists for one-off investigation.",
    )
    args = ap.parse_args()

    font_path = Path(args.font)
    if not font_path.is_absolute():
        font_path = (MOBILE_ROOT / font_path).resolve()
    if not font_path.exists():
        print(f"ERROR: font not found: {font_path}", file=sys.stderr)
        sys.exit(2)

    dart_root = Path(args.lib_root).resolve() if args.lib_root else DART_ROOT

    allowlist = dict(KNOWN_PRE_EXISTING_GAPS)
    for entry in args.allow:
        try:
            cp = int(entry.replace("U+", "").replace("u+", ""), 16)
        except ValueError:
            print(f"ERROR: --allow value must look like U+XXXX, got {entry!r}", file=sys.stderr)
            sys.exit(2)
        allowlist.setdefault(cp, "ad-hoc --allow flag, no persistent reason recorded")

    occurrences, rendered, files = scan_source(dart_root)
    cmap = TTFont(str(font_path)).getBestCmap()

    print(f"Scanned {len(files)} Dart file(s) under {dart_root}")
    print(f"Checking against: {font_path}")
    print(f"Rendered non-ASCII codepoints found: {len(rendered)}\n")

    print(f"{'codepoint':<10} {'char':<4} {'in font':<8} verdict")
    print("-" * 90)

    failures = []
    allowlisted_gaps = 0
    for cp in sorted(rendered):
        char = chr(cp)
        in_font = cp in cmap
        if in_font:
            verdict = "OK"
        elif cp in allowlist:
            verdict = f"ALLOWLISTED (pre-existing gap): {allowlist[cp]}"
            allowlisted_gaps += 1
        else:
            verdict = "MISSING -- rendered by source but absent from font cmap"
            failures.append(cp)
        printable = char if char.isprintable() else repr(char)
        print(f"U+{cp:05X}   {printable:<4} {str(in_font):<8} {verdict}")
        cats = occurrences[cp]
        shown = 0
        for cat in ("string", "code-bare"):
            for (fp, ln, ctx) in cats.get(cat, []):
                print(f"           used at: {Path(fp).name}:{ln}: {ctx.strip()[:90]}")
                shown += 1
                if shown >= 2:
                    break
            if shown >= 2:
                break

    print("-" * 90)
    if failures:
        print(f"GATE FAILED: {len(failures)} rendered codepoint(s) missing from {font_path.name}:")
        for cp in failures:
            print(f"  U+{cp:05X} ({chr(cp)!r})")
        sys.exit(1)

    print(
        f"GATE PASSED: 0 of {len(rendered)} rendered codepoints missing from "
        f"{font_path.name} ({allowlisted_gaps} pre-existing gap(s) allowlisted)."
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
