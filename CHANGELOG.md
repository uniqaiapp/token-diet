# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-10-28

### Added

- `SKILL.md` with the protect → rewrite → verify → restore procedure, the agent workflow, and the three context levers (stable prefix, history window, compact tool output).
- `scripts/diet.py`: compact-English rewrite through OpenAI, Gemini or Anthropic with keys from environment variables; placeholder protection for code, paths, identifiers, flags and quoted strings; placeholder integrity check; `--dry-run`, `--json`, `--out`, `--answer-in`.
- `scripts/measure.py`: before/after token comparison via Anthropic `count_tokens` when `ANTHROPIC_API_KEY` is set, otherwise a labelled character estimate; `--breakdown` for transcripts by source with lever hints; optional `--price-in` cost line using a price you supply.
- `scripts/estimate.py`: the character-based estimator with its assumed rates in one place.
- Six example prompts (ru, es, pt, de) with reference rewrites, pinned dry-run and report fixtures, and one transcript sample.
- Adapters for Claude Code (`.claude-plugin/plugin.json`), Cursor (`.cursor/rules/token-diet.mdc`), Codex (`codex/INSTRUCTIONS.md`) and generic `AGENTS.md`.
- Tests (`python3 tests/run.py`), CI workflow, issue and PR templates, Russian README.
