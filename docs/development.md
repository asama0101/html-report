# 開発の手引き

利用者向けの説明は [README.md](../README.md)。ここは、このリポジトリを直す人向け。

## テストと lint

```
.venv/Scripts/python -m pytest
.venv/Scripts/python -m ruff check .
.venv/Scripts/python -m ruff format --check .
```

`.venv/` は、リポジトリ直下で `python -m venv .venv` を作り、`requirements-dev.txt` を入れる。

## 動作解説ページ（docs/explain-create/）

create が、何を読み、何を実行し、何が標準出力に出るかを、手順ごとに説明する 1 枚のページ。初めて見る開発者が読む。公開用の HTML は、リポジトリに置かず、毎回生成する。

| ファイル | 役割 |
|---|---|
| `docs/explain-create/page.html` | 文章のテンプレート。実ファイルの写しは書かず、`{{名前}}` で埋める |
| `docs/explain-create/build.py` | 生成スクリプト（標準ライブラリだけ） |
| `docs/explain-create/sample_report.py` | 「実際の画面」に使う例のレポートを、`tests/fixtures/sales.csv` から作る |
| `docs/images/explain-create-sample.png` | 例のレポートの画面（幅 1280px）。撮影時の版は `build.py` の `SHOT_VERSION` |

### 使い方

```
.venv/Scripts/python docs/explain-create/build.py
```

出力先は、省くと一時フォルダの `html-report-explain-create/`。引数で変えられる。リポジトリの中は指定できない。

| 出力 | 内容 |
|---|---|
| `index.html` | 公開用。Artifact に渡す（`<!DOCTYPE>`・`head`・`body` を含まない） |
| `preview.html` | ローカルで開いて確かめる用 |
| `images/` | 解説に使う画像 |

生成のたびに、次をリポジトリから読み直す。

- 手順書・`dom-check.js`・`NOTICE` の全文、手順の節、ファイルの大きさ、版
- 手順の見出しの行番号、手順書の数、手順9 の照合の項目数
- デモの HTML に `tests/check_html.py` を実行した標準出力と終了コード

ブラウザで採取した戻り値（`dom-check.js`・`browser_navigate` など）と、画面の画像は、実行できないので `page.html` と `docs/images/` に固定してある。

### 直すときの決まり

- `page.html` に、実ファイルの文章・ファイルの大きさ・版・件数を書かない。`{{名前}}` を足し、`build.py` に `t_名前` を足す（テストが検査する）。
- 手順書・`dom-check.js`・`tests/check_html.py`・`tests/fixtures/sales.csv` を変えたら、同じ PR で次を行う。
  1. `build.py` を実行し、`preview.html` を 1200px と 400px、ダークテーマで見る。
  2. `page.html` の手書きの説明（手順の中身・回数・秒数・止まる条件）が、手順書と合っているか見直す。
  3. 画面が変わったときは、画像を撮り直し、`SHOT_VERSION` と `SHOT_DATE` を更新する。
- 図・表・カードは、解説の文章。実ファイルの文章と実行結果は、ラベル（読む／標準出力／戻り値）で区別する。
- 公開した Artifact は、リポジトリと連動しない。直したら、`index.html` を `images/` と一緒に再公開する。

## 更新の対応表

| 変えたもの | 見直すもの |
|---|---|
| `skills/create/SKILL.md`・`references/*.md`・`dom-check.js` | 動作解説ページ（`page.html` の説明と、図の順序）。README の図（`docs/images/`） |
| `tests/check_html.py` | 動作解説ページの標準出力（自動で再採取される）と、`page.html` の説明 |
| `tests/fixtures/sales.csv` | 例のレポートの画面（`docs/images/explain-create-sample.png`） |
| 版（`plugin.json`・`pyproject.toml`・doctor の表示例） | 動作解説ページの撮影時の版の注記（画面が変わったときだけ撮り直す） |
