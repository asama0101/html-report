---
name: doctor
description: html-report が動く環境かを点検し、足りないものと対処の手順を出す。Playwright MCP・artifact-design・dataviz・artifact-diagramming の有無（と OS）と、GitHub をマーケットプレイスに登録していれば最新版かどうかを、項目ごとに伝える。「環境を点検して」「doctor」「動かない原因を調べて」と頼まれたときに使う。何も変更しない（Playwright がファイルを作ることはある）。レポートの作成には使わない（create）。Windows 専用。
disable-model-invocation: true
---

html-report の動作に必要な環境を点検し、結果を、共通の行形式で報告する。1 行 1 項目で、`[OK]`・`[NG]`（必須が足りない）・`[任意]`（なくても動く）・`[情報]`（版）のどれかを付け、対処は次の行に「→」で書く。点検だけを行い、インストールや設定の変更はしない（Playwright MCP の確認で、Playwright が出力先にファイルを作ることはある）。

判定は次のとおり。

1. OS: 実行環境の Platform が `win32`（Windows）なら `[OK]`、それ以外は `[NG]`。
2. Playwright MCP: `mcp__playwright__browser_navigate` などのブラウザツールが、利用可能なツールの一覧、または ToolSearch（遅延読み込みのツールを含む）で見つかり、`browser_navigate` で `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` を `file://` の URL（`\` を `/` にし、各部分をパーセントエンコードする）で開ければ `[OK]`。開けなければ `[NG]` とし、エラーの文をそのまま伝える（`[NG] Playwright MCP: file:// を開けません（<エラーの文>）`）。エラーが `Access to "file:" protocol is blocked` なら、「Playwright MCP が `--allow-unrestricted-file-access` なしで登録されている」と伝える。それ以外のエラー（ブラウザがない、タイムアウトなど）も `[NG]` とする。`browser_navigate` の承認が得られなかったときは、`[NG]` にせず、`[OK] Playwright MCP: ツールはあります（file:// を開けるかは、承認されなかったため確認していません）` とする。ツールが見つからなければ `[NG]`。ツール結果がファイルのパスを報告したとき（Playwright が出力先にスナップショットなどを書いたとき）は、消さずに、次の行に `  → Playwright が <パス> を作った（不要なら削除してよい）` と書く。`mcp__claude-in-chrome__*` は対象外で、これがあっても `[OK]` としない。
3. `artifact-design`: 利用可能なスキルの一覧に `artifact-design` があれば `[OK]`、なければ `[NG]`。
4. `dataviz`（任意）: スキルの一覧にあれば `[OK]`、なければ `[任意]`（未導入でも動く）。
5. `artifact-diagramming`（任意）: スキルの一覧にあれば `[OK]`、なければ `[任意]`（未導入でも動く）。

6. プラグインのバージョン（html-report 本体）: 次の順に調べる。読み取りだけを行う。行の頭は `[情報] プラグインのバージョン: v<現在のバージョン>`。
   1. `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` の `version` を、現在のバージョンとする。
   2. `~/.claude/plugins/known_marketplaces.json` の `html-report` の `source` が `"source": "github"` でなければ（`--plugin-dir` で使っている場合など）、「（GitHub のマーケットプレイスに登録していないため、最新かは確認しません）」を続けて終わる。
   3. 手順 2 の `source.repo` を使い、Bash で `curl -fsS --max-time 10 https://raw.githubusercontent.com/<repo>/HEAD/plugins/html-report/.claude-plugin/plugin.json` を実行し、`version` を最新のバージョンとする。取得できないとき（10 秒で応答がないときを含む）、または手順 2 のファイルを読めないときは、「（最新のバージョンを確認できませんでした: <理由>）」を続け、次の行に「  → ネットワークにつながっているか、github.com への通信を止めていないかを確認する」を書いて終わる。
   4. 現在と最新を、`MAJOR.MINOR.PATCH` の数値で比べる。現在が最新以上なら「（最新です）」。最新が大きければ「（GitHub に v<最新> があります）」を続け、次の 3 行を書く。
      - `  → /plugin marketplace update html-report を実行する`
      - `  → /plugin update html-report@html-report を実行する`
      - `  → Claude Code を開き直す`

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
[情報] プラグインのバージョン: v0.1.1（最新です）
```

出力は、項目の行と対処の行だけにする（前置きや結びの文は付けない）。
