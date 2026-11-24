"""解説ページの「実際の画面」に使う、例のレポートを作る。

tests/fixtures/sales.csv を読み、create の「守ること」（1 ファイル完結・CSP の meta・
素材の文字列のエスケープ・外部読み込みなし）に沿った HTML を書く。
create を実行して出た HTML ではない。
"""

import csv
import html
from pathlib import Path

# グラフの寸法（SVG の viewBox）。座標は、目盛りと同じ式でコードで計算する。
W, H = 760, 270
LEFT, RIGHT, TOP, BOTTOM = 56, 24, 28, 40
SALES_MAX = 200.0  # 売上の軸の上限（万円）
COUNT_MAX = 70  # 件数の軸の上限（件）

CSP = (
    "default-src 'none'; img-src data:; font-src data:; style-src 'unsafe-inline'; "
    "script-src 'unsafe-inline'; form-action 'none'; base-uri 'none'"
)
STYLE = """
:root{--bg:#f4f6f9;--fg:#1a2330;--muted:#5a6676;--line:#d5dbe3;--panel:#fff;--accent:#1f5fbf;--accent2:#7aa5e6}
@media (prefers-color-scheme:dark){:root{--bg:#12171d;--fg:#e4e9ef;--muted:#9aa7b8;--line:#33404f;--panel:#1a222b;--accent:#6fa8f0;--accent2:#3f6ca8}}
body{margin:0;background:var(--bg);color:var(--fg);font-family:"Yu Gothic UI","Meiryo",sans-serif;line-height:1.7}
main{max-width:1100px;margin:0 auto;padding:28px 32px 40px}
h1{font-size:26px;margin:0 0 4px} h2{font-size:18px;margin:28px 0 8px}
.lead{background:var(--panel);border:1px solid var(--line);border-left:5px solid var(--accent);padding:14px 18px;font-size:18px;margin:14px 0}
.panel{background:var(--panel);border:1px solid var(--line);padding:12px 16px}
svg{width:100%;height:auto;display:block}
table{border-collapse:collapse;width:100%;background:var(--panel)}
th,td{border-bottom:1px solid var(--line);padding:6px 10px;text-align:left} td.num{text-align:right;font-variant-numeric:tabular-nums}
p.m{color:var(--muted);font-size:14px;margin:4px 0}
"""


def man(yen: int) -> str:
    """円を万円の文字列にする。"""
    return f"{yen / 10000:.1f}"


def _x(i: int, n: int) -> float:
    return LEFT + (W - LEFT - RIGHT) * i / (n - 1)


def _y_sales(yen: int) -> float:
    return TOP + (H - TOP - BOTTOM) * (1 - (yen / 10000) / SALES_MAX)


def _month_labels(months: list[str]) -> str:
    return "".join(
        f'<text x="{_x(i, len(months)):.1f}" y="{H - 16}" text-anchor="middle" '
        f'font-size="12" fill="var(--muted)">{html.escape(m[2:])}</text>'
        for i, m in enumerate(months)
    )


def _line_chart(months: list[str], sales: list[int], hi: int, lo: int) -> str:
    n = len(sales)
    grid = "".join(
        f'<line x1="{LEFT}" x2="{W - RIGHT}" y1="{_y_sales(v * 10000):.1f}" '
        f'y2="{_y_sales(v * 10000):.1f}" stroke="var(--line)"/>'
        f'<text x="{LEFT - 8}" y="{_y_sales(v * 10000) + 4:.1f}" text-anchor="end" '
        f'font-size="12" fill="var(--muted)">{v}</text>'
        for v in range(0, int(SALES_MAX) + 1, 50)
    )
    points = " ".join(f"{_x(i, n):.1f},{_y_sales(v):.1f}" for i, v in enumerate(sales))
    dots = "".join(
        f'<circle cx="{_x(i, n):.1f}" cy="{_y_sales(sales[i]):.1f}" r="5" fill="var(--accent)"/>'
        for i in (hi, lo)
    )
    label_hi = (
        f'<text x="{_x(hi, n) - 10:.1f}" y="{_y_sales(sales[hi]) - 4:.1f}" text-anchor="end" '
        f'font-size="13" font-weight="700" fill="var(--fg)">最高 {man(sales[hi])}</text>'
    )
    label_lo = (
        f'<text x="{_x(lo, n):.1f}" y="{_y_sales(sales[lo]) + 22:.1f}" text-anchor="middle" '
        f'font-size="13" font-weight="700" fill="var(--fg)">最低 {man(sales[lo])}</text>'
    )
    aria = (
        f"月別売上の折れ線グラフ（万円）。{html.escape(months[lo])} の {man(sales[lo])} 万円が最低、"
        f"{html.escape(months[hi])} の {man(sales[hi])} 万円が最高"
    )
    return (
        f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{aria}" '
        f'xmlns="http://www.w3.org/2000/svg">{grid}'
        f'<polyline points="{points}" fill="none" stroke="var(--accent)" stroke-width="2.5"/>'
        f"{dots}{label_hi}{label_lo}{_month_labels(months)}"
        f'<text x="{LEFT}" y="14" font-size="12" fill="var(--muted)">単位: 万円</text></svg>'
    )


def _bar_chart(months: list[str], counts: list[int]) -> str:
    n = len(counts)
    width = (W - LEFT - RIGHT) / n * 0.6
    bars = ""
    for i, c in enumerate(counts):
        height = (H - TOP - BOTTOM) * c / COUNT_MAX
        bars += (
            f'<rect x="{_x(i, n) - width / 2:.1f}" y="{H - BOTTOM - height:.1f}" '
            f'width="{width:.1f}" height="{height:.1f}" fill="var(--accent2)"/>'
            f'<text x="{_x(i, n):.1f}" y="{H - BOTTOM - height - 5:.1f}" text-anchor="middle" '
            f'font-size="12" fill="var(--fg)">{c}</text>'
        )
    bars += (
        f'<line x1="{LEFT}" x2="{W - RIGHT}" y1="{H - BOTTOM}" y2="{H - BOTTOM}" '
        f'stroke="var(--line)"/>{_month_labels(months)}'
    )
    return (
        f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="月別件数の棒グラフ（件）" '
        f'xmlns="http://www.w3.org/2000/svg">{bars}'
        f'<text x="{LEFT}" y="14" font-size="12" fill="var(--muted)">単位: 件</text></svg>'
    )


def build_report(csv_path: Path) -> tuple[str, str]:
    """HTML と、画面の値を説明する 1 文（解説ページの照合の項目に使う）を返す。"""
    with csv_path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    months = [r["月"] for r in rows]
    sales = [int(r["売上(円)"]) for r in rows]
    counts = [int(r["件数"]) for r in rows]
    notes = [r["備考"] for r in rows]
    hi, lo = sales.index(max(sales)), sales.index(min(sales))
    total = sum(sales)
    esc = html.escape

    body_rows = "".join(
        f'<tr><td>{esc(m)}</td><td class="num">{man(s)}</td><td class="num">{c}</td><td>{esc(n)}</td></tr>'
        for m, s, c, n in zip(months, sales, counts, notes, strict=True)
    )
    page = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="{CSP}">
<title>月次売上レポート</title>
<style>{STYLE}</style>
</head>
<body><main>
<h1>月次売上レポート</h1>
<p class="m">対象: {esc(months[0])}〜{esc(months[-1])}（{len(months)} か月）。読み手: 役員。目的: 来期の販促予算を決める。</p>
<p class="lead">売上が最高の月は {esc(months[hi])} の {man(sales[hi])} 万円（{counts[hi]} 件）、最低の月は {esc(months[lo])} の {man(sales[lo])} 万円（{counts[lo]} 件）。{len(months)} か月の合計は {man(total)} 万円。</p>
<h2>売上の推移</h2>
<div class="panel">{_line_chart(months, sales, hi, lo)}</div>
<h2>件数の推移</h2>
<div class="panel">{_bar_chart(months, counts)}</div>
<h2>月別の数値</h2>
<table><thead><tr><th>月</th><th>売上（万円）</th><th>件数</th><th>備考</th></tr></thead><tbody>{body_rows}</tbody></table>
<h2>出典</h2>
<p class="m">{esc(csv_path.name)}</p>
</main></body></html>
"""
    facts = (
        f"{len(months)} か月の売上と件数、最高 {months[hi]} の {man(sales[hi])} 万円・{counts[hi]} 件、"
        f"最低 {months[lo]} の {man(sales[lo])} 万円・{counts[lo]} 件、合計 {man(total)} 万円"
    )
    return page, facts
