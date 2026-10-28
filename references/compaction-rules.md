# Compaction rules

The rules `scripts/diet.py` gives the cheap model, written out for an agent (or a person) doing the rewrite by hand. Apply them in order; stop when the prompt reads as a brief, not a message.

## Keep verbatim

Never touch: code blocks and inline code; file paths and file names; URLs; identifiers (`snake_case`, `camelCase`, `PascalCase`, dotted names like `np.array`); command-line flags; environment variable names; quoted strings in any quote style (`"…"`, `'…'`, `«…»`); numbers, versions, limits, dates; product and library names.

If you are unsure whether a word is an identifier, keep it as it is. Keeping a word costs nothing; breaking an identifier costs a wrong answer.

## Drop

- Greetings, sign-offs, thanks, apologies ("Привет!", "заранее спасибо", "sorry to bother you").
- Hedges and softeners ("мне кажется", "наверное", "если не сложно", "I think maybe").
- Commentary about the agent or the asker ("ты же умный", "я не очень разбираюсь").
- Repetition: when a constraint appears twice, keep the stricter phrasing once.
- Explanations of why the asker wants something, unless the reason changes the answer ("because the frontend depends on the response shape" changes the answer; "because my manager asked" does not).
- Markdown headings; a brief rarely needs them.

## Rewrite

- One sentence of context first: stack, file, symptom. Then the task. Then constraints as a list.
- Imperative mood: "Find the root cause", not "I would like you to find".
- Concrete over vague: "roughly 1 in 5 requests" instead of "sometimes, I think"; keep the asker's own estimate, do not invent a sharper one.
- Keep acceptance criteria explicit: "tests in `tests/x.test.ts` must pass", "no new dependencies", "output the complete file".
- Keep the asker's language for user-facing strings (a button label stays in Russian because the UI is in Russian).

## Append

One final line: `Answer in Russian.` (or the asker's language). It costs a handful of tokens and saves a round-trip when the agent would otherwise answer in English.

## Check

- Every protected span from the original is present, exactly once, unchanged.
- Nothing was added that the asker did not say.
- The result is shorter in characters; if it is not, the original was already compact and should be used as is.
- Run `python3 scripts/measure.py before.txt after.txt` and report the method it used.
