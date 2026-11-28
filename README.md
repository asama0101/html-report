# html-report

依頼と素材ファイルから、デザインされた HTML レポートを 1 ファイルで作る Claude Code プラグイン。CSV やメモをもとに、読み手に合わせたレポートを作りたい人向け。

```
/html-report:create 先月の売上 CSV（C:\data\sales.csv）を、経営会議向けのレポートにして
```

<img src="docs/images/overview.svg" alt="全体の流れ。依頼文と素材ファイルを create に渡すと、質問、案ごとの生成と保存、全案の検証、案の選択の順に進む。デザインの異なる完成版が 2〜3 案できて、選んだ案の HTML レポートだけが残る" width="800">

## 機能

外部の CDN・Web フォント・画像を読み込まないので、作ったレポートはファイル単体で開ける。

| 項目 | できること | できないこと |
|---|---|---|
| 出力 | 1 ファイルで完結する HTML を作る。 | PDF・PowerPoint の生成、既存 HTML の編集、完成後の修正支援。 |
| 表示 | PC の画面（幅 1280px）で読める形にする。 | スマートフォン表示と印刷。 |
| 構成 | 縦に続く 1 つのレポートを作る。 | 複数ページのサイトとフォーム送信。 |
| 大きな CSV | 1000 行超は、集計・要約を載せる。 | 1000 行超の全件掲載。 |

スキルは 2 つ。

- `/html-report:create`: レポートを作る。11 の手順で進む。
- `/html-report:doctor`: 環境を点検する。何も変更しない（Playwright がファイルを作ることはある）。`[NG]` の次の行に対処が出る。

## 導入方法

次がそろっていること。

- Windows 11（Windows 専用）、Claude Code（動作確認は 2.1.328）
- Playwright MCP（ブラウザを操作して、作った HTML を確かめる部品。手順 2 で入れる）
- Node.js 20 以上（動作確認は 24.13.1）、Chrome または Edge
- ネットワーク接続（Playwright MCP の取得と、`/html-report:doctor` の最新バージョンの確認に使う）
- `artifact-design` スキル（Claude Code に同梱。`/skills` の一覧にあること）
- 任意: Python 3（1000 行超の CSV の集計）、`dataviz`・`artifact-diagramming` スキル（グラフと図の指針）、Git（オフライン導入の clone）

### 1. プラグインを入れる

Claude Code の中で実行する。

```
/plugin marketplace add asama0101/html-report
/plugin install html-report@html-report
```

### 2. Playwright MCP を入れる

注意: `playwright` がすでに登録されていると、「already exists」で失敗する。先に `claude mcp list` で、`playwright` の行に `--allow-unrestricted-file-access` があるか確かめる。あれば、この手順は要らない。フラグなしで登録済みなら、先に次のコマンドで登録を外してから、下のコマンドを実行する。

> **警告:** `playwright` の登録が消える。下の `claude mcp add` で登録し直せば戻る。ほかの引数を付けていたときは、先に `claude mcp list` の行を控える。

```
claude mcp remove -s user playwright
```

シェルで実行し、Claude Code を再起動する。`--allow-unrestricted-file-access` は、作った HTML を `file://` で開くために必要。Edge だけのときは、末尾に `--browser msedge` を足す。

```
claude mcp add -s user playwright -- npx @playwright/mcp@latest --allow-unrestricted-file-access
```

### 3. 環境を点検する

```
/html-report:doctor
```

### 更新

`/html-report:doctor` が新しい版を知らせたら、次を実行して、Claude Code を開き直す。

```
/plugin marketplace update html-report
/plugin update html-report@html-report
```

## 使い方

依頼文に目的と素材のパスを書くと、レポートが 1 つ保存される。`create` は、次の図の順に進む。

注意: 最後の段階で、選ばなかった案のファイルが削除される。削除したファイルは元に戻せないので、残したい案は、選ぶ前に別の場所へコピーする。

<img src="docs/images/flow.svg" alt="create の流れ。環境と素材、要件の確定、案の生成と保存、検証、選択と照合、後始末と報告の順に進む。選択で「その他」を選ぶと、案の生成に戻る" width="800">

要件の確定では、分からない項目だけを聞く。

<img src="docs/images/ask.svg" alt="要件を聞くときの動作。依頼文と素材から分かる項目は聞かず、分からない項目だけを選択式で聞く。素材に根拠のない必須項目は、内容を伝える、項目を外す、「素材なし」と書いて載せる、の 3 つから選ぶ。要件のまとめを見せ、「このまま作る」と答えると HTML を作る。「直す」と答えると、まとめを書き直す。質問ツールが使えない実行では、文章で出して止まる" width="800">

検証では、保存した全案を開いて確かめる。

<img src="docs/images/verify.svg" alt="全案の検証と、選んだ案の照合。全案は、崩れがないこと、外部へのリクエストがないこと、危険な属性や要素がないことを確かめる。選んだ案は、必須の内容、章の順序、読み手、目的、結論の位置、分量、出典と未確定事項の 7 点を照合する。合わない点は、崩れ、安全の検査、照合のそれぞれ最大 3 回まで直す" width="800">

「その他」で伝えると全案を作り直すが、これは初版の選び直しで、完成後の修正支援ではない。終わると、次の形で完了報告が出る。

```
保存先: C:\work\2026-11-10-先月の売上.html
選んだ案: 紺と白の落ち着いた案（全 3 案）。
要件との照合: 必須の内容 3 件をすべて載せた。分量は、指定 2 画面に対して 2.4 画面。
```

素材の内容（機密情報を含む）は HTML にそのまま入る。共有する前に確かめる。

## 困ったとき

### 「使えないもの」が伝えられ、HTML が作られない
OS・Playwright MCP・`artifact-design` のどれかが使えない。`/html-report:doctor` を実行し、`→` の行に従う。

### 検証で、保存した HTML を `file://` で開けず止まる
`claude mcp list` で、`playwright` の行に `--allow-unrestricted-file-access` があるか確かめる。なければ、導入方法の手順 2 をやり直す。

### 検証で、ページの読み込みが 30 秒で終わらず止まる
HTML は保存済み。ブラウザで直接開いて確かめる。

## ライセンス

[MIT License](LICENSE)
