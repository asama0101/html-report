# CLAUDE.md

Claude Code 用プラグイン `html-report`（`plugins/html-report/`）。依頼と素材から、1 ファイル完結の HTML レポートを作る。Windows 11 で動作を確かめている。利用者向けの説明は `README.md`。

## コマンド

開発用の依存は `requirements-dev.txt`。`.venv/` は Git 管理外（リポジトリ直下で `python -m venv .venv` を作る）。

```bash
.venv/Scripts/python -m pytest        # 全テスト（形式の検査 test_plugin.py、HTML の検査 test_check_html.py）
.venv/Scripts/python -m ruff check .  # lint（ルールは pyproject.toml）
.venv/Scripts/python -m ruff format --check .
```

`test_claude_plugin_validateが通る` は `claude plugin validate --strict` を実行する（`claude` がなければ skip）。

## 構成

- `plugins/html-report/skills/create/SKILL.md`: レポートを作る手順の目次と、守ること・止まるとき。手順2〜10 の詳細は `skills/create/references/`（`materials.md`・`generate.md`・`verify.md`・`select.md`）に分けてある。手順7 の DOM 検査だけは、`browser_evaluate` に渡す関数 `dom-check.js` にしてある。
- `plugins/html-report/skills/doctor/SKILL.md`: 環境の点検。Claude が利用可能なツールとスキルを見て判定するので、スクリプトはない（plugin-rules A4 の例外）。
- `tests/check_html.py`: 作った HTML の検査（外部読み込み・外部への送信など）。`tests/SCENARIOS.md` は手動の受入シナリオ。

## 守ること

- 版は、`plugins/html-report/.claude-plugin/plugin.json` の `version`、`pyproject.toml` の `version`、`plugins/html-report/skills/doctor/SKILL.md` の表示例（`[情報] プラグインのバージョン: v…`）の 3 か所にある。版を上げるときは、そろえる。
- SKILL.md の環境の判定方法は、create と doctor で同じ文面にそろえる。
- `skills/create/SKILL.md`・`references/*.md`・`dom-check.js` を変えたら、README の図（`docs/images/`）を見直す。
- 規則は `~/.claude/reference/plugin-rules.md`。SKILL.md や README を直したら、テストを先に流す。
- `docs/superpowers/`・`docs/grill-spec/` は `.gitignore` の対象（作業メモの置き場）。
