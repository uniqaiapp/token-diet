# AGENTS.md

This repository is an agent skill. The full instructions are in `SKILL.md`; read it first.

## Working in this repo

- Zero dependencies: Python 3.9+ standard library only. Do not add packages.
- Run tests: `python3 tests/run.py` (no network; every committed example output is pinned byte-for-byte).
- Keep `SKILL.md` under 500 lines; long material goes to `references/`.
- Never commit or print API key values. Scripts read keys from environment variables only and show the variable name in dry runs.
- Any number in README or CHANGELOG must come from a script in this repo on data in this repo, labelled with its method (exact `count_tokens` or character estimate).
- Author and maintainer is UniqAI <support@uniqai.app>; do not add personal names anywhere.

## Using this skill from another project

Copy or clone this repo, then follow "Install" in README.md. The one-line summary: when a user's prompt is long and not in English, run `python3 scripts/diet.py` on it, work from the compact English version, and answer in the language named on its last line.
