---
name: token-diet
description: Cuts LLM token spend for prompts in Russian, Spanish, Portuguese, German or other languages. Rewrites the prompt into compact English with a cheap model the user picks (OpenAI, Gemini or Anthropic, key from an environment variable), keeps code blocks, paths, identifiers and quoted strings verbatim through placeholders, appends an "Answer in <language>" line so the agent still replies in the user's language, and measures before/after with Anthropic count_tokens or a labelled character estimate. Also breaks an agent transcript down by source (system prompt, history, tool output, RAG) to show what to trim. Use when the user asks to reduce token costs, compress a prompt, translate a prompt to English for the agent, asks where the context window goes, mentions prompt caching, or writes "сократи промпт", "экономия токенов", "сожми контекст", "переведи промпт на английский". Not for translating documents for humans, and not for prompts of a few sentences, where the extra call costs more than it saves.
license: MIT
metadata:
  version: 0.1.0
  author: UniqAI
  homepage: https://github.com/uniqaiapp/token-diet
---

# token-diet

Non-English prompts cost more tokens than their English equivalent on every major tokenizer, and prompts written for a chat window carry greetings, hedges and repetition that a coding agent does not need. This skill turns such a prompt into compact English with a cheap model, keeps everything that must stay byte-exact, and makes the agent answer in the user's language. It also tells you, with a script, whether the rewrite saved anything before you say it did.

## When to use

- The user writes in Russian, Ukrainian, Spanish, Portuguese, German or another non-English language and the prompt will be reused: a system prompt, `CLAUDE.md` / `AGENTS.md` section, saved task template, few-shot example, or a long brief that a more expensive model will process.
- The user asks to "reduce token costs", "shorten this prompt", "compress the context", or asks why a session is expensive.
- The user asks where the input tokens go in an agent loop (system prompt vs history vs tool output vs retrieved context).
- Russian triggers: "сократи промпт", "экономия токенов", "сожми контекст", "почему так дорого", "переведи промпт на английский".

## When NOT to use

- One-off chat messages of a few sentences. The rewrite call plus the appended line costs about as much as it saves; just answer.
- Text whose exact wording matters to a human reader: legal text, UI copy, marketing, translations for publication. This produces agent-facing prompts, not translations.
- Prompts that are already compact English. `diet.py` warns when the result is longer than the input; believe the warning.
- When no provider key is available and the agent would have to do the rewrite itself on the expensive model. Then apply the manual rules in `references/compaction-rules.md` only if the prompt will be reused many times.

## How it works

1. **Protect.** `scripts/diet.py` replaces spans that must survive untouched with numbered placeholders (`⟦0⟧`, `⟦1⟧`, ...): fenced code, inline code, URLs, paths, file names, flags, function calls, dotted and snake/camel identifiers, quoted strings. The rules use ASCII-only character classes so Cyrillic words are never mistaken for identifiers.
2. **Rewrite.** The protected text goes to the cheap model with a fixed system prompt (in `diet.py`, `SYSTEM_PROMPT`): compact English, imperative, every requirement kept, every placeholder kept exactly once, no answering, no additions.
3. **Verify.** Every placeholder must come back exactly once. If one is missing, duplicated or invented, the script exits 3 and prints the raw model output to stderr instead of silently shipping a broken prompt.
4. **Restore and tag.** Placeholders are swapped back and a final line is appended: `Answer in Russian.` (language auto-detected; override with `--answer-in`). The agent that receives the prompt follows that line.
5. **Measure.** `scripts/measure.py BEFORE AFTER` counts both files. With `ANTHROPIC_API_KEY` set it calls `POST /v1/messages/count_tokens` (exact, model-specific; pick the model you actually use with `--model`). Without a key it prints a character-based estimate, labelled as such on every line. Only quote the exact numbers.

```
prompt.ru.txt ──protect──▶ ⟦placeholders⟧ ──cheap model──▶ compact EN ──verify+restore──▶ prompt.en.txt + "Answer in Russian."
                                                                                            │
                                                               measure.py before after ◀────┘
```

### Agent procedure

When the skill triggers:

1. Save the user's prompt to a file (or read it from one). Do not paraphrase it first.
2. Run `python3 scripts/diet.py prompt.txt --provider <openai|gemini|anthropic> --out prompt.en.txt`. The provider is the user's choice; if they have not said, ask which key they have, or run `--dry-run` and show what would be sent. Never read, print or guess key values.
3. Show the result and the `measure.py` report. Say which method the report used (exact or estimate) in one line.
4. Use `prompt.en.txt` as the task, and answer in the language named on its last line. Keep answering in that language for the rest of the session unless the user switches.
5. If the user asks about a whole session rather than one prompt, export the transcript as JSON (shape in `measure.py --help`) and run `python3 scripts/measure.py --breakdown transcript.json`. Report the table and the levers it names; do not promise savings you have not measured.

### Beyond translation: the three levers for context tokens

The rewrite helps with what the user types. In an agent loop most input tokens are not typed by the user. `measure.py --breakdown` shows the split; the usual order of wins is:

- **Stable prefix.** Keep the system prompt and tool list byte-identical between calls so prompt caching can hit; move anything that changes per request (dates, IDs, the question) after the stable part.
- **History window.** Keep the last N turns verbatim and a short running summary of the rest; old tool calls and their results are the first thing to drop.
- **Compact tool output.** Truncate long tool results before they enter the context: first and last lines, counts, errors, a path to the full output. Stack traces and test runners are the usual offenders.

Each of these is a change to the harness, not to the prompt. Measure before and after with the same script.

## Inputs / outputs

| Script | Input | Output |
|---|---|---|
| `scripts/diet.py FILE` | prompt in any language; `-` for stdin | compact English prompt with protected spans restored and an `Answer in …` line; `--json` for a JSON object; `--dry-run` for the placeholders and the exact request without sending |
| `scripts/measure.py BEFORE AFTER` | two text files | table: chars, tokens, delta; method stated on line 2 |
| `scripts/measure.py --breakdown FILE.json` | transcript JSON (`system`, `tools`, `rag`, `messages[]`) | tokens and share per source, plus which lever applies |
| `scripts/estimate.py FILE…` | text files | character-based estimate only |

Environment: `OPENAI_API_KEY`, `GEMINI_API_KEY` (or `GOOGLE_API_KEY`), `ANTHROPIC_API_KEY`; optional `TOKEN_DIET_PROVIDER`, `TOKEN_DIET_MODEL`. Defaults per provider are in `references/providers.md`.

## Examples

`examples/` holds six prompts (ru ×3, es, pt, de) with a reference rewrite, the dry-run output and the measurement report for each, plus one transcript for `--breakdown`. Reproduce any of them:

```bash
python3 scripts/diet.py examples/ru-01-bugfix/before.txt --dry-run
python3 scripts/measure.py examples/ru-01-bugfix/before.txt examples/ru-01-bugfix/after.txt --estimate
python3 scripts/measure.py --breakdown examples/transcript/transcript.sample.json --estimate
```

The committed reports are pinned by `tests/test_scripts.py`; the `after.txt` files are reference rewrites written by the maintainers to the rules above, not model output, and are labelled so in `examples/README.md`.

## Limits

- Comments inside code fences are kept verbatim, so Russian comments in code stay Russian. Ask the agent to translate them separately if that matters.
- Language detection is script-and-stopword based; mixed-language prompts fall back to the dominant script, and unknown languages get a generic "answer in the language of the original request" line.
- The character estimate is a heuristic with assumed rates (`scripts/estimate.py`, `RATES`). It is for orientation when no key is available, never for a claim.
- A cheap model can still drop a nuance. The verify step guarantees the protected spans, not the prose; read the result once before reusing it.
- The protection rules are regexes and will occasionally protect an ordinary word that looks like an identifier (`and/or`, `Next.js`). That is harmless: it stays verbatim.
- Only three providers are wired. Any OpenAI-compatible endpoint works by setting `--provider openai` and pointing `OPENAI_BASE_URL`-style proxies in front; this script does not read that variable itself.

## References

- `references/compaction-rules.md`: the rewrite rules in human form, for agents working without a provider key.
- `references/providers.md`: request shapes, default models, how to choose a cheap model and what to override.
