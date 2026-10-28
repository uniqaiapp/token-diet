<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/banner-light.svg">
  <img alt="token-diet: cut prompt and context tokens without losing meaning" src="assets/banner.svg" width="1280" height="320">
</picture>

<h1>token-diet: reduce el costo en tokens de los LLM en agentes y aplicaciones</h1>

[![License: MIT](https://img.shields.io/badge/license-MIT-d1fe17?style=flat-square&labelColor=0d0f12)](LICENSE)
[![Claude Code skill](https://img.shields.io/badge/Claude_Code-skill-d1fe17?style=flat-square&labelColor=0d0f12)](#instalación)
[![Cursor](https://img.shields.io/badge/Cursor-rules-d1fe17?style=flat-square&labelColor=0d0f12)](#instalación)
[![Codex](https://img.shields.io/badge/Codex-AGENTS.md-d1fe17?style=flat-square&labelColor=0d0f12)](#instalación)
[![Made by UniqAI](https://img.shields.io/badge/made_by-UniqAI-fdfc07?style=flat-square&labelColor=0d0f12)](https://uniqai.app/?utm_source=github&utm_medium=readme-es&utm_campaign=token-diet)

**Prompts compactos en inglés desde cualquier idioma, código intacto, ahorro medido y no prometido.**

[Inicio rápido](#inicio-rápido) · [Cómo funciona](#cómo-funciona) · [Ejemplos](#ejemplos) · [Instalación](#instalación) · [Preguntas frecuentes](#preguntas-frecuentes)

</div>

[English](README.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md) · Español · [Português (BR)](README.pt-BR.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

Reduce el costo en tokens de los LLM en Claude Code, Cursor, Codex y tus propias aplicaciones midiendo primero. Los prompts escritos en ruso, español, portugués o alemán cuestan más tokens que la misma instrucción en inglés, y los prompts escritos para una ventana de chat arrastran saludos, rodeos y repeticiones que un agente no necesita. `token-diet` pasa ese prompt por un modelo barato de tu elección, devuelve un inglés compacto con cada bloque de código, ruta, identificador y cadena entre comillas sin tocar, le indica al agente que responda en tu idioma y después cuenta los tokens antes y después con el endpoint `count_tokens` de Anthropic (o con una estimación claramente etiquetada cuando no tienes clave). Para sesiones de agente completas, desglosa la entrada por origen para que veas si lo que hay que recortar es el system prompt, el historial, la salida de las herramientas o el contexto recuperado.

| **Proteger, luego reescribir** | **Respuesta en tu idioma** | **Medir antes de afirmar** |
|:---|:---|:---|
| Bloques de código, código en línea, rutas, flags, identificadores y cadenas entre comillas se convierten en marcadores; el modelo barato nunca los ve ni los edita, y si falta un marcador la ejecución falla. | Una línea añadida, `Answer in Russian.`, hace que el agente te siga respondiendo tal como escribiste, mientras la tarea en sí viaja en inglés breve. | `measure.py` imprime cifras exactas de `count_tokens` con una clave y una estimación por caracteres sin ella, y en la segunda línea dice cuál de las dos usó. |

## Inicio rápido

```bash
git clone https://github.com/uniqaiapp/token-diet ~/.claude/skills/token-diet
cd ~/.claude/skills/token-diet
python3 scripts/diet.py examples/ru-01-bugfix/before.txt --dry-run      # no key, no network
python3 scripts/measure.py examples/ru-01-bugfix/before.txt examples/ru-01-bugfix/after.txt
```

El primer comando enumera los ocho fragmentos que protegería en un informe de error en ruso y la petición exacta que enviaría. El segundo imprime una tabla antes/después para la reescritura de referencia; con `ANTHROPIC_API_KEY` definida en tu shell usa `count_tokens`; si no, imprime una estimación y lo dice. Python 3.9+, sin paquetes que instalar.

## Demo

<img alt="token-diet demo: a dry run listing protected placeholders, then a before/after token report" src="assets/demo.svg" width="820">

## Cómo funciona

1. **Proteger.** `scripts/diet.py` recorre el prompt con reglas solo ASCII (así las palabras en cirílico nunca se confunden con identificadores) y sustituye el código entre fences, el código en línea, las URL, rutas, nombres de archivo, flags, llamadas, identificadores con puntos, en snake_case o camelCase y las cadenas entre comillas por marcadores numerados `⟦0⟧ … ⟦n⟧`.
2. **Reescribir.** El texto protegido va al proveedor que elijas (`--provider openai|gemini|anthropic`, clave desde `OPENAI_API_KEY`, `GEMINI_API_KEY` o `ANTHROPIC_API_KEY`) con un system prompt fijo: inglés compacto, imperativo, todos los requisitos conservados, sin responder, sin añadir nada. Los modelos por defecto son el nivel barato de cada proveedor; se cambian con `--model`.
3. **Verificar y restaurar.** Cada marcador debe volver exactamente una vez. Si no, el script sale con código 3 y muestra la salida sin procesar en lugar de entregar un prompt roto. Después los marcadores se sustituyen por su contenido original y se añade `Answer in <language>.` (detectado automáticamente; `--answer-in` lo sobrescribe).
4. **Medir.** `scripts/measure.py BEFORE AFTER` cuenta ambos archivos. Con `ANTHROPIC_API_KEY` definida llama a `POST /v1/messages/count_tokens` para el modelo que indiques con `--model` (los recuentos dependen del modelo). Sin clave recurre a `scripts/estimate.py`, una heurística por caracteres cuyas tasas supuestas están en un único diccionario al principio del archivo, y etiqueta cada línea como estimación.
5. **Desglosar una sesión.** `scripts/measure.py --breakdown transcript.json` divide la transcripción de un agente en system prompt, herramientas, historial, salida de herramientas, contexto recuperado y turno actual, imprime la proporción de cada uno y nombra la palanca que aplica: prefijo estable para caché, ventana de historial o resultados de herramientas compactos.

```
prompt.ru.txt ─protect─▶ ⟦placeholders⟧ ─cheap model─▶ compact EN ─verify+restore─▶ prompt.en.txt + "Answer in Russian."
                                                                                        │
                                                      measure.py before after ◀─────────┘
```

En este README no aparece ningún porcentaje, a propósito. Cada número que imprimen las herramientas sale de un archivo de `examples/` y está fijado por la suite de pruebas; ejecuta los comandos de arriba para verlos, y ejecútalos con una clave para obtener recuentos exactos para tu propio modelo.

## Ejemplos

<details>
<summary><b>Informe de error en ruso → instrucción compacta en inglés (examples/ru-01-bugfix)</b></summary>

**Antes** (1596 caracteres; el archivo completo es `examples/ru-01-bugfix/before.txt`)

```text
Привет! Слушай, у меня тут проблема с Next.js приложением, и я уже довольно долго пытаюсь её решить,
но что-то никак не получается, поэтому решил обратиться к тебе. В общем, суть в том, что когда
пользователь открывает страницу src/app/video/page.tsx и нажимает на кнопку "Сгенерировать", то иногда
(не всегда, а примерно в одном случае из пяти, как мне кажется) запрос к API уходит дважды …
```

**Después** (`examples/ru-01-bugfix/after.txt`, una reescritura de referencia hecha según las reglas de `references/compaction-rules.md`)

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

`python3 scripts/measure.py examples/ru-01-bugfix/before.txt examples/ru-01-bugfix/after.txt --estimate` imprime el `report.txt` incluido en el repositorio.

</details>

<details>
<summary><b>A dónde van los tokens en una sesión de agente (examples/transcript)</b></summary>

```bash
python3 scripts/measure.py --breakdown examples/transcript/transcript.sample.json
```

La muestra es una sesión corta y sintética de depuración de Next.js: una pregunta en ruso, dos llamadas a herramientas, una ejecución fallida de Vitest. El informe lista cada origen con su proporción y, como la salida del ejecutor de pruebas domina, sugiere truncar los resultados de las herramientas antes de que entren en el contexto. La salida incluida en el repositorio es `examples/transcript/breakdown.txt`.

</details>

<details>
<summary><b>Instrucciones en español, portugués y alemán</b></summary>

`examples/es-01-api`, `examples/pt-01-tests` y `examples/de-01-docs` siguen la misma estructura: `before.txt`, un `after.txt` de referencia, el `dry-run.txt` que muestra qué fragmentos se protegieron y `report.txt`. `examples/README.md` indica qué ejercita cada uno.

</details>

## Instalación

Funciona con cualquier agente que lea archivos de instrucciones. Elige el tuyo. Requisitos: Python 3.9+. No hay paquetes que instalar.

<details open>
<summary><b>Claude Code</b></summary>

```bash
# user-level (every project)
git clone https://github.com/uniqaiapp/token-diet ~/.claude/skills/token-diet
# or project-level
git clone https://github.com/uniqaiapp/token-diet .claude/skills/token-diet
```

Después escribe `/token-diet` en una sesión, o simplemente describe la tarea; la `description` de la skill se activa con "reduce token costs", "compress this prompt", "сократи промпт", "экономия токенов". Como plugin, cuando se publique el marketplace de uniqaiapp: `/plugin marketplace add uniqaiapp/skills` y luego `/plugin install token-diet@uniqaiapp`.

</details>

<details>
<summary><b>Cursor</b></summary>

Copia `SKILL.md`, `scripts/`, `references/` y [`.cursor/rules/token-diet.mdc`](.cursor/rules/token-diet.mdc) en tu proyecto. El archivo de reglas incrusta la skill con `@SKILL.md`.

</details>

<details>
<summary><b>Codex / cualquier agente con AGENTS.md</b></summary>

Copia `SKILL.md`, `scripts/` y `references/` en `.agents/skills/token-diet/` y añade el fragmento de [`codex/INSTRUCTIONS.md`](codex/INSTRUCTIONS.md) a tu `AGENTS.md`. El propio [`AGENTS.md`](AGENTS.md) de este repositorio muestra la forma.

</details>

<details>
<summary><b>Sin agente</b></summary>

Cada script funciona por sí solo: `python3 scripts/diet.py --help`, `python3 scripts/measure.py --help`, `python3 scripts/estimate.py --help`. Las reglas de reescritura también están redactadas para humanos en [`references/compaction-rules.md`](references/compaction-rules.md).

</details>

## Límites y honestidad

- Los comentarios dentro de los bloques de código se quedan en el idioma original; el paso de protección mantiene el código byte a byte a propósito.
- La estimación por caracteres es una heurística. Sus cinco tasas supuestas están en `scripts/estimate.py`; si las cambias, cambian los informes fijados, que es para lo que están las pruebas. No cites una estimación como si fuera una medición.
- El paso de verificación garantiza los marcadores, no los matices. Un modelo barato puede dejar caer un calificativo; lee el resultado una vez antes de reutilizarlo como plantilla.
- La detección de idioma se basa en el alfabeto y en palabras vacías (ru, uk, es, pt, de, fr, it). Los demás idiomas reciben una línea genérica "answer in the language of the original request"; pasa `--answer-in` para ser preciso.
- Los archivos `after.txt` de `examples/` son reescrituras de referencia hechas por los mantenedores, no salida de un modelo. Muestran el objetivo; la salida de tu modelo será distinta.
- La reescritura compensa cuando un prompt se reutiliza o cuando el modelo que lo recibe es mucho más caro que el que lo reescribe. Para un mensaje de chat de una línea no compensa, y `diet.py` avisa cuando el resultado es más largo que la entrada.

## Preguntas frecuentes

<details>
<summary><b>¿Funciona sin clave de API?</b></summary>

En parte. `--dry-run` muestra el prompt protegido y la petición exacta sin enviar nada, `measure.py` recurre a una estimación etiquetada y `references/compaction-rules.md` permite que un agente haga la reescritura a mano. Una reescritura real necesita una clave de uno de los tres proveedores, leída del entorno.

</details>

<details>
<summary><b>¿Por qué enviar el prompt a otro modelo? El agente podría traducirlo él mismo.</b></summary>

Podría, al precio por token del agente y dentro del contexto del agente. La idea es hacer el recorte una sola vez en un modelo barato y después reutilizar la versión compacta: en `CLAUDE.md` o `AGENTS.md`, como plantilla de tarea guardada, como system prompt, como ejemplos few-shot. Para un único mensaje corto, sáltatelo.

</details>

<details>
<summary><b>¿El agente seguirá respondiendo en ruso?</b></summary>

Sí. La última línea del prompt reescrito dice `Answer in Russian.` (o Spanish, Portuguese, German, …), y `SKILL.md` le indica al agente que mantenga ese idioma durante la sesión. Las etiquetas de botones y las cadenas entre comillas de tu prompt también se quedan en el idioma original, porque están protegidas.

</details>

<details>
<summary><b>¿Qué modelo cuenta los tokens?</b></summary>

El que indiques con `measure.py --model`; por defecto es `claude-opus-5-5`. Los recuentos dependen del tokenizador, así que cuenta con el modelo que realmente recibirá el prompt. Aquí no hay ruta de recuento para OpenAI ni Gemini; para esos proveedores obtienes la estimación, etiquetada como tal.

</details>

<details>
<summary><b>¿Mi prompt se guarda en algún sitio?</b></summary>

Solo donde tú lo envíes. Los scripts escriben en stdout o en el archivo que indiques con `--out` y no guardan caché ni registro. Lo que conserve el proveedor se rige por los términos de ese proveedor.

</details>

## Proyectos relacionados

- [skill-shrinker](https://github.com/uniqaiapp/skill-shrinker): comprime cualquier SKILL.md o archivo de instrucciones de agente: mide el tamaño, mueve el material largo a referencias y mantiene intactos los disparadores.
- [model-router](https://github.com/uniqaiapp/model-router): elige el modelo más barato capaz de hacer el trabajo: una tabla de reglas y un script en stdlib que enruta tareas por tipo, longitud y riesgo.
- [deslop-ru](https://github.com/uniqaiapp/deslop-ru): elimina el relleno con sabor a IA de textos en ruso: una skill más un script en stdlib que marca y reescribe los clichés habituales.

## Contribuir

Los issues y pull requests son bienvenidos. Mantén los cambios pequeños e incluye un ejemplo antes/después en la descripción del PR.
Consulta [CONTRIBUTING.md](CONTRIBUTING.md) para las comprobaciones locales (`python3 tests/run.py`, sin dependencias).

## Licencia

[MIT](LICENSE) © UniqAI

---

<div align="center">

<sub>Made by <a href="https://uniqai.app/?utm_source=github&utm_medium=readme-es&utm_campaign=token-diet">UniqAI</a> — Kling 3.0, Veo 3, Flux, Nano Banana y GPT-5/Claude/Gemini/Grok en una sola app. Nosotros pagamos estas facturas de tokens; así es como mantenemos cortos nuestros propios prompts.</sub>

</div>
