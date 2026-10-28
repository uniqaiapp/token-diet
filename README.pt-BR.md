<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/banner-light.svg">
  <img alt="token-diet: cut prompt and context tokens without losing meaning" src="assets/banner.svg" width="1280" height="320">
</picture>

<h1>token-diet: reduza o custo de tokens de LLM em agentes e aplicativos</h1>

[![License: MIT](https://img.shields.io/badge/license-MIT-d1fe17?style=flat-square&labelColor=0d0f12)](LICENSE)
[![Claude Code skill](https://img.shields.io/badge/Claude_Code-skill-d1fe17?style=flat-square&labelColor=0d0f12)](#instalação)
[![Cursor](https://img.shields.io/badge/Cursor-rules-d1fe17?style=flat-square&labelColor=0d0f12)](#instalação)
[![Codex](https://img.shields.io/badge/Codex-AGENTS.md-d1fe17?style=flat-square&labelColor=0d0f12)](#instalação)
[![Made by UniqAI](https://img.shields.io/badge/made_by-UniqAI-fdfc07?style=flat-square&labelColor=0d0f12)](https://uniqai.app/?utm_source=github&utm_medium=readme-pt-br&utm_campaign=token-diet)

**Prompts compactos em inglês a partir de qualquer idioma, código intacto, economia medida e não prometida.**

[Início rápido](#início-rápido) · [Como funciona](#como-funciona) · [Exemplos](#exemplos) · [Instalação](#instalação) · [Perguntas frequentes](#perguntas-frequentes)

</div>

[English](README.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · Português (BR) · [日本語](README.ja.md) · [한국어](README.ko.md)

Reduza o custo de tokens de LLM no Claude Code, Cursor, Codex e nos seus próprios aplicativos medindo primeiro. Prompts escritos em russo, espanhol, português ou alemão custam mais tokens do que a mesma instrução em inglês, e prompts escritos para uma janela de chat carregam cumprimentos, rodeios e repetições de que um agente não precisa. O `token-diet` passa esse prompt por um modelo barato à sua escolha, devolve um inglês compacto com cada bloco de código, caminho, identificador e string entre aspas intactos, diz ao agente para responder no seu idioma e depois conta os tokens antes e depois com o endpoint `count_tokens` da Anthropic (ou com uma estimativa claramente rotulada quando você não tem chave). Para sessões inteiras de agente, ele separa a entrada por origem, para você ver se o que precisa ser cortado é o system prompt, o histórico, a saída das ferramentas ou o contexto recuperado.

| **Proteger, depois reescrever** | **Resposta no seu idioma** | **Medir antes de afirmar** |
|:---|:---|:---|
| Blocos de código, código inline, caminhos, flags, identificadores e strings entre aspas viram placeholders; o modelo barato nunca os vê nem os edita, e um placeholder faltando faz a execução falhar. | Uma linha acrescentada, `Answer in Russian.`, mantém o agente respondendo do jeito que você escreveu, enquanto a tarefa em si viaja em inglês curto. | O `measure.py` imprime números exatos do `count_tokens` com uma chave e uma estimativa por caracteres sem ela, e diz na segunda linha qual dos dois usou. |

## Início rápido

```bash
git clone https://github.com/uniqaiapp/token-diet ~/.claude/skills/token-diet
cd ~/.claude/skills/token-diet
python3 scripts/diet.py examples/ru-01-bugfix/before.txt --dry-run      # no key, no network
python3 scripts/measure.py examples/ru-01-bugfix/before.txt examples/ru-01-bugfix/after.txt
```

O primeiro comando lista os oito trechos que ele protegeria em um relatório de bug em russo e a requisição exata que enviaria. O segundo imprime uma tabela antes/depois para a reescrita de referência; com `ANTHROPIC_API_KEY` definida no seu shell ele usa o `count_tokens`, senão imprime uma estimativa e avisa. Python 3.9+, nenhum pacote para instalar.

## Demonstração

<img alt="token-diet demo: a dry run listing protected placeholders, then a before/after token report" src="assets/demo.svg" width="820">

## Como funciona

1. **Proteger.** O `scripts/diet.py` varre o prompt com regras só ASCII (assim palavras em cirílico nunca são confundidas com identificadores) e substitui código em fences, código inline, URLs, caminhos, nomes de arquivo, flags, chamadas, identificadores com ponto, em snake_case ou camelCase e strings entre aspas por placeholders numerados `⟦0⟧ … ⟦n⟧`.
2. **Reescrever.** O texto protegido vai para o provedor que você escolher (`--provider openai|gemini|anthropic`, chave em `OPENAI_API_KEY`, `GEMINI_API_KEY` ou `ANTHROPIC_API_KEY`) com um system prompt fixo: inglês compacto, imperativo, todos os requisitos mantidos, sem responder, sem acrescentar nada. Os modelos padrão são a faixa barata de cada provedor; troque com `--model`.
3. **Verificar e restaurar.** Cada placeholder precisa voltar exatamente uma vez. Se não voltar, o script sai com código 3 e mostra a saída bruta em vez de entregar um prompt quebrado. Depois os placeholders são trocados de volta e `Answer in <language>.` é acrescentado (detectado automaticamente; `--answer-in` sobrescreve).
4. **Medir.** `scripts/measure.py BEFORE AFTER` conta os dois arquivos. Com `ANTHROPIC_API_KEY` definida, ele chama `POST /v1/messages/count_tokens` para o modelo que você indicar com `--model` (as contagens dependem do modelo). Sem chave, ele recorre ao `scripts/estimate.py`, uma heurística por caracteres cujas taxas presumidas ficam em um único dicionário no topo do arquivo, e rotula cada linha como estimativa.
5. **Decompor uma sessão.** `scripts/measure.py --breakdown transcript.json` divide a transcrição de um agente em system prompt, ferramentas, histórico, saída de ferramentas, contexto recuperado e turno atual, imprime a fatia de cada um e aponta a alavanca que se aplica: prefixo estável para cache, janela de histórico ou resultados de ferramentas compactos.

```
prompt.ru.txt ─protect─▶ ⟦placeholders⟧ ─cheap model─▶ compact EN ─verify+restore─▶ prompt.en.txt + "Answer in Russian."
                                                                                        │
                                                      measure.py before after ◀─────────┘
```

Nenhuma porcentagem aparece neste README, de propósito. Todo número que as ferramentas imprimem vem de um arquivo em `examples/` e está fixado pela suíte de testes; rode os comandos acima para vê-los, e rode com uma chave para obter contagens exatas para o seu próprio modelo.

## Exemplos

<details>
<summary><b>Relatório de bug em russo → instrução compacta em inglês (examples/ru-01-bugfix)</b></summary>

**Antes** (1596 caracteres; o arquivo completo é `examples/ru-01-bugfix/before.txt`)

```text
Привет! Слушай, у меня тут проблема с Next.js приложением, и я уже довольно долго пытаюсь её решить,
но что-то никак не получается, поэтому решил обратиться к тебе. В общем, суть в том, что когда
пользователь открывает страницу src/app/video/page.tsx и нажимает на кнопку "Сгенерировать", то иногда
(не всегда, а примерно в одном случае из пяти, как мне кажется) запрос к API уходит дважды …
```

**Depois** (`examples/ru-01-bugfix/after.txt`, uma reescrita de referência feita segundo as regras de `references/compaction-rules.md`)

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

`python3 scripts/measure.py examples/ru-01-bugfix/before.txt examples/ru-01-bugfix/after.txt --estimate` imprime o `report.txt` que está no repositório.

</details>

<details>
<summary><b>Para onde vão os tokens em uma sessão de agente (examples/transcript)</b></summary>

```bash
python3 scripts/measure.py --breakdown examples/transcript/transcript.sample.json
```

A amostra é uma sessão curta e sintética de depuração em Next.js: uma pergunta em russo, duas chamadas de ferramenta, uma execução do Vitest que falha. O relatório lista cada origem com a sua fatia e, como a saída do test runner domina, sugere truncar os resultados das ferramentas antes de entrarem no contexto. A saída que está no repositório é `examples/transcript/breakdown.txt`.

</details>

<details>
<summary><b>Instruções em espanhol, português e alemão</b></summary>

`examples/es-01-api`, `examples/pt-01-tests` e `examples/de-01-docs` seguem o mesmo layout: `before.txt`, um `after.txt` de referência, o `dry-run.txt` mostrando quais trechos foram protegidos e `report.txt`. O `examples/README.md` lista o que cada um exercita.

</details>

## Instalação

Funciona com qualquer agente que leia arquivos de instruções. Escolha o seu. Requisitos: Python 3.9+. Nenhum pacote para instalar.

<details open>
<summary><b>Claude Code</b></summary>

```bash
# user-level (every project)
git clone https://github.com/uniqaiapp/token-diet ~/.claude/skills/token-diet
# or project-level
git clone https://github.com/uniqaiapp/token-diet .claude/skills/token-diet
```

Depois digite `/token-diet` em uma sessão, ou simplesmente descreva a tarefa; a `description` da skill dispara com "reduce token costs", "compress this prompt", "сократи промпт", "экономия токенов". Como plugin, quando o marketplace da uniqaiapp for publicado: `/plugin marketplace add uniqaiapp/skills` e então `/plugin install token-diet@uniqaiapp`.

</details>

<details>
<summary><b>Cursor</b></summary>

Copie `SKILL.md`, `scripts/`, `references/` e [`.cursor/rules/token-diet.mdc`](.cursor/rules/token-diet.mdc) para o seu projeto. O arquivo de regra embute a skill com `@SKILL.md`.

</details>

<details>
<summary><b>Codex / qualquer agente com AGENTS.md</b></summary>

Copie `SKILL.md`, `scripts/` e `references/` para `.agents/skills/token-diet/` e adicione o trecho de [`codex/INSTRUCTIONS.md`](codex/INSTRUCTIONS.md) ao seu `AGENTS.md`. O próprio [`AGENTS.md`](AGENTS.md) deste repositório mostra o formato.

</details>

<details>
<summary><b>Sem agente</b></summary>

Todo script roda sozinho: `python3 scripts/diet.py --help`, `python3 scripts/measure.py --help`, `python3 scripts/estimate.py --help`. As regras de reescrita também estão escritas para humanos em [`references/compaction-rules.md`](references/compaction-rules.md).

</details>

## Limites e honestidade

- Comentários dentro de blocos de código ficam no idioma original; a etapa de proteção mantém o código byte a byte de propósito.
- A estimativa por caracteres é uma heurística. As suas cinco taxas presumidas ficam em `scripts/estimate.py`; mude-as e os relatórios fixados mudam junto, que é para isso que os testes existem. Não cite uma estimativa como se fosse uma medição.
- A etapa de verificação garante os placeholders, não as nuances. Um modelo barato pode deixar cair um qualificador; leia o resultado uma vez antes de reutilizá-lo como template.
- A detecção de idioma é baseada em alfabeto e stopwords (ru, uk, es, pt, de, fr, it). Os outros idiomas recebem uma linha genérica "answer in the language of the original request"; passe `--answer-in` para ser preciso.
- Os arquivos `after.txt` em `examples/` são reescritas de referência feitas pelos mantenedores, não saída de modelo. Eles mostram o alvo; a saída do seu modelo vai ser diferente.
- A reescrita vale a pena quando um prompt é reutilizado ou quando o modelo que o recebe é muito mais caro do que o que o reescreve. Para uma mensagem de chat de uma linha não vale, e o `diet.py` avisa quando o resultado fica mais longo do que a entrada.

## Perguntas frequentes

<details>
<summary><b>Funciona sem chave de API?</b></summary>

Em parte. `--dry-run` mostra o prompt protegido e a requisição exata sem enviar nada, o `measure.py` recorre a uma estimativa rotulada e o `references/compaction-rules.md` permite que um agente faça a reescrita à mão. Uma reescrita de verdade precisa de uma chave de um dos três provedores, lida do ambiente.

</details>

<details>
<summary><b>Por que mandar o prompt para outro modelo? O agente poderia simplesmente traduzir.</b></summary>

Poderia, ao preço por token do agente e dentro do contexto do agente. A ideia é fazer o corte uma vez em um modelo barato e depois reutilizar a versão compacta: no `CLAUDE.md` ou `AGENTS.md`, como template de tarefa salvo, como system prompt, como exemplos few-shot. Para uma única mensagem curta, pule essa etapa.

</details>

<details>
<summary><b>O agente ainda vai responder em russo?</b></summary>

Sim. A última linha do prompt reescrito diz `Answer in Russian.` (ou Spanish, Portuguese, German, …), e o `SKILL.md` instrui o agente a manter esse idioma durante a sessão. Os rótulos de botões e as strings entre aspas do seu prompt também ficam no idioma original, porque estão protegidos.

</details>

<details>
<summary><b>Qual modelo conta os tokens?</b></summary>

O que você indicar em `measure.py --model`; o padrão é `claude-opus-5-5`. As contagens dependem do tokenizador, então conte com o modelo que vai de fato receber o prompt. Não existe caminho de contagem para OpenAI ou Gemini aqui; para esses provedores você recebe a estimativa, rotulada como tal.

</details>

<details>
<summary><b>Meu prompt fica armazenado em algum lugar?</b></summary>

Só onde você o enviar. Os scripts escrevem no stdout ou no arquivo que você indicar em `--out` e não mantêm cache nem log. O que o provedor retém é regido pelos termos desse provedor.

</details>

## Projetos relacionados

- [skill-shrinker](https://github.com/uniqaiapp/skill-shrinker): encolhe qualquer SKILL.md ou arquivo de instruções de agente: mede o tamanho, move o material longo para referências e mantém os gatilhos intactos.
- [model-router](https://github.com/uniqaiapp/model-router): escolhe o modelo mais barato que dá conta da tarefa: uma tabela de regras e um script em stdlib que roteia tarefas por tipo, tamanho e risco.
- [deslop-ru](https://github.com/uniqaiapp/deslop-ru): tira o enchimento com cara de IA de textos em russo: uma skill mais um script em stdlib que sinaliza e reescreve os clichês de sempre.

## Como contribuir

Issues e pull requests são bem-vindos. Mantenha as mudanças pequenas e inclua um exemplo antes/depois na descrição do PR.
Veja [CONTRIBUTING.md](CONTRIBUTING.md) para as verificações locais (`python3 tests/run.py`, sem dependências).

## Licença

[MIT](LICENSE) © UniqAI

---

<div align="center">

<sub>Made by <a href="https://uniqai.app/?utm_source=github&utm_medium=readme-pt-br&utm_campaign=token-diet">UniqAI</a> — Kling 3.0, Veo 3, Flux, Nano Banana e GPT-5/Claude/Gemini/Grok em um só app. Nós mesmos pagamos essas contas de tokens; é assim que mantemos os nossos próprios prompts curtos.</sub>

</div>
