#!/usr/bin/env python3
"""token-diet: rewrite a prompt in any language as compact English, verbatim parts protected.

Pipeline:
  1. protect   code fences, inline code, URLs, paths, file names, flags, identifiers and
               quoted strings are swapped for numbered placeholders (⟦0⟧, ⟦1⟧, ...).
  2. rewrite   the protected text goes to a cheap model you choose (OpenAI, Gemini or
               Anthropic; the key is read from an environment variable, never from a file).
  3. verify    every placeholder must come back exactly once, or the run fails loudly.
  4. restore   placeholders are swapped back, and one line is appended that tells the
               agent which language to answer in ("Answer in Russian.").

Python 3.9+ standard library only. No key is ever printed.

Usage:
    python3 scripts/diet.py prompt.txt --provider openai
    cat prompt.txt | python3 scripts/diet.py - --provider gemini --model gemini-2.5-flash-lite
    python3 scripts/diet.py prompt.txt --dry-run          # no network: shows what would be sent

Environment variables (names only; set them in your shell, never commit them):
    OPENAI_API_KEY      for --provider openai
    GEMINI_API_KEY      for --provider gemini   (GOOGLE_API_KEY is accepted as a fallback)
    ANTHROPIC_API_KEY   for --provider anthropic
    TOKEN_DIET_PROVIDER / TOKEN_DIET_MODEL   defaults for --provider / --model
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

OPEN, CLOSE = "⟦", "⟧"  # ⟦ ⟧
PH_RE = re.compile(OPEN + r"\s*(\d+)\s*" + CLOSE)

# Protection rules, in precedence order. ASCII-only character classes on purpose:
# `\w` would match Cyrillic and swallow ordinary words.
A = r"[A-Za-z0-9_.@-]"
RULES = [
    ("fence", re.compile(r"```.*?```", re.S)),
    ("inline-code", re.compile(r"`[^`\n]+`")),
    ("url", re.compile(r"\bhttps?://[^\s<>()\"'«»]+")),
    ("path", re.compile(r"(?<![A-Za-z0-9_])(?:(?:~|\.{1,2})?/)?" + A + r"+(?:/" + A + r"+)+/?")),
    ("file", re.compile(r"\b[A-Za-z0-9_.-]+\.(?:py|pyi|js|mjs|cjs|ts|tsx|jsx|json|md|mdc|yml|yaml|toml|ini|env|sql|go|rs|java|kt|swift|rb|php|cs|css|scss|html|sh|zsh|txt|csv|lock|cfg|conf|xml|svg|png|jpg|jpeg|webp|gif|pdf)\b(?![A-Za-z0-9_])")),
    ("quote", re.compile(r"\"[^\"\n]{1,200}\"|«[^»\n]{1,200}»|'[^'\s]{1,80}'")),
    ("flag", re.compile(r"(?<![A-Za-z0-9])--?[A-Za-z][A-Za-z0-9-]*")),
    ("call", re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\(\)")),
    ("dotted", re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+\b")),
    ("snake", re.compile(r"\b[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+\b")),
    ("camel", re.compile(r"\b[a-z]+(?:[A-Z][a-z0-9]+)+\b|\b(?:[A-Z][a-z0-9]+){2,}\b")),
]

SYSTEM_PROMPT = (
    "You rewrite prompts for a coding agent. Rewrite the user's text as compact English.\n"
    "Rules:\n"
    "- Keep every placeholder like " + OPEN + "3" + CLOSE + " exactly as written, each one exactly once, "
    "in a sensible position. Never translate, number, merge or drop a placeholder.\n"
    "- Keep all numbers, versions, limits, dates and proper nouns.\n"
    "- Keep every requirement, constraint and acceptance criterion; put them as a short list when there are several.\n"
    "- Drop greetings, apologies, hedges, repetition and commentary about the agent.\n"
    "- Use imperative mood and short sentences. No markdown headings.\n"
    "- Do not answer the task, do not add advice, do not add information that is not in the text.\n"
    "- Output only the rewritten prompt."
)

# Default models are the cheap tier of each provider at the time of writing (2026-10).
# Override with --model or TOKEN_DIET_MODEL; see references/providers.md.
PROVIDERS = {
    "openai": {"env": "OPENAI_API_KEY", "model": "gpt-5-mini"},
    "gemini": {"env": "GEMINI_API_KEY", "model": "gemini-2.5-flash-lite"},
    "anthropic": {"env": "ANTHROPIC_API_KEY", "model": "claude-haiku-5-5"},
}

LANG_NAMES = {"ru": "Russian", "uk": "Ukrainian", "es": "Spanish", "pt": "Portuguese",
              "de": "German", "fr": "French", "it": "Italian", "en": "English"}
STOPWORDS = {
    "es": {"el", "la", "los", "las", "que", "para", "con", "una", "por", "del", "pero", "también", "necesito", "hacer"},
    "pt": {"o", "os", "as", "que", "para", "com", "uma", "não", "por", "mas", "também", "preciso", "fazer", "você"},
    "de": {"der", "die", "das", "und", "nicht", "ist", "ich", "mit", "ein", "eine", "für", "bitte", "auch", "wir"},
    "fr": {"le", "la", "les", "des", "est", "pas", "pour", "avec", "une", "que", "nous", "vous", "dans"},
    "it": {"il", "la", "che", "per", "con", "una", "non", "del", "della", "anche", "sono"},
}


# --------------------------------------------------------------------------- protect / restore

def protect(text):
    """Return (protected_text, placeholders) where placeholders is a list of (rule, original)."""
    spans = []
    for name, rx in RULES:
        for m in rx.finditer(text):
            s, e = m.span()
            if name in ("url", "path", "file", "dotted", "flag"):
                while e > s + 1 and text[e - 1] in ".,;:":
                    e -= 1  # sentence punctuation is not part of a path
            if any(s < pe and e > ps for ps, pe, _ in spans):
                continue  # overlaps a higher-precedence span
            if name == "dotted" and all(len(p) <= 1 for p in m.group(0).split(".")):
                continue  # "e.g.", "i.e."
            spans.append((s, e, name))
    spans.sort()
    out, last, table = [], 0, []
    for s, e, name in spans:
        out.append(text[last:s])
        out.append("%s%d%s" % (OPEN, len(table), CLOSE))
        table.append((name, text[s:e]))
        last = e
    out.append(text[last:])
    return "".join(out), table


def restore(text, table):
    """Swap placeholders back. Raises ValueError if any is missing or duplicated."""
    seen = {}
    for m in PH_RE.finditer(text):
        seen[int(m.group(1))] = seen.get(int(m.group(1)), 0) + 1
    missing = [i for i in range(len(table)) if i not in seen]
    dupes = [i for i, n in seen.items() if n > 1]
    unknown = [i for i in seen if i >= len(table)]
    if missing or dupes or unknown:
        raise ValueError("placeholder check failed: missing=%s duplicated=%s unknown=%s"
                         % (missing, dupes, unknown))
    return PH_RE.sub(lambda m: table[int(m.group(1))][1], text)


# --------------------------------------------------------------------------- language

def detect_language(text):
    """Cheap script + stopword detection. Returns an ISO code or 'en'."""
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return "en"
    cyr = sum(1 for c in letters if "Ѐ" <= c <= "ԯ")
    if cyr > len(letters) * 0.3:
        return "uk" if re.search(r"[іїєґ]", text) else "ru"
    words = set(re.findall(r"[a-záéíóúñüçãõâêôàèìòùäöß]+", text.lower()))
    best, score = "en", 1
    for code, sw in STOPWORDS.items():
        n = len(words & sw)
        if n > score:
            best, score = code, n
    return best


# --------------------------------------------------------------------------- providers

def build_request(provider, model, protected):
    """Return (url, headers, body) for the provider. The key header holds the ENV VAR NAME;
    send() replaces it with the value at the last moment, so dry runs never touch the key."""
    env = PROVIDERS[provider]["env"]
    if provider == "openai":
        return ("https://api.openai.com/v1/chat/completions",
                {"Authorization": "Bearer $" + env},
                {"model": model,
                 "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                              {"role": "user", "content": protected}]})
    if provider == "gemini":
        return ("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent" % model,
                {"x-goog-api-key": "$" + env},
                {"system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                 "contents": [{"role": "user", "parts": [{"text": protected}]}],
                 "generationConfig": {"temperature": 0}})
    if provider == "anthropic":
        return ("https://api.anthropic.com/v1/messages",
                {"x-api-key": "$" + env, "anthropic-version": "2023-06-01"},
                {"model": model, "max_tokens": 4096, "system": SYSTEM_PROMPT,
                 "messages": [{"role": "user", "content": protected}]})
    raise ValueError("unknown provider: " + provider)


def extract_text(provider, data):
    if provider == "openai":
        return data["choices"][0]["message"]["content"]
    if provider == "gemini":
        return "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"])
    if provider == "anthropic":
        if data.get("stop_reason") == "refusal":
            raise RuntimeError("the model declined this request (stop_reason=refusal)")
        return "".join(b.get("text", "") for b in data["content"] if b.get("type") == "text")
    raise ValueError(provider)


def resolve_key(provider):
    env = PROVIDERS[provider]["env"]
    val = os.environ.get(env)
    if not val and provider == "gemini":
        val = os.environ.get("GOOGLE_API_KEY")
    if not val:
        sys.exit("error: %s is not set. Export it in your shell, or use --dry-run." % env)
    return val


def send(url, headers, body, provider):
    key = resolve_key(provider)
    hdrs = {"content-type": "application/json", "user-agent": "token-diet/0.1 (+https://github.com/uniqaiapp/token-diet)"}
    for k, v in headers.items():
        hdrs[k] = v.replace("$" + PROVIDERS[provider]["env"], key)
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=hdrs, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:500]
        sys.exit("error: %s returned HTTP %s\n%s" % (provider, e.code, detail))
    except urllib.error.URLError as e:
        sys.exit("error: network: %s" % e.reason)


# --------------------------------------------------------------------------- CLI

def answer_line(lang):
    return "Answer in %s." % LANG_NAMES.get(lang, "the language of the original request")


def dry_run_report(provider, model, protected, table, lang):
    url, headers, body = build_request(provider, model, protected)
    lines = ["# token-diet dry run (nothing was sent, no key was read)",
             "provider: %s  model: %s  key: $%s" % (provider, model, PROVIDERS[provider]["env"]),
             "source language: %s  ->  appended line: %s" % (lang, answer_line(lang) if lang != "en" else "(none, already English)"),
             "placeholders: %d" % len(table)]
    for i, (name, orig) in enumerate(table):
        one = orig if "\n" not in orig else orig.split("\n")[0] + " ... (%d lines)" % orig.count("\n")
        lines.append("  %s%d%s  %-11s %s" % (OPEN, i, CLOSE, name, one))
    lines += ["--- protected prompt ---", protected.rstrip("\n"),
              "--- request: POST %s ---" % url,
              json.dumps({"headers": headers, "body": body}, ensure_ascii=False, indent=2, sort_keys=True)]
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Rewrite a prompt as compact English with code, paths and identifiers kept verbatim.",
                                 epilog="Keys are read from environment variables only: " + ", ".join(p["env"] for p in PROVIDERS.values()))
    ap.add_argument("file", help="prompt file, or '-' for stdin")
    ap.add_argument("--provider", choices=sorted(PROVIDERS), default=os.environ.get("TOKEN_DIET_PROVIDER", "openai"))
    ap.add_argument("--model", default=os.environ.get("TOKEN_DIET_MODEL"), help="override the provider's default cheap model")
    ap.add_argument("--answer-in", default="auto", help="language code for the appended 'Answer in ...' line (auto|ru|es|pt|de|...|none)")
    ap.add_argument("--dry-run", action="store_true", help="print placeholders and the exact request; send nothing")
    ap.add_argument("--json", action="store_true", help="print a JSON object instead of plain text")
    ap.add_argument("--out", help="write the result to this file instead of stdout")
    a = ap.parse_args(argv)

    text = sys.stdin.read() if a.file == "-" else open(a.file, encoding="utf-8").read()
    if not text.strip():
        sys.exit("error: empty prompt")
    model = a.model or PROVIDERS[a.provider]["model"]
    lang = detect_language(text) if a.answer_in == "auto" else a.answer_in
    protected, table = protect(text)

    if a.dry_run:
        sys.stdout.write(dry_run_report(a.provider, model, protected, table, lang))
        return 0

    url, headers, body = build_request(a.provider, model, protected)
    data = send(url, headers, body, a.provider)
    rewritten = extract_text(a.provider, data).strip()
    try:
        result = restore(rewritten, table)
    except ValueError as e:
        sys.stderr.write("error: %s\nraw model output follows (not restored):\n%s\n" % (e, rewritten))
        return 3
    if lang not in ("en", "none"):
        result = result.rstrip("\n") + "\n\n" + answer_line(lang) + "\n"
    if len(result) > len(text):
        sys.stderr.write("warning: result is longer than the original (%d > %d chars); the original may already be compact\n"
                         % (len(result), len(text)))
    if a.json:
        result = json.dumps({"prompt": result, "provider": a.provider, "model": model,
                             "answer_in": lang, "placeholders": len(table),
                             "chars_before": len(text), "chars_after": len(result)}, ensure_ascii=False, indent=2) + "\n"
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(result)
        sys.stderr.write("wrote %s\n" % a.out)
    else:
        sys.stdout.write(result if result.endswith("\n") else result + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
