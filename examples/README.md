# Examples

Each folder is one prompt somebody would actually type to a coding agent, in its original language, with everything needed to reproduce the numbers.

| Folder | Language | What it shows |
|---|---|---|
| `ru-01-bugfix` | Russian | long bug report with a TypeScript code block, four paths and a hook name |
| `ru-02-refactor` | Russian | refactor brief with flags, env var names, function names and «» quotes |
| `ru-03-sql` | Russian | SQL question with inline code, table names and an index name |
| `es-01-api` | Spanish | FastAPI change with quoted status strings and a `Depends(get_db)` call |
| `pt-01-tests` | Portuguese | test-writing brief with many short quoted inputs |
| `de-01-docs` | German | documentation task with a Go install command and file paths |
| `transcript` | mixed | a synthetic agent transcript for `measure.py --breakdown` |

## Files in each folder

| File | Produced by | Notes |
|---|---|---|
| `before.txt` | written by hand | the original prompt |
| `after.txt` | written by hand | a reference rewrite following `references/compaction-rules.md`. It is not model output; it shows the target shape, and the test suite checks that it keeps every protected span of `before.txt` verbatim and is shorter |
| `dry-run.txt` | `python3 scripts/diet.py <folder>/before.txt --dry-run --provider openai` | the placeholders and the exact request body; nothing is sent |
| `report.txt` | `python3 scripts/measure.py <folder>/before.txt <folder>/after.txt --estimate` | character-based ESTIMATE, labelled; run without `--estimate` and with `ANTHROPIC_API_KEY` set for an exact count |

`transcript/breakdown.txt` is `python3 scripts/measure.py --breakdown examples/transcript/transcript.sample.json --estimate`.

All of these are pinned byte-for-byte by `tests/test_scripts.py`. To get a real rewrite instead of the reference one:

```bash
python3 scripts/diet.py examples/ru-01-bugfix/before.txt --provider openai --out /tmp/ru-01.en.txt
python3 scripts/measure.py examples/ru-01-bugfix/before.txt /tmp/ru-01.en.txt
```

The second command reports an exact `count_tokens` figure when `ANTHROPIC_API_KEY` is set and an estimate otherwise; the first line of its output says which.
