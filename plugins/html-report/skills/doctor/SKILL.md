---
name: doctor
description: html-report が動く環境かを点検し、足りないものと対処の手順を出す。Playwright MCP・artifact-design・dataviz・artifact-diagramming の有無（と OS）と、GitHub をマーケットプレイスに登録していれば最新版かどうかを、項目ごとに伝える。「環境を点検して」「doctor」「動かない原因を調べて」と頼まれたときに使う。何も変更しない（Playwright がファイルを作ることはある）。レポートの作成には使わない（create）。Windows 専用。
disable-model-invocation: true
---

# doctor: 環境の点検

html-report の動作に必要な環境を点検し、結果を、共通の行形式で報告する。足りないものには、対処を次の行に添える。点検だけを行い、インストールや設定の変更はしない（Playwright MCP の確認で、Playwright が出力先にファイルを作ることはある）。

## 用語
| 用語 | 意味 |
|---|---|
| `[OK]` | 満たしている |
| `[NG]` | 必須のものが足りない |
| `[任意]` | なくても動く（使う機能のときだけ要る）ものが足りない |
| `[情報]` | プラグインのバージョンと、最新版の確認結果 |
| Playwright MCP | ブラウザを操作するツール群。作った HTML を `file://` で開いて確かめるのに使う |
| ToolSearch | 遅延読み込みのツールを探すツール |
| `artifact-design` | デザインの指針を持つスキル |
| `dataviz` | グラフの指針を持つスキル |
| `artifact-diagramming` | 図の指針を持つスキル |

出力は、1 行 1 項目で、`[OK]`・`[NG]`・`[任意]`・`[情報]` のどれかを先頭に付け、対処は次の行に「→」で書く。

## 全体の流れ
| 手順 | やること | 終わりの目印 |
|---|---|---|
| 1 OS の確認 | Windows かを確かめる | OS の行を出した |
| 2 Playwright MCP の確認 | ブラウザツールがあり、`file://` を開けるかを確かめる | Playwright MCP の行を出した |
| 3 `artifact-design` の確認 | スキルの一覧を確かめる | `artifact-design` の行を出した |
| 4 `dataviz` の確認 | スキルの一覧を確かめる | `dataviz` の行を出した |
| 5 `artifact-diagramming` の確認 | スキルの一覧を確かめる | `artifact-diagramming` の行を出した |
| 6 プラグインのバージョンの確認 | 現在のバージョンと、GitHub の最新を比べる | バージョンの行を出した |

## 手順

### 手順1: OS の確認
目的: 対応する OS（Windows）で動いているかを確かめる。

Platform が `win32`（Windows）なら `[OK]`、それ以外は `[NG]`。

### 手順2: Playwright MCP の確認
目的: ブラウザツールがあり、作った HTML を `file://` で開けるかを確かめる。

- `mcp__playwright__browser_navigate` などのブラウザツールが、ツールの一覧か ToolSearch で見つかり、`browser_navigate` で `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` を `file://` の URL（`\` を `/` にし、各部分をパーセントエンコードする）で開ければ `[OK]`。
- 開けなければ、エラーの種類（ブラウザがない、タイムアウトなど）を問わず `[NG]` とし、エラーの文をそのまま伝える（`[NG] Playwright MCP: file:// を開けません（<エラーの文>）`）。
- エラーが `Access to "file:" protocol is blocked` なら、「Playwright MCP が `--allow-unrestricted-file-access` なしで登録されている」と伝える。
- `browser_navigate` の承認が得られなかったときは、`[NG]` にせず、`[OK] Playwright MCP: ツールはあります（file:// を開けるかは、承認されなかったため確認していません）` とする。
- ツールが見つからなければ `[NG]`。
- ツール結果がファイルのパスを報告したとき（Playwright が出力先にスナップショットなどを書いたとき）は、消さずに、次の行に `  → Playwright が <パス> を作った（不要なら削除してよい）` と書く。
- `mcp__claude-in-chrome__*` があっても `[OK]` としない。

### 手順3: `artifact-design` の確認
目的: デザインの指針のスキルが使えるかを確かめる。

スキルの一覧に `artifact-design` があれば `[OK]`、なければ `[NG]`。

### 手順4: `dataviz` の確認
目的: グラフの指針のスキルがあるかを確かめる（なくても動く）。

スキルの一覧にあれば `[OK]`、なければ `[任意]`（未導入でも動く）。

### 手順5: `artifact-diagramming` の確認
目的: 図の指針のスキルがあるかを確かめる（なくても動く）。

スキルの一覧にあれば `[OK]`、なければ `[任意]`（未導入でも動く）。

### 手順6: プラグインのバージョンの確認
目的: html-report 本体の現在のバージョンと、GitHub 上の最新を比べる。

読み取りだけを行う。行の頭は `[情報] プラグインのバージョン: v<現在のバージョン>`。次の順に調べる（番号は、この手順の中の番号）。
1. `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` の `version` を、現在のバージョンとする。読めないとき（承認されなかったときを含む）は、`[情報] プラグインのバージョン: 確認できませんでした（<理由>）` の 1 行だけを出して終わる。
2. `~/.claude/plugins/known_marketplaces.json` を読む。ファイルを読めないときは、下の 3 の「確認できませんでした」の扱いにする。`html-report` の項目がないとき、または `html-report` の `source` が `"source": "github"` でないとき（`--plugin-dir` で使っている場合など）は、「（GitHub のマーケットプレイスに登録していないため、最新かは確認しません）」を続けて終わる。
3. 2 の `source.repo` を使い、Bash で `curl -fsS --max-time 10 https://raw.githubusercontent.com/<repo>/HEAD/plugins/html-report/.claude-plugin/plugin.json` を実行し、`version` を最新のバージョンとする（GitHub から最新の plugin.json を取り寄せる）。取得できないとき（10 秒で応答がないときを含む）、または 2 のファイルを読めないときは、「（最新のバージョンを確認できませんでした: <理由>）」を続け、次の行に「  → ネットワークにつながっているか、github.com への通信を止めていないかを確認する」を書いて終わる。
4. 現在と最新を、`MAJOR.MINOR.PATCH` の数値で比べる。現在が最新以上なら「（最新です）」。最新が大きければ「（GitHub に v<最新> があります）」を続け、次の 3 行を書く。
   - `  → /plugin marketplace update html-report を実行する`
   - `  → /plugin update html-report@html-report を実行する`
   - `  → Claude Code を開き直す`

## 対処の案内と出力の形
`[NG]` の項目には、README の該当する節を添える。
- OS → 「導入方法」の冒頭
- Playwright MCP → 「導入方法」の 2
- `artifact-design` → 「導入方法」の冒頭

出力の例:

```
[OK] OS: Windows
[OK] Playwright MCP: 使えます
[NG] artifact-design: 使えません
  → README の「導入方法」の冒頭を見る
[任意] dataviz: 未導入（なくても動く）
[任意] artifact-diagramming: 未導入（なくても動く）
[情報] プラグインのバージョン: v0.1.2（最新です）
```

出力は、項目の行と対処の行だけにする（前置きや結びの文は付けない）。
