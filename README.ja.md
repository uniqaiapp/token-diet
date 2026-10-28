<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/banner-light.svg">
  <img alt="token-diet: cut prompt and context tokens without losing meaning" src="assets/banner.svg" width="1280" height="320">
</picture>

<h1>token-diet: エージェントとアプリの LLM トークンコストを削減</h1>

[![License: MIT](https://img.shields.io/badge/license-MIT-d1fe17?style=flat-square&labelColor=0d0f12)](LICENSE)
[![Claude Code skill](https://img.shields.io/badge/Claude_Code-skill-d1fe17?style=flat-square&labelColor=0d0f12)](#インストール)
[![Cursor](https://img.shields.io/badge/Cursor-rules-d1fe17?style=flat-square&labelColor=0d0f12)](#インストール)
[![Codex](https://img.shields.io/badge/Codex-AGENTS.md-d1fe17?style=flat-square&labelColor=0d0f12)](#インストール)
[![Made by UniqAI](https://img.shields.io/badge/made_by-UniqAI-fdfc07?style=flat-square&labelColor=0d0f12)](https://uniqai.app/?utm_source=github&utm_medium=readme-ja&utm_campaign=token-diet)

**どの言語のプロンプトも簡潔な英語に。コードはそのまま、削減量は約束ではなく実測で。**

[クイックスタート](#クイックスタート) · [仕組み](#仕組み) · [使用例](#使用例) · [インストール](#インストール) · [よくある質問](#よくある質問)

</div>

[English](README.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Português (BR)](README.pt-BR.md) · 日本語 · [한국어](README.ko.md)

まず測ることから始めて、Claude Code、Cursor、Codex、そして自作アプリの LLM トークンコストを削減します。ロシア語、スペイン語、ポルトガル語、ドイツ語で書いたプロンプトは、同じ内容を英語で書いた場合よりトークンを多く消費します。また、チャット画面向けに書いたプロンプトには、挨拶や遠回しな言い方、繰り返しといった、エージェントには不要なものが混じっています。`token-diet` はそうしたプロンプトを任意の安価なモデルに通し、コードブロック、パス、識別子、引用符内の文字列をすべてそのまま残した簡潔な英語を受け取り、エージェントにはあなたの言語で答えるよう指示し、その上で Anthropic の `count_tokens` エンドポイントで前後のトークン数を数えます（キーがない場合は、見積もりであると明記した値を出します）。エージェントのセッション全体に対しては入力を出どころ別に分解するので、削るべきなのがシステムプロンプトなのか、履歴なのか、ツール出力なのか、取得したコンテキストなのかが分かります。

| **まず保護、それから書き換え** | **あなたの言語で回答** | **主張する前に測る** |
|:---|:---|:---|
| コードフェンス、インラインコード、パス、フラグ、識別子、引用符内の文字列はプレースホルダーになります。安価なモデルはそれらを見ることも編集することもなく、プレースホルダーが一つでも欠ければ実行は失敗します。 | 末尾に追加される一行 `Answer in Russian.` によって、タスク本体は短い英語で送られつつ、エージェントはあなたが書いた言語で返答し続けます。 | `measure.py` はキーがあれば `count_tokens` の正確な値を、なければ文字数ベースの見積もりを出力し、どちらを使ったかを 2 行目に明記します。 |

## クイックスタート

```bash
git clone https://github.com/uniqaiapp/token-diet ~/.claude/skills/token-diet
cd ~/.claude/skills/token-diet
python3 scripts/diet.py examples/ru-01-bugfix/before.txt --dry-run      # no key, no network
python3 scripts/measure.py examples/ru-01-bugfix/before.txt examples/ru-01-bugfix/after.txt
```

1 つ目のコマンドは、ロシア語のバグ報告の中で保護対象になる 8 つのスパンと、実際に送信されるリクエストをそのまま表示します。2 つ目は参照用の書き換えに対する before/after の表を出力します。シェルで `ANTHROPIC_API_KEY` が設定されていれば `count_tokens` を使い、なければ見積もりを出してその旨を表示します。Python 3.9+、インストールするパッケージはありません。

## デモ

<img alt="token-diet demo: a dry run listing protected placeholders, then a before/after token report" src="assets/demo.svg" width="820">

## 仕組み

1. **保護。** `scripts/diet.py` は ASCII のみのルールでプロンプトを走査し（そのためキリル文字の単語が識別子と誤認されることはありません）、フェンスで囲まれたコード、インラインコード、URL、パス、ファイル名、フラグ、関数呼び出し、ドット区切り・snake_case・camelCase の識別子、引用符内の文字列を、番号付きプレースホルダー `⟦0⟧ … ⟦n⟧` に置き換えます。
2. **書き換え。** 保護済みのテキストは、選んだプロバイダー（`--provider openai|gemini|anthropic`、キーは `OPENAI_API_KEY`、`GEMINI_API_KEY`、`ANTHROPIC_API_KEY` から取得）に固定のシステムプロンプト付きで送られます。内容は、簡潔な英語、命令形、すべての要件を維持、回答しない、追加しない、です。デフォルトのモデルは各プロバイダーの安価なティアで、`--model` で上書きできます。
3. **検証と復元。** すべてのプレースホルダーがちょうど一度ずつ戻ってこなければなりません。そうでなければスクリプトは終了コード 3 で止まり、壊れたプロンプトを渡す代わりに生の出力を表示します。その後プレースホルダーを元に戻し、`Answer in <language>.` を末尾に追加します（言語は自動判定、`--answer-in` で上書き可能）。
4. **測定。** `scripts/measure.py BEFORE AFTER` は両方のファイルを数えます。`ANTHROPIC_API_KEY` が設定されていれば、`--model` で指定したモデルに対して `POST /v1/messages/count_tokens` を呼びます（カウントはモデルごとに異なります）。キーがなければ `scripts/estimate.py` にフォールバックします。これは文字数ベースのヒューリスティックで、仮定しているレートはファイル冒頭の一つの辞書にまとまっており、すべての行に見積もりであるとラベルを付けます。
5. **セッションの分解。** `scripts/measure.py --breakdown transcript.json` はエージェントのトランスクリプトを、システムプロンプト、ツール、履歴、ツール出力、取得コンテキスト、現在のターンに分割し、それぞれの割合を表示して、有効な手段を示します。キャッシュのための安定したプレフィックス、履歴のウィンドウ化、ツール結果の圧縮のいずれかです。

```
prompt.ru.txt ─protect─▶ ⟦placeholders⟧ ─cheap model─▶ compact EN ─verify+restore─▶ prompt.en.txt + "Answer in Russian."
                                                                                        │
                                                      measure.py before after ◀─────────┘
```

この README には意図的にパーセンテージを一つも載せていません。ツールが出力する数値はすべて `examples/` 内のファイルから得られ、テストスイートで固定されています。上のコマンドを実行すれば確認でき、キー付きで実行すれば自分のモデルでの正確なカウントが得られます。

## 使用例

<details>
<summary><b>ロシア語のバグ報告 → 簡潔な英語のブリーフ（examples/ru-01-bugfix）</b></summary>

**Before**（1596 文字。完全なファイルは `examples/ru-01-bugfix/before.txt`）

```text
Привет! Слушай, у меня тут проблема с Next.js приложением, и я уже довольно долго пытаюсь её решить,
но что-то никак не получается, поэтому решил обратиться к тебе. В общем, суть в том, что когда
пользователь открывает страницу src/app/video/page.tsx и нажимает на кнопку "Сгенерировать", то иногда
(не всегда, а примерно в одном случае из пяти, как мне кажется) запрос к API уходит дважды …
```

**After**（`examples/ru-01-bugfix/after.txt`、`references/compaction-rules.md` のルールに沿って書いた参照用の書き換え）

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

`python3 scripts/measure.py examples/ru-01-bugfix/before.txt examples/ru-01-bugfix/after.txt --estimate` を実行すると、コミット済みの `report.txt` と同じ内容が出力されます。

</details>

<details>
<summary><b>エージェントのセッションでトークンはどこに消えるか（examples/transcript）</b></summary>

```bash
python3 scripts/measure.py --breakdown examples/transcript/transcript.sample.json
```

サンプルは短い合成の Next.js デバッグセッションです。ロシア語の質問が 1 つ、ツール呼び出しが 2 回、失敗する Vitest の実行が 1 回。レポートは各出どころとその割合を列挙し、テストランナーの出力が大半を占めているため、ツール結果をコンテキストに入れる前に切り詰めることを提案します。コミット済みの出力は `examples/transcript/breakdown.txt` です。

</details>

<details>
<summary><b>スペイン語、ポルトガル語、ドイツ語のブリーフ</b></summary>

`examples/es-01-api`、`examples/pt-01-tests`、`examples/de-01-docs` も同じ構成です。`before.txt`、参照用の `after.txt`、どのスパンが保護されたかを示す `dry-run.txt`、そして `report.txt`。それぞれが何を検証しているかは `examples/README.md` にまとめてあります。

</details>

## インストール

指示ファイルを読むエージェントならどれでも使えます。お使いのものを選んでください。要件: Python 3.9+。インストールするパッケージはありません。

<details open>
<summary><b>Claude Code</b></summary>

```bash
# user-level (every project)
git clone https://github.com/uniqaiapp/token-diet ~/.claude/skills/token-diet
# or project-level
git clone https://github.com/uniqaiapp/token-diet .claude/skills/token-diet
```

あとはセッションで `/token-diet` と入力するか、タスクを説明するだけです。スキルの `description` は "reduce token costs"、"compress this prompt"、"сократи промпт"、"экономия токенов" でトリガーされます。プラグインとして使う場合は、uniqaiapp マーケットプレイス公開後に `/plugin marketplace add uniqaiapp/skills` に続けて `/plugin install token-diet@uniqaiapp` を実行してください。

</details>

<details>
<summary><b>Cursor</b></summary>

`SKILL.md`、`scripts/`、`references/`、[`.cursor/rules/token-diet.mdc`](.cursor/rules/token-diet.mdc) をプロジェクトにコピーします。ルールファイルは `@SKILL.md` でスキルを埋め込みます。

</details>

<details>
<summary><b>Codex / AGENTS.md を読む任意のエージェント</b></summary>

`SKILL.md`、`scripts/`、`references/` を `.agents/skills/token-diet/` にコピーし、[`codex/INSTRUCTIONS.md`](codex/INSTRUCTIONS.md) のスニペットを自分の `AGENTS.md` に追加します。このリポジトリ自身の [`AGENTS.md`](AGENTS.md) が書き方の見本です。

</details>

<details>
<summary><b>エージェントなしで</b></summary>

各スクリプトは単体で動きます: `python3 scripts/diet.py --help`、`python3 scripts/measure.py --help`、`python3 scripts/estimate.py --help`。書き換えのルールは人が読める形でも [`references/compaction-rules.md`](references/compaction-rules.md) に書いてあります。

</details>

## 制限と正直な注意点

- コードフェンス内のコメントは元の言語のままです。保護ステップは意図的にコードをバイト単位で保持します。
- 文字数ベースの見積もりはヒューリスティックです。仮定している 5 つのレートは `scripts/estimate.py` にあり、それを変えれば固定済みのレポートも変わります。テストはそのためにあります。見積もりを測定値として引用しないでください。
- 検証ステップが保証するのはプレースホルダーであって、ニュアンスではありません。安価なモデルは限定語を落とすことがあります。テンプレートとして再利用する前に、結果を一度は読んでください。
- 言語判定は文字種とストップワードに基づきます（ru、uk、es、pt、de、fr、it）。それ以外の言語には汎用の "answer in the language of the original request" という行が付きます。正確にしたい場合は `--answer-in` を渡してください。
- `examples/` 内の `after.txt` はメンテナーによる参照用の書き換えであり、モデルの出力ではありません。目標の形を示すものであり、あなたのモデルの出力は異なります。
- 書き換えが割に合うのは、プロンプトを再利用する場合か、受け取る側のモデルが書き換える側より大幅に高価な場合です。一行のチャットメッセージには向きませんし、結果が入力より長くなった場合は `diet.py` が警告します。

## よくある質問

<details>
<summary><b>API キーなしでも動きますか?</b></summary>

一部は動きます。`--dry-run` は何も送信せずに保護済みプロンプトと実際のリクエストを表示し、`measure.py` はラベル付きの見積もりにフォールバックし、`references/compaction-rules.md` があればエージェントが手動で書き換えられます。本当の書き換えには、3 つのプロバイダーのいずれか 1 つのキーが必要で、環境変数から読み取ります。

</details>

<details>
<summary><b>そもそもなぜ別のモデルにプロンプトを送るのですか? エージェント自身が翻訳すればよいのでは?</b></summary>

できますが、それはエージェントのトークン単価で、エージェントのコンテキスト内で行われます。要点は、安価なモデルで一度だけ削り、その簡潔版を再利用することです。`CLAUDE.md` や `AGENTS.md` に入れる、保存済みのタスクテンプレートにする、システムプロンプトにする、few-shot の例にする、といった使い方です。短い一回きりのメッセージなら、この手順は飛ばしてください。

</details>

<details>
<summary><b>エージェントはそれでもロシア語で答えてくれますか?</b></summary>

はい。書き換え後のプロンプトの最後の行は `Answer in Russian.`（あるいは Spanish、Portuguese、German など）で、`SKILL.md` はエージェントにセッション中その言語を維持するよう指示します。プロンプト内のボタンのラベルや引用符内の文字列も保護されているので、元の言語のまま残ります。

</details>

<details>
<summary><b>トークンを数えるのはどのモデルですか?</b></summary>

`measure.py --model` で指定したモデルで、デフォルトは `claude-opus-5-5` です。カウントはトークナイザーごとに異なるので、実際にプロンプトを受け取るモデルで数えてください。OpenAI や Gemini 用のカウント経路はここにはありません。それらのプロバイダーについては、見積もりであると明記した値が返ります。

</details>

<details>
<summary><b>プロンプトはどこかに保存されますか?</b></summary>

あなたが送った先にだけ残ります。スクリプトは標準出力か `--out` で指定したファイルに書き込むだけで、キャッシュもログも持ちません。プロバイダー側で何が保持されるかは、そのプロバイダーの規約によります。

</details>

## 関連リポジトリ

- [skill-shrinker](https://github.com/uniqaiapp/skill-shrinker): SKILL.md やエージェントの指示ファイルを圧縮します。サイズを測り、長い内容を references に移し、トリガーはそのまま残します。
- [model-router](https://github.com/uniqaiapp/model-router): タスクをこなせる中でもっとも安いモデルを選びます。ルール表と、タスクを種類・長さ・リスクで振り分ける標準ライブラリ製スクリプト。
- [deslop-ru](https://github.com/uniqaiapp/deslop-ru): ロシア語テキストから AI っぽい埋め草を取り除きます。スキルと、よくある癖を検出して書き換える標準ライブラリ製スクリプト。

## コントリビュート

Issue と pull request を歓迎します。変更は小さく保ち、PR の説明に before/after の例を添えてください。
ローカルでのチェック（`python3 tests/run.py`、依存関係なし）は [CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。

## ライセンス

[MIT](LICENSE) © UniqAI

---

<div align="center">

<sub>Made by <a href="https://uniqai.app/?utm_source=github&utm_medium=readme-ja&utm_campaign=token-diet">UniqAI</a> — Kling 3.0、Veo 3、Flux、Nano Banana、そして GPT-5/Claude/Gemini/Grok を一つのアプリで。私たち自身がこのトークン代を払っているので、自分たちのプロンプトもこの方法で短く保っています。</sub>

</div>
