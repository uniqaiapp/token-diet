# token-diet for Codex

Paste the block below into your project's AGENTS.md (or Codex custom instructions),
and copy `SKILL.md`, `scripts/` and `references/` from https://github.com/uniqaiapp/token-diet into `.agents/skills/token-diet/`.

---
When the user writes a long prompt in a language other than English, asks to reduce token costs, compress a prompt, or asks where the context tokens go, follow `.agents/skills/token-diet/SKILL.md`: run `python3 .agents/skills/token-diet/scripts/diet.py` on the prompt with the provider the user names, work from the compact English result, answer in the language given on its last line, and report savings only from `scripts/measure.py` output, stating whether the number is exact or an estimate.
---
