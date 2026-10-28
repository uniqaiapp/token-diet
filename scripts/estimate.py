#!/usr/bin/env python3
"""Character-based token ESTIMATE for prompts, with a breakdown by writing system.

This is not a tokenizer. It exists so `measure.py` can print something useful
when no ANTHROPIC_API_KEY is set. Every number it prints is labelled as an
estimate. For an exact count use `measure.py` with ANTHROPIC_API_KEY set; it
then calls the count_tokens endpoint instead of this file.

Model: characters are grouped by writing system and divided by an assumed
"characters per token" rate. The rates below are deliberately conservative
assumptions, not measurements, and they are the only thing in this file worth
arguing about. Change them, re-run, and the reports in examples/ change with
them (tests pin the committed reports, so the test suite will tell you).

Usage:
    python3 scripts/estimate.py FILE [FILE ...]
    cat prompt.txt | python3 scripts/estimate.py -
"""
import argparse
import re
import sys

# Assumed characters per token, per class. Assumptions, not measurements.
RATES = {
    "latin": 4.0,      # English and other Latin-script prose, punctuation, spaces
    "cyrillic": 2.4,   # Russian, Ukrainian, Bulgarian, ...: fewer chars per token
    "cjk": 1.0,        # Chinese / Japanese / Korean: roughly one token per character
    "code": 3.3,       # fenced code blocks (any language)
    "other": 2.5,      # Arabic, Hebrew, Greek, Devanagari, emoji, everything else
}

FENCE_RE = re.compile(r"```.*?```", re.S)


def classify(ch):
    """Return the RATES class for one character (outside code fences)."""
    o = ord(ch)
    if o < 0x0250 or 0x2000 <= o <= 0x206F or 0x20A0 <= o <= 0x20CF:
        return "latin"
    if 0x0400 <= o <= 0x052F:
        return "cyrillic"
    if 0x2E80 <= o <= 0x9FFF or 0xAC00 <= o <= 0xD7AF or 0xF900 <= o <= 0xFAFF or 0xFF00 <= o <= 0xFFEF:
        return "cjk"
    return "other"


def breakdown(text):
    """Character counts per class, code fences counted as 'code'."""
    counts = {k: 0 for k in RATES}
    code_chars = sum(len(m.group(0)) for m in FENCE_RE.finditer(text))
    counts["code"] = code_chars
    for ch in FENCE_RE.sub("", text):
        counts[classify(ch)] += 1
    return counts


def estimate_tokens(text):
    """Estimated token count (int) for `text`."""
    counts = breakdown(text)
    return int(round(sum(n / RATES[k] for k, n in counts.items())))


def describe(counts):
    """Short human-readable class summary, e.g. 'cyrillic 71%, latin 29%'."""
    total = sum(counts.values()) or 1
    parts = ["%s %d%%" % (k, round(100.0 * n / total)) for k, n in counts.items() if n]
    parts.sort(key=lambda p: -int(p.split()[1].rstrip("%")))
    return ", ".join(parts) if parts else "empty"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", help="text files to estimate; '-' reads stdin")
    a = ap.parse_args(argv)
    print("ESTIMATE (character-based, not a tokenizer; rates in scripts/estimate.py)")
    for f in a.files:
        text = sys.stdin.read() if f == "-" else open(f, encoding="utf-8").read()
        counts = breakdown(text)
        print("%-32s %6d chars  ~%5d tokens  (%s)" % (f, len(text), estimate_tokens(text), describe(counts)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
