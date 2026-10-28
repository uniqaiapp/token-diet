<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/banner-light.svg">
  <img alt="token-diet: cut prompt and context tokens without losing meaning" src="assets/banner.svg" width="1280" height="320">
</picture>

<h1>token-diet: reduce LLM token costs in agents and apps</h1>

[![License: MIT](https://img.shields.io/badge/license-MIT-d1fe17?style=flat-square&labelColor=0d0f12)](LICENSE)
[![Claude Code skill](https://img.shields.io/badge/Claude_Code-skill-d1fe17?style=flat-square&labelColor=0d0f12)](#install)
[![Cursor](https://img.shields.io/badge/Cursor-rules-d1fe17?style=flat-square&labelColor=0d0f12)](#install)
[![Codex](https://img.shields.io/badge/Codex-AGENTS.md-d1fe17?style=flat-square&labelColor=0d0f12)](#install)
[![Made by UniqAI](https://img.shields.io/badge/made_by-UniqAI-fdfc07?style=flat-square&labelColor=0d0f12)](https://uniqai.app/?utm_source=github&utm_medium=readme&utm_campaign=token-diet)

**Compact English prompts from any language, code kept verbatim, savings measured not promised.**

[Quickstart](#quickstart) · [How it works](#how-it-works) · [Examples](#examples) · [Install](#install) · [FAQ](#faq)

[Русская версия](README.ru.md)

</div>

Reduce LLM token costs in Claude Code, Cursor, Codex and your own apps by measuring first. Prompts written in Russian, Spanish, Portuguese or German cost more tokens than the same brief in English, and prompts written for a chat window carry greetings, hedges and repetition an agent does not need. `token-diet` sends such a prompt through a cheap model of your choice, brings back compact English with every code block, path, identifier and quoted string untouched, tells the agent to answer in your language, and then counts the tokens before and after with Anthropic's `count_tokens` endpoint (or a clearly labelled estimate when you have no key). For whole agent sessions it breaks the input down by source, so you see whether the system prompt, the history, tool output or retrieved context is the thing to trim.

| **Protect, then rewrite** | **Answer in your language** | **Measure before you claim** |
|:---|:---|:---|
| Code fences, inline code, paths, flags, identifiers and quoted strings become placeholders; the cheap model never sees or edits them, and a missing placeholder fails the run. | One appended line, `Answer in Russian.`, keeps the agent replying to you the way you wrote, while the task itself travels in short English. | `measure.py` prints exact `count_tokens` figures with a key and a character estimate without one, and says on line two which it used. |

## Quickstart

```bash
git clone https://github.com/uniqaiapp/token-diet ~/.claude/skills/token-diet
cd ~/.claude/skills/token-diet
python3 scripts/diet.py examples/ru-01-bugfix/before.txt --dry-run      # no key, no network
python3 scripts/measure.py examples/ru-01-bugfix/before.txt examples/ru-01-bugfix/after.txt
```

The first command lists the eight spans it would protect in a Russian bug report and the exact request it would send. The second prints a before/after table for the reference rewrite; with `ANTHROPIC_API_KEY` set in your shell it uses `count_tokens`, otherwise it prints an estimate and says so. Python 3.9+, no packages to install.

## Demo

<img alt="token-diet demo: a dry run listing protected placeholders, then a before/after token report" src="assets/demo.svg" width="820">

## How it works

1. **Protect.** `scripts/diet.py` scans the prompt with ASCII-only rules (so Cyrillic words are never mistaken for identifiers) and replaces fenced code, inline code, URLs, paths, file names, flags, calls, dotted and snake/camel identifiers and quoted strings with numbered placeholders `⟦0⟧ … ⟦n⟧`.
2. **Rewrite.** The protected text goes to the provider you pick (`--provider openai|gemini|anthropic`, key from `OPENAI_API_KEY`, `GEMINI_API_KEY` or `ANTHROPIC_API_KEY`) with a fixed system prompt: compact English, imperative, every requirement kept, no answering, no additions. Default models are the cheap tier of each provider; override with `--model`.
3. **Verify and restore.** Every placeholder must come back exactly once. If not, the script exits with code 3 and shows the raw output instead of shipping a broken prompt. Then placeholders are swapped back and `Answer in <language>.` is appended (auto-detected; `--answer-in` overrides).
4. **Measure.** `scripts/measure.py BEFORE AFTER` counts both files. With `ANTHROPIC_API_KEY` set it calls `POST /v1/messages/count_tokens` for the model you name with `--model` (counts are model-specific). Without a key it falls back to `scripts/estimate.py`, a character-based heuristic whose assumed rates sit in one dictionary at the top of the file, and labels every line as an estimate.
5. **Break down a session.** `scripts/measure.py --breakdown transcript.json` splits an agent transcript into system prompt, tools, history, tool output, retrieved context and the current turn, prints each one's share, and names the lever that applies: stable prefix for caching, a history window, or compact tool results.

```
prompt.ru.txt ─protect─▶ ⟦placeholders⟧ ─cheap model─▶ compact EN ─verify+restore─▶ prompt.en.txt + "Answer in Russian."
                                                                                        │
                                                      measure.py before after ◀─────────┘
```

No percentage appears in this README on purpose. Every number the tools print comes from a file in `examples/` and is pinned by the test suite; run the commands above to see them, and run them with a key to get exact counts for your own model.

## Examples

<details>
<summary><b>Russian bug report → compact English brief (examples/ru-01-bugfix)</b></summary>

**Before** (1596 characters; the full file is `examples/ru-01-bugfix/before.txt`)

```text
Привет! Слушай, у меня тут проблема с Next.js приложением, и я уже довольно долго пытаюсь её решить,
но что-то никак не получается, поэтому решил обратиться к тебе. В общем, суть в том, что когда
пользователь открывает страницу src/app/video/page.tsx и нажимает на кнопку "Сгенерировать", то иногда
(не всегда, а примерно в одном случае из пяти, как мне кажется) запрос к API уходит дважды …
```

**After** (`examples/ru-01-bugfix/after.txt`, a reference rewrite written to the rules in `references/compaction-rules.md`)

```text
Next.js app: clicking "Сгенерировать" on src/app/video/page.tsx sometimes (roughly 1 in 5) sends the POST
to the API twice, so the user is charged twice.

Suspect src/hooks/useGenerate.ts:
[code block kept verbatim]

Tasks:
- Find the real root cause, not a guess.
- Propose a fix that keeps tests/generate.test.ts passing.
- No new dependencies.
- Changing src/app/api/generate/route.ts (e.g. an idempotency key) is fine; explain how it works.

Answer in Russian.
```

`python3 scripts/measure.py examples/ru-01-bugfix/before.txt examples/ru-01-bugfix/after.txt --estimate` prints the committed `report.txt`.

</details>

<details>
<summary><b>Where the tokens go in an agent session (examples/transcript)</b></summary>

```bash
python3 scripts/measure.py --breakdown examples/transcript/transcript.sample.json
```

The sample is a short synthetic Next.js debugging session: one Russian question, two tool calls, a failing Vitest run. The report lists each source with its share and, because the test runner's output dominates, suggests truncating tool results before they enter the context. The committed output is `examples/transcript/breakdown.txt`.

</details>

<details>
<summary><b>Spanish, Portuguese and German briefs</b></summary>

`examples/es-01-api`, `examples/pt-01-tests` and `examples/de-01-docs` follow the same layout: `before.txt`, a reference `after.txt`, the `dry-run.txt` showing which spans were protected, and `report.txt`. `examples/README.md` lists what each one exercises.

</details>

## Install

Works with every agent that reads instruction files. Pick yours. Requirements: Python 3.9+. No packages to install.

<details open>
<summary><b>Claude Code</b></summary>

```bash
# user-level (every project)
git clone https://github.com/uniqaiapp/token-diet ~/.claude/skills/token-diet
# or project-level
git clone https://github.com/uniqaiapp/token-diet .claude/skills/token-diet
```

Then type `/token-diet` in a session, or just describe the task; the skill's `description` triggers on "reduce token costs", "compress this prompt", "сократи промпт", "экономия токенов". As a plugin, once the uniqaiapp marketplace is published: `/plugin marketplace add uniqaiapp/skills` then `/plugin install token-diet@uniqaiapp`.

</details>

<details>
<summary><b>Cursor</b></summary>

Copy `SKILL.md`, `scripts/`, `references/` and [`.cursor/rules/token-diet.mdc`](.cursor/rules/token-diet.mdc) into your project. The rule file embeds the skill with `@SKILL.md`.

</details>

<details>
<summary><b>Codex / any AGENTS.md agent</b></summary>

Copy `SKILL.md`, `scripts/` and `references/` into `.agents/skills/token-diet/` and add the snippet from [`codex/INSTRUCTIONS.md`](codex/INSTRUCTIONS.md) to your `AGENTS.md`. This repo's own [`AGENTS.md`](AGENTS.md) shows the shape.

</details>

<details>
<summary><b>Without an agent</b></summary>

Every script runs standalone: `python3 scripts/diet.py --help`, `python3 scripts/measure.py --help`, `python3 scripts/estimate.py --help`. The rewrite rules are also written out for humans in [`references/compaction-rules.md`](references/compaction-rules.md).

</details>

## Limits and honesty

- Comments inside code fences stay in the original language; the protect step keeps code byte-exact by design.
- The character estimate is a heuristic. Its five assumed rates live in `scripts/estimate.py`; change them and the pinned reports change with them, which is what the tests are for. Do not quote an estimate as a measurement.
- The verify step guarantees placeholders, not nuance. A cheap model can drop a qualifier; read the result once before you reuse it as a template.
- Language detection is script-and-stopword based (ru, uk, es, pt, de, fr, it). Other languages get a generic "answer in the language of the original request" line; pass `--answer-in` to be precise.
- The `after.txt` files in `examples/` are reference rewrites by the maintainers, not model output. They show the target; your model's output will differ.
- The rewrite is worth it when a prompt is reused or when the receiving model is much more expensive than the rewriting one. For a one-line chat message it is not, and `diet.py` warns when the result is longer than the input.

## FAQ

<details>
<summary><b>Does it work without an API key?</b></summary>

Partly. `--dry-run` shows the protected prompt and the exact request without sending anything, `measure.py` falls back to a labelled estimate, and `references/compaction-rules.md` lets an agent do the rewrite by hand. A real rewrite needs one key for one of the three providers, read from the environment.

</details>

<details>
<summary><b>Why send the prompt to another model at all? The agent could just translate it.</b></summary>

It could, at the agent's price per token and inside the agent's context. The point is to do the trim once on a cheap model and then reuse the compact version: in `CLAUDE.md` or `AGENTS.md`, as a saved task template, as a system prompt, as few-shot examples. For a single short message, skip it.

</details>

<details>
<summary><b>Will the agent still answer in Russian?</b></summary>

Yes. The last line of the rewritten prompt says `Answer in Russian.` (or Spanish, Portuguese, German, …), and `SKILL.md` tells the agent to keep that language for the session. The button labels and quoted strings in your prompt stay in the original language too, because they are protected.

</details>

<details>
<summary><b>Which model counts the tokens?</b></summary>

`measure.py --model` names it; the default is `claude-opus-5-5`. Counts are tokenizer-specific, so count with the model that will actually receive the prompt. There is no OpenAI or Gemini counting path here; for those providers you get the estimate, labelled as such.

</details>

<details>
<summary><b>Is my prompt stored anywhere?</b></summary>

Only where you send it. The scripts write to stdout or the `--out` file you name and keep no cache or log. What the provider retains is governed by that provider's terms.

</details>

## Related

- [skill-shrinker](https://github.com/uniqaiapp/skill-shrinker): shrink any SKILL.md or agent instruction file: measures size, moves long material to references, keeps the triggers intact.
- [model-router](https://github.com/uniqaiapp/model-router): pick the cheapest model that can do the job: a rule table and a stdlib script that routes tasks by type, length and risk.
- [deslop-ru](https://github.com/uniqaiapp/deslop-ru): strip AI-sounding filler from Russian text: a skill plus a stdlib script that flags and rewrites the usual tells.

## Contributing

Issues and pull requests are welcome. Keep changes small and include a before/after example in the PR description.
See [CONTRIBUTING.md](CONTRIBUTING.md) for the local checks (`python3 tests/run.py`, no dependencies).

## License

[MIT](LICENSE) © UniqAI

---

<div align="center">

<sub>Made by <a href="https://uniqai.app/?utm_source=github&utm_medium=readme&utm_campaign=token-diet">UniqAI</a> — Kling 3.0, Veo 3, Flux, Nano Banana and GPT-5/Claude/Gemini/Grok in one app. We pay these token bills ourselves; this is how we keep our own prompts short.</sub>

</div>
