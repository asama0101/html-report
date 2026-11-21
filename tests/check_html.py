"""生成した HTML の検査。外部読み込み・外部への送信・javascript: の URL・
イベント属性・骨組み（DOCTYPE・charset・CSP の meta）を見る。
文字列の照合なので、すべての経路は見つけられない。主な防御は CSP で、これは補助。
--require を付けると、
必須の語が本文（タグ・script・style を除いた文字）にあるかも見る。

使い方: python tests/check_html.py <html のパス> [--require 語 ...]
問題があれば 1 行ずつ出して終了コード 1、なければ 0。
"""

import html as html_lib
import re
import sys
from pathlib import Path

_URL = r"""["']?\s*(?:https?:)?//"""
_EXTERNAL_LOADS = [
    re.compile(rf"\bsrc\s*=\s*{_URL}", re.I),
    # 候補の先頭だけを見る。base64 の中の ",//" は候補の区切りではない。
    re.compile(
        r"""\bsrcset\s*=\s*["']?(?:[^"'>]*(?:\s|\d[xw],))?(?:https?:)?//""", re.I
    ),
    re.compile(rf"<base\b[^>]*\bhref\s*=\s*{_URL}", re.I),
    re.compile(rf"\bposter\s*=\s*{_URL}", re.I),
    re.compile(rf"<object\b[^>]*\bdata\s*=\s*{_URL}", re.I),
    re.compile(rf"<(?:link|image|use)\b[^>]*\b(?:xlink:)?href\s*=\s*{_URL}", re.I),
    re.compile(rf"@import\s+(?:url\(\s*)?{_URL}", re.I),
    re.compile(rf"\burl\(\s*{_URL}", re.I),
]
_JAVASCRIPT_URL = re.compile(
    r"""\b(?:href|src|action|formaction)\s*=\s*["']?\s*javascript:""", re.I
)
_EXTERNAL_SENDS = [
    re.compile(
        r"\bfetch\s*\(|\bXMLHttpRequest\b|\bnew\s+WebSocket\b|\bsendBeacon\s*\(|\bimport\s*\("
        r"|\bwindow\.open\s*\(|\bnew\s+Image\s*\(|\bnew\s+EventSource\b"
        r"|\bnew\s+Worker\s*\("
        r"|\blocation(?:\.href)?\s*=(?!=)|\blocation\.(?:assign|replace)\s*\("
    ),
    re.compile(rf"<[a-z][^>]*\s(?:ping|formaction)\s*=\s*{_URL}", re.I),
    re.compile(rf"<form\b[^>]*\baction\s*=\s*{_URL}", re.I),
    re.compile(r"""<meta\b[^>]*\bhttp-equiv\s*=\s*["']?refresh\b""", re.I),
]
_EVENT_ATTRIBUTE = re.compile(r"<[a-z][^>]*\son[a-z]+\s*=", re.I)


def find_problems(html: str) -> list[str]:
    problems = []
    for m in _JAVASCRIPT_URL.finditer(html):
        problems.append(f"javascript: の URL: {m.group(0).strip()}")
    for pattern in _EXTERNAL_SENDS:
        for m in pattern.finditer(html):
            problems.append(f"外部への送信: {m.group(0).strip()}")
    for m in _EVENT_ATTRIBUTE.finditer(html):
        problems.append(f"イベント属性: {m.group(0).strip()}")
    for pattern in _EXTERNAL_LOADS:
        for m in pattern.finditer(html):
            problems.append(f"外部読み込み: {m.group(0).strip()}")
    return problems


def find_structure_problems(html: str) -> list[str]:
    problems = []
    if not re.match(r"\s*<!DOCTYPE html>", html, re.I):
        problems.append("骨組み: 先頭が <!DOCTYPE html> でない")
    if not re.search(r"<meta\b[^>]*\bcharset\s*=", html, re.I):
        problems.append("骨組み: <meta charset> がない")
    csp = re.search(
        r"""<meta\b[^>]*\bhttp-equiv\s*=\s*["']?Content-Security-Policy\b[^>]*>""",
        html,
        re.I,
    )
    if not csp:
        problems.append("骨組み: CSP の meta がない")
    else:
        for directive in (
            "default-src 'none'",
            "form-action 'none'",
            "base-uri 'none'",
        ):
            if directive not in csp.group(0):
                problems.append(f"骨組み: CSP に {directive} がない")
    return problems


def find_missing_required(html: str, required: list[str]) -> list[str]:
    body = re.sub(r"<(script|style)\b.*?</\1\s*>", "", html, flags=re.I | re.S)
    text = html_lib.unescape(re.sub(r"<[^>]*>", "", body))
    return [f"必須の語が本文にない: {w}" for w in required if w not in text]


def main(argv: list[str]) -> int:
    args = argv[1:]
    required = []
    if "--require" in args:
        i = args.index("--require")
        args, required = args[:i], args[i + 1 :]
    if len(args) != 1:
        print("使い方: python tests/check_html.py <html のパス> [--require 語 ...]")
        return 2
    html = Path(args[0]).read_text(encoding="utf-8")
    problems = (
        find_problems(html)
        + find_structure_problems(html)
        + find_missing_required(html, required)
    )
    for p in problems:
        print("NG:", p)
    if not problems:
        print("OK")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
