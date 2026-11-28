# 開発者向けの情報

利用者向けの説明は [README.md](../README.md)。Claude が守る規則は [CLAUDE.md](../CLAUDE.md)。ここは、このリポジトリを直す人向けの、準備・構成・版の手順。

## 準備

開発用の依存は `requirements-dev.txt`。`.venv/` は Git 管理外で、リポジトリ直下で `python -m venv .venv` を作り、依存を入れる。確認のコマンドは、CLAUDE.md の「コマンド」にある。

`test_claude_plugin_validateが通る` は `claude plugin validate --strict` を実行する（`claude` がなければ skip）。

## 構成

- `plugins/html-report/skills/create/SKILL.md`: レポートを作る手順の目次と、守ること・止まるとき。手順2〜10 の詳細は `skills/create/references/`（`materials.md`・`generate.md`・`verify.md`・`select.md`）に分けてある。手順7 の DOM 検査だけは、`browser_evaluate` に渡す関数 `dom-check.js` にしてある。
- `plugins/html-report/skills/doctor/SKILL.md`: 環境の点検。Claude が利用可能なツールとスキルを見て判定するので、スクリプトはない（plugin-rules A4 の例外）。
- `tests/check_html.py`: 作った HTML の検査（外部読み込み・外部への送信など）。`tests/SCENARIOS.md` は手動の受入シナリオ。

## 版を上げる

版は、次の 3 か所にある。上げるときは、そろえる。

- `plugins/html-report/.claude-plugin/plugin.json` の `version`
- `pyproject.toml` の `version`
- `plugins/html-report/skills/doctor/SKILL.md` の表示例（`[情報] プラグインのバージョン: v…`）
