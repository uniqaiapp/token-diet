<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/banner-light.svg">
  <img alt="token-diet: cut prompt and context tokens without losing meaning" src="assets/banner.svg" width="1280" height="320">
</picture>

<h1>token-diet: экономия токенов LLM в агентах и приложениях</h1>

[![License: MIT](https://img.shields.io/badge/license-MIT-d1fe17?style=flat-square&labelColor=0d0f12)](LICENSE)
[![Claude Code skill](https://img.shields.io/badge/Claude_Code-skill-d1fe17?style=flat-square&labelColor=0d0f12)](#установка)
[![Cursor](https://img.shields.io/badge/Cursor-rules-d1fe17?style=flat-square&labelColor=0d0f12)](#установка)
[![Codex](https://img.shields.io/badge/Codex-AGENTS.md-d1fe17?style=flat-square&labelColor=0d0f12)](#установка)
[![Made by UniqAI](https://img.shields.io/badge/made_by-UniqAI-fdfc07?style=flat-square&labelColor=0d0f12)](https://uniqai.app/?utm_source=github&utm_medium=readme-ru&utm_campaign=token-diet)

**Компактные английские промпты из любого языка, код без изменений, экономия измерена, а не обещана.**

[Быстрый старт](#быстрый-старт) · [Как работает](#как-работает) · [Примеры](#примеры) · [Установка](#установка) · [FAQ](#faq)

</div>

[English](README.md) · Русский · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Português (BR)](README.pt-BR.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

Снижайте расход токенов LLM в Claude Code, Cursor, Codex и собственных приложениях, начиная с измерения. Промпт на русском, испанском, португальском или немецком стоит больше токенов, чем та же задача на английском, а промпт, написанный для окна чата, тащит за собой приветствия, оговорки и повторы, которые агенту не нужны. `token-diet` прогоняет такой промпт через дешёвую модель на ваш выбор, возвращает сжатый английский, в котором каждый блок кода, путь, идентификатор и строка в кавычках остались нетронутыми, велит агенту отвечать на вашем языке, а затем считает токены до и после через эндпоинт `count_tokens` Anthropic (или даёт оценку с явной пометкой, если ключа нет). Для целых агентских сессий он раскладывает входные токены по источникам, и видно, что именно резать: системный промпт, историю, вывод инструментов или извлечённый контекст.

| **Сначала защитить, потом переписать** | **Ответ на вашем языке** | **Измерить, прежде чем заявлять** |
|:---|:---|:---|
| Блоки кода, inline-код, пути, флаги, идентификаторы и строки в кавычках становятся плейсхолдерами; дешёвая модель их не видит и не правит, а пропавший плейсхолдер роняет запуск. | Одна добавленная строка, `Answer in Russian.`, заставляет агента отвечать вам так, как вы писали, при этом сама задача едет коротким английским. | `measure.py` печатает точные цифры `count_tokens`, если есть ключ, и оценку по символам, если нет, а во второй строке говорит, что именно использовал. |

## Быстрый старт

```bash
git clone https://github.com/uniqaiapp/token-diet ~/.claude/skills/token-diet
cd ~/.claude/skills/token-diet
python3 scripts/diet.py examples/ru-01-bugfix/before.txt --dry-run      # no key, no network
python3 scripts/measure.py examples/ru-01-bugfix/before.txt examples/ru-01-bugfix/after.txt
```

Первая команда перечисляет восемь фрагментов, которые она защитила бы в русском баг-репорте, и точный запрос, который был бы отправлен. Вторая печатает таблицу до/после для эталонного переписывания; если в окружении задан `ANTHROPIC_API_KEY`, используется `count_tokens`, иначе печатается оценка с пометкой. Python 3.9+, ничего ставить не нужно.

## Демо

<img alt="token-diet demo: a dry run listing protected placeholders, then a before/after token report" src="assets/demo.svg" width="820">

## Как работает

1. **Защита.** `scripts/diet.py` сканирует промпт правилами только для ASCII (поэтому кириллические слова никогда не принимаются за идентификаторы) и заменяет блоки кода, inline-код, URL, пути, имена файлов, флаги, вызовы, идентификаторы с точками, snake_case и camelCase, а также строки в кавычках нумерованными плейсхолдерами `⟦0⟧ … ⟦n⟧`.
2. **Переписывание.** Защищённый текст уходит выбранному провайдеру (`--provider openai|gemini|anthropic`, ключ из `OPENAI_API_KEY`, `GEMINI_API_KEY` или `ANTHROPIC_API_KEY`) с фиксированным системным промптом: компактный английский, повелительное наклонение, все требования сохранены, не отвечать, ничего не добавлять. Модели по умолчанию — дешёвый тариф каждого провайдера; переопределяется через `--model`.
3. **Проверка и восстановление.** Каждый плейсхолдер должен вернуться ровно один раз. Если нет, скрипт завершается с кодом 3 и показывает сырой вывод вместо того, чтобы отдать сломанный промпт. Затем плейсхолдеры подставляются обратно и добавляется `Answer in <language>.` (язык определяется автоматически; `--answer-in` переопределяет).
4. **Измерение.** `scripts/measure.py BEFORE AFTER` считает оба файла. С заданным `ANTHROPIC_API_KEY` он вызывает `POST /v1/messages/count_tokens` для модели из `--model` (счёт зависит от модели). Без ключа откатывается на `scripts/estimate.py`, эвристику по символам, чьи предполагаемые коэффициенты лежат в одном словаре в начале файла, и помечает каждую строку как оценку.
5. **Разбор сессии.** `scripts/measure.py --breakdown transcript.json` делит транскрипт агента на системный промпт, инструменты, историю, вывод инструментов, извлечённый контекст и текущий ход, печатает долю каждого и называет подходящий рычаг: стабильный префикс для кеширования, окно истории или компактные результаты инструментов.

```
prompt.ru.txt ─protect─▶ ⟦placeholders⟧ ─cheap model─▶ compact EN ─verify+restore─▶ prompt.en.txt + "Answer in Russian."
                                                                                        │
                                                      measure.py before after ◀─────────┘
```

В этом README намеренно нет ни одного процента. Каждое число, которое печатают инструменты, берётся из файла в `examples/` и зафиксировано тестами; запустите команды выше, чтобы их увидеть, и запустите с ключом, чтобы получить точный счёт для своей модели.

## Примеры

<details>
<summary><b>Русский баг-репорт → компактный английский бриф (examples/ru-01-bugfix)</b></summary>

**До** (1596 символов; полный файл — `examples/ru-01-bugfix/before.txt`)

```text
Привет! Слушай, у меня тут проблема с Next.js приложением, и я уже довольно долго пытаюсь её решить,
но что-то никак не получается, поэтому решил обратиться к тебе. В общем, суть в том, что когда
пользователь открывает страницу src/app/video/page.tsx и нажимает на кнопку "Сгенерировать", то иногда
(не всегда, а примерно в одном случае из пяти, как мне кажется) запрос к API уходит дважды …
```

**После** (`examples/ru-01-bugfix/after.txt`, эталонное переписывание по правилам из `references/compaction-rules.md`)

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

`python3 scripts/measure.py examples/ru-01-bugfix/before.txt examples/ru-01-bugfix/after.txt --estimate` печатает закоммиченный `report.txt`.

</details>

<details>
<summary><b>Куда уходят токены в агентской сессии (examples/transcript)</b></summary>

```bash
python3 scripts/measure.py --breakdown examples/transcript/transcript.sample.json
```

Пример — короткая синтетическая сессия отладки Next.js: один вопрос на русском, два вызова инструментов, упавший прогон Vitest. Отчёт перечисляет каждый источник с его долей и, поскольку доминирует вывод тест-раннера, предлагает обрезать результаты инструментов до того, как они попадут в контекст. Закоммиченный вывод — `examples/transcript/breakdown.txt`.

</details>

<details>
<summary><b>Брифы на испанском, португальском и немецком</b></summary>

`examples/es-01-api`, `examples/pt-01-tests` и `examples/de-01-docs` устроены так же: `before.txt`, эталонный `after.txt`, `dry-run.txt` с защищёнными фрагментами и `report.txt`. Что проверяет каждый из них, перечислено в `examples/README.md`.

</details>

## Установка

Работает с любым агентом, который читает файлы инструкций. Выберите свой. Требования: Python 3.9+, ничего ставить не нужно.

<details open>
<summary><b>Claude Code</b></summary>

```bash
# user-level (every project)
git clone https://github.com/uniqaiapp/token-diet ~/.claude/skills/token-diet
# or project-level
git clone https://github.com/uniqaiapp/token-diet .claude/skills/token-diet
```

Дальше `/token-diet` в сессии или просто опишите задачу; `description` скилла срабатывает на «reduce token costs», «compress this prompt», «сократи промпт», «экономия токенов». Как плагин, когда будет опубликован маркетплейс uniqaiapp: `/plugin marketplace add uniqaiapp/skills`, затем `/plugin install token-diet@uniqaiapp`.

</details>

<details>
<summary><b>Cursor</b></summary>

Скопируйте `SKILL.md`, `scripts/`, `references/` и [`.cursor/rules/token-diet.mdc`](.cursor/rules/token-diet.mdc) в проект. Файл правила подключает скилл через `@SKILL.md`.

</details>

<details>
<summary><b>Codex и любой агент с AGENTS.md</b></summary>

Скопируйте `SKILL.md`, `scripts/` и `references/` в `.agents/skills/token-diet/` и добавьте блок из [`codex/INSTRUCTIONS.md`](codex/INSTRUCTIONS.md) в свой `AGENTS.md`. Собственный [`AGENTS.md`](AGENTS.md) этого репозитория показывает, как это выглядит.

</details>

<details>
<summary><b>Без агента</b></summary>

Каждый скрипт работает сам по себе: `python3 scripts/diet.py --help`, `python3 scripts/measure.py --help`, `python3 scripts/estimate.py --help`. Правила переписывания изложены и для людей в [`references/compaction-rules.md`](references/compaction-rules.md).

</details>

## Ограничения и честность

- Комментарии внутри блоков кода остаются на исходном языке; этап защиты намеренно сохраняет код байт в байт.
- Оценка по символам — эвристика. Пять её коэффициентов лежат в `scripts/estimate.py`; поменяете их — изменятся и зафиксированные отчёты, для этого тесты и нужны. Не выдавайте оценку за измерение.
- Этап проверки гарантирует плейсхолдеры, а не нюансы. Дешёвая модель может потерять уточнение; прочитайте результат один раз, прежде чем использовать его как шаблон.
- Определение языка основано на письменности и стоп-словах (ru, uk, es, pt, de, fr, it). Для других языков добавляется общая строка «answer in the language of the original request»; чтобы было точно, передайте `--answer-in`.
- Файлы `after.txt` в `examples/` — эталонные переписывания от мейнтейнеров, а не вывод модели. Они показывают цель; вывод вашей модели будет отличаться.
- Переписывание окупается, когда промпт используется многократно или когда принимающая модель сильно дороже переписывающей. Для сообщения в одну строку — нет, и `diet.py` предупреждает, если результат длиннее исходника.

## FAQ

<details>
<summary><b>Работает без API-ключа?</b></summary>

Частично. `--dry-run` показывает защищённый промпт и точный запрос, ничего не отправляя, `measure.py` откатывается на оценку с пометкой, а по `references/compaction-rules.md` агент может переписать вручную. Для настоящего переписывания нужен один ключ одного из трёх провайдеров, читается из окружения.

</details>

<details>
<summary><b>Зачем вообще отправлять промпт другой модели? Агент мог бы перевести сам.</b></summary>

Мог бы — по цене агента за токен и внутри контекста агента. Смысл в том, чтобы один раз ужать промпт на дешёвой модели, а потом переиспользовать компактную версию: в `CLAUDE.md` или `AGENTS.md`, как сохранённый шаблон задачи, как системный промпт, как few-shot примеры. Для одного короткого сообщения пропустите этот шаг.

</details>

<details>
<summary><b>Агент всё ещё ответит по-русски?</b></summary>

Да. Последняя строка переписанного промпта — `Answer in Russian.` (или Spanish, Portuguese, German, …), а `SKILL.md` велит агенту держать этот язык всю сессию. Подписи кнопок и строки в кавычках из вашего промпта тоже остаются на исходном языке, потому что защищены.

</details>

<details>
<summary><b>Какая модель считает токены?</b></summary>

Та, что указана в `measure.py --model`; по умолчанию `claude-opus-5-5`. Счёт зависит от токенизатора, поэтому считайте той моделью, которая реально получит промпт. Пути подсчёта для OpenAI или Gemini здесь нет; для этих провайдеров вы получите оценку с соответствующей пометкой.

</details>

<details>
<summary><b>Мой промпт где-то сохраняется?</b></summary>

Только там, куда вы его отправили. Скрипты пишут в stdout или в файл из `--out` и не ведут ни кеша, ни лога. Что хранит провайдер, определяется условиями этого провайдера.

</details>

## Похожие репозитории

- [skill-shrinker](https://github.com/uniqaiapp/skill-shrinker): ужать любой SKILL.md или файл инструкций для агента: измеряет размер, уносит длинное в references, сохраняет триггеры.
- [model-router](https://github.com/uniqaiapp/model-router): выбрать самую дешёвую модель, которая справится: таблица правил и stdlib-скрипт, который распределяет задачи по типу, длине и риску.
- [deslop-ru](https://github.com/uniqaiapp/deslop-ru): убрать из русского текста наполнитель, звучащий как ИИ: скилл плюс stdlib-скрипт, который находит и переписывает типичные штампы.

## Участие

Issue и pull request приветствуются. Делайте изменения небольшими и добавляйте в описание PR пример до/после.
Локальные проверки (`python3 tests/run.py`, без зависимостей): [CONTRIBUTING.md](CONTRIBUTING.md).

## Лицензия

[MIT](LICENSE) © UniqAI

---

<div align="center">

<sub>Made by <a href="https://uniqai.app/?utm_source=github&utm_medium=readme-ru&utm_campaign=token-diet">UniqAI</a> — Kling 3.0, Veo 3, Flux, Nano Banana и GPT-5/Claude/Gemini/Grok в одном приложении. Мы сами платим по этим счетам за токены; так мы держим короткими собственные промпты.</sub>

</div>
