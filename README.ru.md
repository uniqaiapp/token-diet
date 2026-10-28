<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/banner-light.svg">
  <img alt="token-diet: экономия токенов без потери смысла" src="assets/banner.svg" width="1280" height="320">
</picture>

<h1>token-diet: экономия токенов для промптов на русском</h1>

[English version](README.md)

</div>

Промпт на русском обходится дороже, чем та же задача на английском: токенизаторы режут кириллицу на более мелкие куски, а к этому добавляются приветствия, оговорки и повторы, которые агенту не нужны. `token-diet` прогоняет промпт через дешёвую модель на ваш выбор, возвращает сжатый английский вариант, в котором код, пути, идентификаторы и строки в кавычках остались байт в байт, добавляет строку «Answer in Russian.», чтобы агент отвечал по-русски, и считает токены до и после. Без ключа скрипт честно печатает оценку по символам и подписывает её как оценку.

## Что делает

- `scripts/diet.py` защищает код, пути, флаги и идентификаторы плейсхолдерами, отправляет текст в OpenAI, Gemini или Anthropic (ключ только из переменной окружения) и проверяет, что каждый плейсхолдер вернулся ровно один раз.
- `scripts/measure.py` сравнивает исходник и результат: через `count_tokens` Anthropic, если задан `ANTHROPIC_API_KEY`, иначе через оценку по символам с пометкой.
- `scripts/measure.py --breakdown` раскладывает транскрипт агентской сессии по источникам (системный промпт, история, вывод инструментов, RAG) и говорит, что резать.

## Установка

**Claude Code**

```bash
git clone https://github.com/uniqaiapp/token-diet ~/.claude/skills/token-diet
```

Дальше `/token-diet` в сессии или просто просьба «сократи промпт», «экономия токенов»: скилл срабатывает по описанию.

**Cursor**

Скопируйте `SKILL.md`, `scripts/`, `references/` и `.cursor/rules/token-diet.mdc` в проект. Файл правила подключает скилл через `@SKILL.md`.

Нужен Python 3.9+, ничего устанавливать не надо.

## Пример

```bash
python3 scripts/diet.py examples/ru-01-bugfix/before.txt --dry-run
python3 scripts/measure.py examples/ru-01-bugfix/before.txt examples/ru-01-bugfix/after.txt
```

Первая команда показывает восемь защищённых фрагментов из русского баг-репорта (пути, блок кода, имя хука) и точный запрос, который был бы отправлен; в сеть ничего не уходит. Вторая печатает таблицу «до/после»: с ключом в окружении это точный подсчёт `count_tokens`, без ключа оценка, и метод написан во второй строке вывода. Процентов в этом README нет намеренно: цифры печатают скрипты на файлах из `examples/`, и тесты фиксируют их побайтно.

Полное описание, ограничения и FAQ: [README.md](README.md). Правила сжатия для ручного применения: [references/compaction-rules.md](references/compaction-rules.md).

## Лицензия

[MIT](LICENSE) © UniqAI

---

<div align="center">

<sub>Made by <a href="https://uniqai.app/?utm_source=github&utm_medium=readme-ru&utm_campaign=token-diet">UniqAI</a> — Kling 3.0, Veo 3, Flux, Nano Banana и GPT-5/Claude/Gemini/Grok в одном приложении.</sub>

</div>
