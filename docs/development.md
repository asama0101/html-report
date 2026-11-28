# 開発の手引き

利用者向けの説明は [README.md](../README.md)。ここは、このリポジトリを直す人向け。

## テストと lint

```
.venv/Scripts/python -m pytest
.venv/Scripts/python -m ruff check .
.venv/Scripts/python -m ruff format --check .
```

`.venv/` は、リポジトリ直下で `python -m venv .venv` を作り、`requirements-dev.txt` を入れる。

## 更新の対応表

| 変えたもの | 見直すもの |
|---|---|
| `skills/create/SKILL.md`・`references/*.md`・`dom-check.js` | README の図（`docs/images/`） |
