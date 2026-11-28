# CLAUDE.md

Claude Code 用プラグイン `html-report`（`plugins/html-report/`）。依頼と素材から、1 ファイル完結の HTML レポートを作る。Windows 11 で動作を確かめている。利用者向けの説明は `README.md`。

## コマンド

開発用の依存は `requirements-dev.txt`。`.venv/` は Git 管理外（リポジトリ直下で `python -m venv .venv` を作る）。

```bash
.venv/Scripts/python -m pytest        # 全テスト（形式の検査 test_plugin.py、HTML の検査 test_check_html.py、解説ページの検査 test_explain_create.py）
.venv/Scripts/python -m ruff check .  # lint（ルールは pyproject.toml）
```

`test_claude_plugin_validateが通る` は `claude plugin validate --strict` を実行する（`claude` がなければ skip）。

## 構成

- `plugins/html-report/skills/create/SKILL.md`: レポートを作る手順の目次と、守ること・止まるとき。手順2〜10 の詳細は `skills/create/references/`（`materials.md`・`generate.md`・`verify.md`・`select.md`）に分けてある。手順7 の DOM 検査だけは、`browser_evaluate` に渡す関数 `dom-check.js` にしてある。
- `plugins/html-report/skills/doctor/SKILL.md`: 環境の点検。Claude が利用可能なツールとスキルを見て判定するので、スクリプトはない（plugin-rules A4 の例外）。
- `tests/check_html.py`: 作った HTML の検査（外部読み込み・外部への送信など）。`tests/SCENARIOS.md` は手動の受入シナリオ。
- `docs/explain-create/`: create の動作解説ページ。文章のテンプレート `page.html` と、生成スクリプト `build.py`。使い方と直し方は `docs/development.md`。

## 動作解説ページの更新

- `page.html` に、実ファイルの文章・大きさ・版・件数の写しを書かない。`{{名前}}` で埋め、`build.py` が生成のたびにリポジトリから読む。標準出力も、生成のたびにデモを実行して採取する。
- 手順書（`SKILL.md`・`references/`）・`dom-check.js`・`tests/check_html.py`・`tests/fixtures/sales.csv`・出力の書式を変えたら、同じ PR で次を行う。
  - `.venv/Scripts/python docs/explain-create/build.py` を実行し、`preview.html` を画面で確かめる。
  - `page.html` の手書きの説明（手順の中身・回数・止まる条件）を見直す。
  - 画面が変わったときは、`docs/images/explain-create-sample.png` を撮り直し、`SHOT_VERSION` を更新する。
- 公開した Artifact は、リポジトリと連動しない。直したら、再生成して再公開する。
- 出力は一時フォルダに作る。リポジトリの中には出力しない。

## 守ること

- 版は、`plugins/html-report/.claude-plugin/plugin.json` の `version`、`pyproject.toml` の `version`、`plugins/html-report/skills/doctor/SKILL.md` の表示例（`[情報] プラグインのバージョン: v…`）の 3 か所にある。版を上げるときは、そろえる。
- SKILL.md の環境の判定方法は、create と doctor で同じ文面にそろえる。
- 規則は `~/.claude/reference/plugin-rules.md`。SKILL.md や README を直したら、テストを先に流す。
- `docs/superpowers/`・`docs/grill-spec/` は `.gitignore` の対象（作業メモの置き場）。
