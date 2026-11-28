# CLAUDE.md

Claude Code 用プラグイン `html-report`（`plugins/html-report/`）。依頼と素材から、1 ファイル完結の HTML レポートを作る。Windows 11 で動作を確かめている。利用者向けの説明は `README.md`。

## コマンド

```bash
.venv/Scripts/python -m pytest        # 全テスト（形式の検査 test_plugin.py、HTML の検査 test_check_html.py）
.venv/Scripts/python -m ruff check .  # lint（ルールは pyproject.toml）
.venv/Scripts/python -m ruff format --check .
```

## 守ること

- SKILL.md の環境の判定方法は、create と doctor で同じ文面にそろえる。
- `skills/create/SKILL.md`・`references/*.md`・`dom-check.js` を変えたら、README の図（`docs/images/`）を見直す。
- 規則は `~/.claude/reference/plugin-rules.md`。SKILL.md や README を直したら、テストを先に流す。
- `docs/superpowers/`・`docs/grill-spec/` は `.gitignore` の対象（作業メモの置き場）。

## 作業の前に読むファイル

| 作業 | 読むファイル |
|---|---|
| 準備、構成の確認、版を上げる | `docs/development.md` |
