"""docs/explain-create/ の生成スクリプトと、文章のテンプレートを検査する。"""

import html
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
EXPLAIN = ROOT / "docs" / "explain-create"
PLUGIN = ROOT / "plugins" / "html-report"
CREATE = PLUGIN / "skills" / "create"
SOURCES = [
    CREATE / "SKILL.md",
    *sorted((CREATE / "references").glob("*.md")),
    CREATE / "dom-check.js",
    PLUGIN / "NOTICE",
]


def run_build(*args):
    return subprocess.run(  # noqa: S603
        [sys.executable, "-X", "utf8", str(EXPLAIN / "build.py"), *args],
        capture_output=True,
        encoding="utf-8",
        check=False,
    )


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("explain") / "out"
    done = run_build(str(out))
    assert done.returncode == 0, done.stdout + done.stderr
    return out


def test_生成でトークンが全部埋まる(built):
    page = (built / "index.html").read_text(encoding="utf-8")
    assert re.findall(r"\{\{[a-z_]+(?::[^}]*)?\}\}", page) == []


def test_実ファイルの全文がそのまま入る(built):
    page = (built / "index.html").read_text(encoding="utf-8")
    for path in SOURCES:
        text = path.read_text(encoding="utf-8")
        assert html.escape(text, quote=True) in page, path.name


def test_版は生成のたびに実ファイルから読む(built):
    plugin = (PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    version = re.search(r'"version":\s*"([^"]+)"', plugin).group(1)
    page = (built / "index.html").read_text(encoding="utf-8")
    assert f"v{version}" in page
    assert "現在の版" in page


def test_check_htmlの標準出力と終了コードを実行して載せる(built):
    page = (built / "index.html").read_text(encoding="utf-8")
    for code in ("0", "1", "2"):
        assert f"[終了コード {code}]" in page
    assert "NG: 必須の語が本文にない: 件数の推移" in page
    assert "使い方: python tests/check_html.py" in page


def test_一時フォルダのパスとユーザー名が出力に残らない(built):
    page = (built / "index.html").read_text(encoding="utf-8")
    assert str(built.parent) not in page
    assert built.parent.as_posix() not in page
    assert str(Path.home().name) not in page


def test_画像が出力先に写される(built):
    shot = built / "images" / "explain-create-sample.png"
    assert shot.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert "images/explain-create-sample.png" in (built / "index.html").read_text(
        encoding="utf-8"
    )


def test_公開用はDOCTYPEとbodyを含まず_確認用は含む(built):
    page = (built / "index.html").read_text(encoding="utf-8")
    preview = (built / "preview.html").read_text(encoding="utf-8")
    assert "<!DOCTYPE" not in page
    assert "<body" not in page
    assert preview.startswith("<!DOCTYPE html>")
    assert "<title>html-report create の動作解説</title>" in page


def test_リポジトリの中には出力しない():
    done = run_build(str(ROOT / "docs" / "explain-create-out"))
    assert done.returncode == 2
    assert not (ROOT / "docs" / "explain-create-out").exists()
    assert run_build("a", "b").returncode == 2


def test_page_htmlに実ファイルの写しがない():
    template = (EXPLAIN / "page.html").read_text(encoding="utf-8")
    copied = []
    for path in SOURCES:
        for line in path.read_text(encoding="utf-8").splitlines():
            if len(line.strip()) >= 30 and line.strip() in template:
                copied.append((path.name, line.strip()[:40]))
    assert copied == []
    plugin = (PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    version = re.search(r'"version":\s*"([^"]+)"', plugin).group(1)
    assert version not in template


def test_page_htmlのトークンがbuildに実装されている():
    template = (EXPLAIN / "page.html").read_text(encoding="utf-8")
    script = (EXPLAIN / "build.py").read_text(encoding="utf-8")
    names = set(re.findall(r"\{\{([a-z_]+)", template))
    assert names
    for name in names:
        assert f"def t_{name}(" in script, name
