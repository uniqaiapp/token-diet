#!/usr/bin/env python3
"""Measure tokens before/after a token-diet rewrite, or break a transcript down by source.

Two methods, always labelled in the output:
  count_tokens   exact, model-specific count from Anthropic's /v1/messages/count_tokens.
                 Used automatically when ANTHROPIC_API_KEY is set (one request per file).
  ESTIMATE       character-based guess from scripts/estimate.py when no key is set or
                 --estimate is passed. Never quote an estimate as a measurement.

Usage:
    python3 scripts/measure.py BEFORE AFTER [--model claude-opus-5-5] [--estimate] [--price-in USD_PER_MTOK]
    python3 scripts/measure.py --breakdown transcript.json [--estimate]

The transcript for --breakdown is JSON: {"system": "...", "rag": "...",
"messages": [{"role": "user"|"assistant"|"tool", "content": "..." | [blocks]}]}.
Anthropic-style content blocks ({"type": "text"|"tool_result"|"tool_use"}) are understood.
"""
import argparse
import datetime
import json
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from estimate import breakdown as char_breakdown, describe, estimate_tokens  # noqa: E402

COUNT_URL = "https://api.anthropic.com/v1/messages/count_tokens"
DEFAULT_MODEL = "claude-opus-5-5"


# --------------------------------------------------------------------------- counting

def build_count_request(model, text):
    """Request body for count_tokens. The text is sent as a single user message."""
    return {"model": model, "messages": [{"role": "user", "content": text}]}


def count_tokens(model, text, key):
    body = json.dumps(build_count_request(model, text)).encode("utf-8")
    req = urllib.request.Request(COUNT_URL, data=body, method="POST", headers={
        "content-type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01",
        "user-agent": "token-diet/0.1 (+https://github.com/uniqaiapp/token-diet)"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8"))["input_tokens"]
    except urllib.error.HTTPError as e:
        sys.exit("error: count_tokens returned HTTP %s\n%s" % (e.code, e.read().decode("utf-8", "replace")[:500]))
    except urllib.error.URLError as e:
        sys.exit("error: network: %s" % e.reason)


class Counter:
    """Picks the method once and reports it in `label`."""

    def __init__(self, model, force_estimate):
        self.key = None if force_estimate else os.environ.get("ANTHROPIC_API_KEY")
        self.model = model
        if self.key:
            self.label = "count_tokens (model %s, exact, %s)" % (model, datetime.date.today().isoformat())
        else:
            self.label = ("ESTIMATE (character-based, not a tokenizer; rates in scripts/estimate.py)\n"
                          "        set ANTHROPIC_API_KEY for an exact count via count_tokens")

    def __call__(self, text):
        if not text:
            return 0
        return count_tokens(self.model, text, self.key) if self.key else estimate_tokens(text)


# --------------------------------------------------------------------------- before / after

def compare(before_path, after_path, counter, price_in=None):
    rows = []
    for p in (before_path, after_path):
        text = open(p, encoding="utf-8").read()
        rows.append((os.path.basename(p), len(text), counter(text), describe(char_breakdown(text))))
    (nb, cb, tb, db), (na, ca, ta, da) = rows
    unit = "tokens" if counter.key else "tokens(est)"
    out = ["token-diet measure", "method: " + counter.label, "",
           "%-16s %7s %12s  %s" % ("file", "chars", unit, "writing systems"),
           "%-16s %7d %12d  %s" % (nb, cb, tb, db),
           "%-16s %7d %12d  %s" % (na, ca, ta, da)]
    pct = (100.0 * (ta - tb) / tb) if tb else 0.0
    out.append("%-16s %+7d %+12d  (%+.1f%% %s)" % ("delta", ca - cb, ta - tb, pct, "exact" if counter.key else "of an estimate"))
    if price_in:
        out.append("")
        out.append("at %.4g USD per 1M input tokens: before %.6f USD, after %.6f USD per send (price supplied by you, not by this script)"
                   % (price_in, tb * price_in / 1e6, ta * price_in / 1e6))
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- transcript breakdown

def _block_text(block):
    if isinstance(block, str):
        return block
    if isinstance(block, dict):
        if block.get("type") == "tool_result":
            c = block.get("content", "")
            return c if isinstance(c, str) else "".join(_block_text(x) for x in c)
        if block.get("type") == "tool_use":
            return json.dumps(block.get("input", {}), ensure_ascii=False)
        return block.get("text", "") or ""
    return ""


def split_transcript(t):
    """Group a transcript into the sources that usually dominate an agent's input."""
    parts = {"system prompt": "", "tools / schemas": "", "retrieved context (rag)": "",
             "history": "", "tool output": "", "current user turn": ""}
    parts["system prompt"] = t.get("system", "") if isinstance(t.get("system"), str) else "\n".join(_block_text(b) for b in t.get("system", []) or [])
    tools = t.get("tools")
    if tools:
        parts["tools / schemas"] = json.dumps(tools, ensure_ascii=False) if not isinstance(tools, str) else tools
    parts["retrieved context (rag)"] = t.get("rag", "") or ""
    msgs = t.get("messages", []) or []
    last_user = max((i for i, m in enumerate(msgs) if m.get("role") == "user"), default=-1)
    for i, m in enumerate(msgs):
        content = m.get("content", "")
        blocks = content if isinstance(content, list) else [content]
        for b in blocks:
            txt = _block_text(b)
            is_tool = m.get("role") == "tool" or (isinstance(b, dict) and b.get("type") == "tool_result")
            if is_tool:
                parts["tool output"] += txt + "\n"
            elif i == last_user:
                parts["current user turn"] += txt + "\n"
            else:
                parts["history"] += txt + "\n"
    return parts


HINTS = [
    ("tool output", 0.35, "tool output dominates: truncate or summarise tool results before they enter the context (keep the first/last lines, counts, and errors)"),
    ("history", 0.45, "history dominates: keep a window of the last N turns and a short running summary of the rest"),
    ("system prompt", 0.30, "the system prompt is large: keep it byte-stable so it can be cached, and move rarely used material behind a lookup"),
    ("retrieved context (rag)", 0.35, "retrieved context dominates: fewer, shorter chunks; rerank before you inject"),
    ("tools / schemas", 0.20, "tool schemas are large: shorten descriptions and defer rarely used tools"),
]


def breakdown_report(path, counter):
    t = json.load(open(path, encoding="utf-8"))
    parts = split_transcript(t)
    counts = {k: counter(v) for k, v in parts.items()}
    total = sum(counts.values()) or 1
    unit = "tokens" if counter.key else "tokens(est)"
    out = ["token-diet breakdown: " + os.path.basename(path), "method: " + counter.label, "",
           "%-26s %12s %7s" % ("source", unit, "share")]
    for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
        out.append("%-26s %12d %6.1f%%" % (k, v, 100.0 * v / total))
    out.append("%-26s %12d" % ("total", total))
    hints = [h for k, thr, h in HINTS if counts[k] / total >= thr]
    out.append("")
    out.append("levers (ordered by share; thresholds in scripts/measure.py):" if hints else "no single source dominates; start with the stable-prefix check in SKILL.md")
    out.extend("  - " + h for h in hints)
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- CLI

def main(argv=None):
    ap = argparse.ArgumentParser(description="Count tokens before/after a rewrite, or break a transcript down by source.",
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__.split("Usage:")[1])
    ap.add_argument("before", nargs="?", help="original prompt file")
    ap.add_argument("after", nargs="?", help="rewritten prompt file")
    ap.add_argument("--breakdown", metavar="TRANSCRIPT_JSON", help="break a transcript down by source instead")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="model to count for (count_tokens is model-specific)")
    ap.add_argument("--estimate", action="store_true", help="force the character estimate even if a key is set")
    ap.add_argument("--price-in", type=float, metavar="USD_PER_MTOK", help="your input price per 1M tokens, to print a cost line")
    a = ap.parse_args(argv)
    counter = Counter(a.model, a.estimate)
    if a.breakdown:
        sys.stdout.write(breakdown_report(a.breakdown, counter))
        return 0
    if not (a.before and a.after):
        ap.error("give BEFORE and AFTER files, or --breakdown TRANSCRIPT_JSON")
    sys.stdout.write(compare(a.before, a.after, counter, a.price_in))
    return 0


if __name__ == "__main__":
    sys.exit(main())
