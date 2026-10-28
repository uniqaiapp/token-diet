<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/banner-light.svg">
  <img alt="token-diet: cut prompt and context tokens without losing meaning" src="assets/banner.svg" width="1280" height="320">
</picture>

<h1>token-diet: 에이전트와 앱의 LLM 토큰 비용 줄이기</h1>

[![License: MIT](https://img.shields.io/badge/license-MIT-d1fe17?style=flat-square&labelColor=0d0f12)](LICENSE)
[![Claude Code skill](https://img.shields.io/badge/Claude_Code-skill-d1fe17?style=flat-square&labelColor=0d0f12)](#설치)
[![Cursor](https://img.shields.io/badge/Cursor-rules-d1fe17?style=flat-square&labelColor=0d0f12)](#설치)
[![Codex](https://img.shields.io/badge/Codex-AGENTS.md-d1fe17?style=flat-square&labelColor=0d0f12)](#설치)
[![Made by UniqAI](https://img.shields.io/badge/made_by-UniqAI-fdfc07?style=flat-square&labelColor=0d0f12)](https://uniqai.app/?utm_source=github&utm_medium=readme-ko&utm_campaign=token-diet)

**어떤 언어의 프롬프트든 간결한 영어로. 코드는 그대로, 절감량은 약속이 아니라 측정으로.**

[빠른 시작](#빠른-시작) · [동작 방식](#동작-방식) · [예시](#예시) · [설치](#설치) · [자주 묻는 질문](#자주-묻는-질문)

</div>

[English](README.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Português (BR)](README.pt-BR.md) · [日本語](README.ja.md) · 한국어

먼저 측정하는 것으로 Claude Code, Cursor, Codex, 그리고 직접 만든 앱의 LLM 토큰 비용을 줄입니다. 러시아어, 스페인어, 포르투갈어, 독일어로 쓴 프롬프트는 같은 내용을 영어로 쓴 것보다 토큰을 더 많이 씁니다. 채팅창용으로 쓴 프롬프트에는 인사말, 에두르는 표현, 반복처럼 에이전트에게 필요 없는 것이 섞여 있습니다. `token-diet`는 그런 프롬프트를 원하는 저렴한 모델에 통과시켜, 코드 블록, 경로, 식별자, 따옴표 안 문자열은 하나도 건드리지 않은 간결한 영어를 받아오고, 에이전트에게는 여러분의 언어로 답하라고 지시한 뒤, Anthropic의 `count_tokens` 엔드포인트로 전후 토큰 수를 셉니다(키가 없으면 추정치임을 분명히 표시한 값을 냅니다). 에이전트 세션 전체에 대해서는 입력을 출처별로 쪼개 주므로, 잘라내야 할 것이 시스템 프롬프트인지, 히스토리인지, 도구 출력인지, 검색된 컨텍스트인지 바로 보입니다.

| **먼저 보호하고, 그다음 재작성** | **여러분의 언어로 답변** | **주장하기 전에 측정** |
|:---|:---|:---|
| 코드 펜스, 인라인 코드, 경로, 플래그, 식별자, 따옴표 안 문자열은 플레이스홀더가 됩니다. 저렴한 모델은 이것을 보지도 고치지도 못하며, 플레이스홀더가 하나라도 빠지면 실행이 실패합니다. | 끝에 덧붙는 한 줄 `Answer in Russian.` 덕분에, 작업 자체는 짧은 영어로 전달되면서도 에이전트는 여러분이 쓴 언어로 계속 답합니다. | `measure.py`는 키가 있으면 정확한 `count_tokens` 수치를, 없으면 글자 수 기반 추정치를 출력하고, 둘 중 무엇을 썼는지 두 번째 줄에 밝힙니다. |

## 빠른 시작

```bash
git clone https://github.com/uniqaiapp/token-diet ~/.claude/skills/token-diet
cd ~/.claude/skills/token-diet
python3 scripts/diet.py examples/ru-01-bugfix/before.txt --dry-run      # no key, no network
python3 scripts/measure.py examples/ru-01-bugfix/before.txt examples/ru-01-bugfix/after.txt
```

첫 번째 명령은 러시아어 버그 리포트에서 보호 대상이 되는 여덟 개 구간과 실제로 보낼 요청을 그대로 보여줍니다. 두 번째는 참조용 재작성본에 대한 before/after 표를 출력합니다. 셸에 `ANTHROPIC_API_KEY`가 설정되어 있으면 `count_tokens`를 쓰고, 없으면 추정치를 출력하면서 그렇다고 밝힙니다. Python 3.9+, 설치할 패키지는 없습니다.

## 데모

<img alt="token-diet demo: a dry run listing protected placeholders, then a before/after token report" src="assets/demo.svg" width="820">

## 동작 방식

1. **보호.** `scripts/diet.py`는 ASCII 전용 규칙으로 프롬프트를 훑어(그래서 키릴 문자 단어가 식별자로 오인되는 일은 없습니다) 펜스 코드, 인라인 코드, URL, 경로, 파일명, 플래그, 함수 호출, 점으로 이어진 식별자, snake_case/camelCase 식별자, 따옴표 안 문자열을 번호가 붙은 플레이스홀더 `⟦0⟧ … ⟦n⟧`로 바꿉니다.
2. **재작성.** 보호된 텍스트는 선택한 provider(`--provider openai|gemini|anthropic`, 키는 `OPENAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`에서 읽음)로 고정된 시스템 프롬프트와 함께 전송됩니다. 간결한 영어, 명령형, 모든 요구 사항 유지, 답변 금지, 추가 금지입니다. 기본 모델은 각 provider의 저가 티어이며 `--model`로 바꿀 수 있습니다.
3. **검증과 복원.** 모든 플레이스홀더가 정확히 한 번씩 돌아와야 합니다. 아니면 스크립트는 종료 코드 3으로 멈추고, 망가진 프롬프트를 내보내는 대신 원본 출력을 보여줍니다. 그다음 플레이스홀더를 원래 내용으로 되돌리고 `Answer in <language>.`를 덧붙입니다(자동 감지, `--answer-in`으로 덮어쓰기 가능).
4. **측정.** `scripts/measure.py BEFORE AFTER`는 두 파일을 셉니다. `ANTHROPIC_API_KEY`가 설정되어 있으면 `--model`로 지정한 모델에 대해 `POST /v1/messages/count_tokens`를 호출합니다(수치는 모델마다 다릅니다). 키가 없으면 `scripts/estimate.py`로 대체합니다. 이것은 글자 수 기반 휴리스틱으로, 가정한 비율은 파일 맨 위의 딕셔너리 하나에 모여 있고, 모든 줄에 추정치라는 표시가 붙습니다.
5. **세션 분해.** `scripts/measure.py --breakdown transcript.json`은 에이전트 트랜스크립트를 시스템 프롬프트, 도구, 히스토리, 도구 출력, 검색된 컨텍스트, 현재 턴으로 나누고, 각각의 비중을 출력한 뒤 적용할 수단을 짚어 줍니다. 캐싱을 위한 안정적인 프리픽스, 히스토리 윈도우, 또는 도구 결과 압축입니다.

```
prompt.ru.txt ─protect─▶ ⟦placeholders⟧ ─cheap model─▶ compact EN ─verify+restore─▶ prompt.en.txt + "Answer in Russian."
                                                                                        │
                                                      measure.py before after ◀─────────┘
```

이 README에는 일부러 퍼센트를 하나도 적지 않았습니다. 도구가 출력하는 숫자는 모두 `examples/`의 파일에서 나오고 테스트 스위트가 고정합니다. 위 명령을 실행하면 볼 수 있고, 키를 넣고 실행하면 자신의 모델에 맞는 정확한 수치를 얻습니다.

## 예시

<details>
<summary><b>러시아어 버그 리포트 → 간결한 영어 브리프 (examples/ru-01-bugfix)</b></summary>

**Before** (1596자. 전체 파일은 `examples/ru-01-bugfix/before.txt`)

```text
Привет! Слушай, у меня тут проблема с Next.js приложением, и я уже довольно долго пытаюсь её решить,
но что-то никак не получается, поэтому решил обратиться к тебе. В общем, суть в том, что когда
пользователь открывает страницу src/app/video/page.tsx и нажимает на кнопку "Сгенерировать", то иногда
(не всегда, а примерно в одном случае из пяти, как мне кажется) запрос к API уходит дважды …
```

**After** (`examples/ru-01-bugfix/after.txt`, `references/compaction-rules.md`의 규칙에 따라 쓴 참조용 재작성본)

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

`python3 scripts/measure.py examples/ru-01-bugfix/before.txt examples/ru-01-bugfix/after.txt --estimate`를 실행하면 커밋된 `report.txt`와 같은 내용이 출력됩니다.

</details>

<details>
<summary><b>에이전트 세션에서 토큰은 어디로 가는가 (examples/transcript)</b></summary>

```bash
python3 scripts/measure.py --breakdown examples/transcript/transcript.sample.json
```

샘플은 짧게 합성한 Next.js 디버깅 세션입니다. 러시아어 질문 하나, 도구 호출 두 번, 실패하는 Vitest 실행 한 번. 보고서는 출처마다 비중을 나열하고, 테스트 러너 출력이 대부분을 차지하므로 도구 결과를 컨텍스트에 넣기 전에 잘라내라고 제안합니다. 커밋된 출력은 `examples/transcript/breakdown.txt`입니다.

</details>

<details>
<summary><b>스페인어, 포르투갈어, 독일어 브리프</b></summary>

`examples/es-01-api`, `examples/pt-01-tests`, `examples/de-01-docs`도 같은 구성입니다. `before.txt`, 참조용 `after.txt`, 어떤 구간이 보호됐는지 보여주는 `dry-run.txt`, 그리고 `report.txt`. 각각이 무엇을 검증하는지는 `examples/README.md`에 정리되어 있습니다.

</details>

## 설치

지시 파일을 읽는 에이전트라면 모두 지원합니다. 쓰는 것을 고르세요. 요구 사항: Python 3.9+. 설치할 패키지는 없습니다.

<details open>
<summary><b>Claude Code</b></summary>

```bash
# user-level (every project)
git clone https://github.com/uniqaiapp/token-diet ~/.claude/skills/token-diet
# or project-level
git clone https://github.com/uniqaiapp/token-diet .claude/skills/token-diet
```

그다음 세션에서 `/token-diet`를 입력하거나 그냥 작업을 설명하면 됩니다. 스킬의 `description`은 "reduce token costs", "compress this prompt", "сократи промпт", "экономия токенов"에 반응합니다. 플러그인으로 쓰려면 uniqaiapp 마켓플레이스가 공개된 뒤 `/plugin marketplace add uniqaiapp/skills`에 이어 `/plugin install token-diet@uniqaiapp`을 실행합니다.

</details>

<details>
<summary><b>Cursor</b></summary>

`SKILL.md`, `scripts/`, `references/`, [`.cursor/rules/token-diet.mdc`](.cursor/rules/token-diet.mdc)를 프로젝트에 복사합니다. 규칙 파일은 `@SKILL.md`로 스킬을 포함합니다.

</details>

<details>
<summary><b>Codex / AGENTS.md를 읽는 모든 에이전트</b></summary>

`SKILL.md`, `scripts/`, `references/`를 `.agents/skills/token-diet/`에 복사하고 [`codex/INSTRUCTIONS.md`](codex/INSTRUCTIONS.md)의 스니펫을 자신의 `AGENTS.md`에 추가합니다. 이 저장소의 [`AGENTS.md`](AGENTS.md)가 그 형태를 보여줍니다.

</details>

<details>
<summary><b>에이전트 없이</b></summary>

모든 스크립트는 단독으로 실행됩니다. `python3 scripts/diet.py --help`, `python3 scripts/measure.py --help`, `python3 scripts/estimate.py --help`. 재작성 규칙은 사람이 읽을 수 있는 형태로 [`references/compaction-rules.md`](references/compaction-rules.md)에도 적혀 있습니다.

</details>

## 한계와 솔직한 고지

- 코드 펜스 안의 주석은 원래 언어 그대로 남습니다. 보호 단계는 의도적으로 코드를 바이트 단위로 보존합니다.
- 글자 수 기반 추정은 휴리스틱입니다. 가정한 다섯 가지 비율은 `scripts/estimate.py`에 있으며, 이를 바꾸면 고정된 보고서도 함께 바뀝니다. 테스트가 있는 이유가 그것입니다. 추정치를 측정값처럼 인용하지 마세요.
- 검증 단계가 보장하는 것은 플레이스홀더이지 뉘앙스가 아닙니다. 저렴한 모델은 한정어를 빠뜨릴 수 있습니다. 템플릿으로 재사용하기 전에 결과를 한 번은 읽어 보세요.
- 언어 감지는 문자 체계와 불용어 기반입니다(ru, uk, es, pt, de, fr, it). 그 밖의 언어에는 일반적인 "answer in the language of the original request" 줄이 붙습니다. 정확하게 하려면 `--answer-in`을 넘기세요.
- `examples/`의 `after.txt` 파일은 메인테이너가 쓴 참조용 재작성본이지 모델 출력이 아닙니다. 목표 형태를 보여줄 뿐이며, 여러분 모델의 출력은 다를 것입니다.
- 재작성은 프롬프트를 재사용할 때, 또는 받는 모델이 재작성하는 모델보다 훨씬 비쌀 때 값어치를 합니다. 한 줄짜리 채팅 메시지에는 아니며, 결과가 입력보다 길어지면 `diet.py`가 경고합니다.

## 자주 묻는 질문

<details>
<summary><b>API 키 없이도 동작하나요?</b></summary>

부분적으로 됩니다. `--dry-run`은 아무것도 보내지 않고 보호된 프롬프트와 실제 요청을 보여주고, `measure.py`는 표시가 붙은 추정치로 대체하며, `references/compaction-rules.md`가 있으면 에이전트가 직접 재작성할 수 있습니다. 진짜 재작성에는 세 provider 중 하나의 키가 하나 필요하며, 환경 변수에서 읽습니다.

</details>

<details>
<summary><b>왜 굳이 다른 모델에 프롬프트를 보내나요? 에이전트가 직접 번역하면 되지 않나요?</b></summary>

할 수는 있지만, 에이전트의 토큰 단가로, 에이전트의 컨텍스트 안에서 하게 됩니다. 핵심은 저렴한 모델에서 한 번만 줄이고, 그 간결한 버전을 재사용하는 것입니다. `CLAUDE.md`나 `AGENTS.md`에 넣거나, 저장된 작업 템플릿으로, 시스템 프롬프트로, few-shot 예시로 쓰는 식입니다. 짧은 메시지 하나라면 건너뛰세요.

</details>

<details>
<summary><b>에이전트가 여전히 러시아어로 답하나요?</b></summary>

네. 재작성된 프롬프트의 마지막 줄은 `Answer in Russian.`(또는 Spanish, Portuguese, German 등)이고, `SKILL.md`는 에이전트에게 세션 내내 그 언어를 유지하라고 지시합니다. 프롬프트 안의 버튼 라벨과 따옴표 안 문자열도 보호되므로 원래 언어 그대로 남습니다.

</details>

<details>
<summary><b>토큰은 어떤 모델이 세나요?</b></summary>

`measure.py --model`로 지정한 모델이며, 기본값은 `claude-opus-5-5`입니다. 수치는 토크나이저에 따라 다르므로, 실제로 프롬프트를 받을 모델로 세세요. OpenAI나 Gemini용 카운트 경로는 여기 없습니다. 그 provider들에 대해서는 추정치임을 표시한 값을 받게 됩니다.

</details>

<details>
<summary><b>제 프롬프트가 어딘가에 저장되나요?</b></summary>

여러분이 보낸 곳에만 남습니다. 스크립트는 stdout이나 `--out`으로 지정한 파일에 쓸 뿐, 캐시나 로그를 남기지 않습니다. provider가 무엇을 보관하는지는 해당 provider의 약관을 따릅니다.

</details>

## 관련 프로젝트

- [skill-shrinker](https://github.com/uniqaiapp/skill-shrinker): SKILL.md나 에이전트 지시 파일을 줄입니다. 크기를 재고, 긴 내용은 references로 옮기고, 트리거는 그대로 유지합니다.
- [model-router](https://github.com/uniqaiapp/model-router): 일을 해낼 수 있는 가장 저렴한 모델을 고릅니다. 규칙 표와, 작업을 유형·길이·위험도로 분배하는 표준 라이브러리 스크립트.
- [deslop-ru](https://github.com/uniqaiapp/deslop-ru): 러시아어 텍스트에서 AI 티 나는 군더더기를 걷어냅니다. 스킬과, 흔한 버릇을 찾아 고쳐 쓰는 표준 라이브러리 스크립트.

## 기여하기

이슈와 pull request를 환영합니다. 변경은 작게 유지하고 PR 설명에 before/after 예시를 하나 넣어 주세요.
로컬 검사(`python3 tests/run.py`, 의존성 없음)는 [CONTRIBUTING.md](CONTRIBUTING.md)를 참고하세요.

## 라이선스

[MIT](LICENSE) © UniqAI

---

<div align="center">

<sub>Made by <a href="https://uniqai.app/?utm_source=github&utm_medium=readme-ko&utm_campaign=token-diet">UniqAI</a> — Kling 3.0, Veo 3, Flux, Nano Banana, 그리고 GPT-5/Claude/Gemini/Grok을 앱 하나에. 이 토큰 요금은 우리도 직접 내고 있고, 우리 프롬프트도 이렇게 짧게 유지합니다.</sub>

</div>
