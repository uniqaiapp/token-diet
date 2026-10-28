# Providers

`scripts/diet.py` talks to three APIs with plain `urllib`. Keys come from environment variables only; the request builders put the variable name in the header and `send()` swaps in the value at the last moment, which is why `--dry-run` can print the complete request without ever reading a key.

| `--provider` | Key variable | Default model (cheap tier as of 2026-10) | Endpoint |
|---|---|---|---|
| `openai` | `OPENAI_API_KEY` | `gpt-5-mini` | `POST https://api.openai.com/v1/chat/completions` |
| `gemini` | `GEMINI_API_KEY` (fallback `GOOGLE_API_KEY`) | `gemini-2.5-flash-lite` | `POST https://generativelanguage.googleapis.com/v1beta/models/<model>:generateContent` |
| `anthropic` | `ANTHROPIC_API_KEY` | `claude-haiku-5-5` | `POST https://api.anthropic.com/v1/messages` (header `anthropic-version: 2023-06-01`) |

Override the model with `--model` or `TOKEN_DIET_MODEL`; set `TOKEN_DIET_PROVIDER` to skip `--provider`. Model names change; if a default stops working, pass the current cheap model of your provider explicitly and open a pull request updating `PROVIDERS` in `diet.py` and this table.

## Choosing the model

The rewrite is a translation-and-trim task with hard constraints checked by the script (placeholders) and soft ones (nuance) checked by you. The smallest current model of each provider handles it; use a bigger one only if the verify step keeps failing on a particular prompt, which usually means placeholders inside unusual markup.

Rough rule: the rewrite is worth it when the prompt will be sent more than once (system prompts, templates, briefs) or when the receiving model is several times more expensive per token than the rewriting one. For a single short chat message, skip it.

## Request shapes

OpenAI (chat completions):

```json
{"model": "gpt-5-mini",
 "messages": [{"role": "system", "content": "<SYSTEM_PROMPT>"},
              {"role": "user", "content": "<protected prompt>"}]}
```

Gemini (`generateContent`):

```json
{"system_instruction": {"parts": [{"text": "<SYSTEM_PROMPT>"}]},
 "contents": [{"role": "user", "parts": [{"text": "<protected prompt>"}]}],
 "generationConfig": {"temperature": 0}}
```

Anthropic (Messages):

```json
{"model": "claude-haiku-5-5", "max_tokens": 4096,
 "system": "<SYSTEM_PROMPT>",
 "messages": [{"role": "user", "content": "<protected prompt>"}]}
```

Anthropic responses with `stop_reason: "refusal"` are reported as an error rather than parsed.

## Counting

`scripts/measure.py` uses `POST https://api.anthropic.com/v1/messages/count_tokens` with `{"model": "<model>", "messages": [{"role": "user", "content": "<text>"}]}` and reads `input_tokens`. Counts are model-specific; pass `--model` with the model that will actually process the prompt. The default is `claude-opus-5-5`. There is no OpenAI or Gemini counting path in this repo; for those, the character estimate is all you get offline, and it is labelled as such.

## Proxies and compatible endpoints

The script does not read base-URL variables. If you route through a proxy or an OpenAI-compatible server, change the URL in `build_request` or wrap the script; keep the key in an environment variable either way.
