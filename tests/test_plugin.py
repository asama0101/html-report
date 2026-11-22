"""プラグインの形式を検査する（plugin-rules E1 の 1〜7）。"""

import json
import re
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugins" / "html-report"
SKILLS = sorted(PLUGIN.glob("skills/*/SKILL.md"))
NAME = "html-report"


def ids(paths):
    return [p.parent.name for p in paths]


def read(path):
    return path.read_text(encoding="utf-8")


def frontmatter(text):
    m = re.match(r"---\r?\n(.*?)\r?\n---\r?\n", text, re.DOTALL)
    assert m, "先頭に frontmatter がない"
    fields = {}
    for line in m.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip()
    return fields


def test_スキルが揃っている():
    assert {p.parent.name for p in SKILLS} == {"create", "doctor"}


@pytest.mark.parametrize("skill", SKILLS, ids=ids(SKILLS))
def test_nameがディレクトリ名と一致しdescriptionがある(skill):
    fm = frontmatter(read(skill))
    assert fm["name"] == skill.parent.name
    assert fm["description"]


def test_doctorは自動起動しない():
    fm = frontmatter(read(PLUGIN / "skills" / "doctor" / "SKILL.md"))
    assert fm["disable-model-invocation"] == "true"


@pytest.mark.parametrize("skill", SKILLS, ids=ids(SKILLS))
def test_絶対パスとCLAUDE_SKILL_DIRがない(skill):
    text = read(skill)
    pattern = r"(?<![A-Za-z])[A-Za-z]:[\/]+\w|/(?:Users|home)/\w"
    assert re.findall(pattern, text) == []
    assert "CLAUDE_SKILL_DIR" not in text


@pytest.mark.parametrize("skill", SKILLS, ids=ids(SKILLS))
def test_CLAUDE_PLUGIN_ROOT_が指すファイルが実在する(skill):
    refs = re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\s\"'`)]+)", read(skill))
    assert [r for r in refs if not (PLUGIN / r).is_file()] == []


@pytest.mark.parametrize("skill", SKILLS, ids=ids(SKILLS))
def test_相対リンクと地の文の相対パスがない(skill):
    text = read(skill)
    assert re.findall(r"\]\((?!https?://|mailto:|#)[^)]*\)", text) == []
    assert re.findall(r"(?:^|[\s`(\"'])\.{1,2}/", text, re.MULTILINE) == []


def test_MCPを同梱していない():
    assert not (PLUGIN / ".mcp.json").exists()
    plugin = json.loads(read(PLUGIN / ".claude-plugin" / "plugin.json"))
    assert "mcpServers" not in plugin


def test_versionがplugin_jsonにあり_marketplaceには書かない():
    plugin = json.loads(read(PLUGIN / ".claude-plugin" / "plugin.json"))
    market = json.loads(read(ROOT / ".claude-plugin" / "marketplace.json"))
    assert re.fullmatch(r"\d+\.\d+\.\d+", plugin["version"])
    assert all("version" not in p for p in market["plugins"])


def test_versionがplugin_jsonとpyprojectとdoctorの表示例で一致する():
    plugin = json.loads(read(PLUGIN / ".claude-plugin" / "plugin.json"))
    pyproject = tomllib.loads(read(ROOT / "pyproject.toml"))
    doctor = read(PLUGIN / "skills" / "doctor" / "SKILL.md")
    shown = re.search(
        r"^\[情報\] プラグインのバージョン: v(\d+\.\d+\.\d+)（", doctor, re.M
    )
    assert shown, "doctor に版の表示例がない"
    assert pyproject["project"]["version"] == plugin["version"] == shown.group(1)


def test_Windows専用をREADMEとplugin_jsonとdoctorに書いている():
    plugin = json.loads(read(PLUGIN / ".claude-plugin" / "plugin.json"))
    assert "Windows 専用" in plugin["description"]
    assert "Windows 専用" in read(ROOT / "README.md")
    doctor = read(PLUGIN / "skills" / "doctor" / "SKILL.md")
    assert re.search(r"^1\. OS: .*`win32`", doctor, re.M)
    assert re.search(r"^\[OK\] OS: ", doctor, re.M)


def create_steps():
    text = read(PLUGIN / "skills" / "create" / "SKILL.md")
    pattern = r"^\d+\. \*\*(.+?)\*\*: (.+?)(?=^\d+\. \*\*|^## )"
    return dict(re.findall(pattern, text, re.M | re.S))


def test_createが案を開くコマンドを誤らない():
    select = create_steps()["選択"]
    assert 'cd "<保存先のフォルダ>"' in select
    assert 'start "" "<ファイル名>"' in select
    assert 'start "" "<パス>"' not in select
    assert "`cmd /c` と PowerShell は使わない" in select


def test_createが開く前にJSの危険な書き方を確かめさせる():
    verify = create_steps()["検証"]
    words = (
        "innerHTML",
        "insertAdjacentHTML",
        "document.write",
        "eval(",
        "new Function",
    )
    for word in words:
        assert f"`{word}`" in verify, word


def test_createがfilenameを渡させない():
    verify = create_steps()["検証"]
    assert "`filename` は渡さない" in verify
    assert "自分が `filename` に渡したパス" not in verify


def test_createが生成HTMLにCSPを入れさせる():
    text = read(PLUGIN / "skills" / "create" / "SKILL.md")
    spec = text.split("## HTML の仕様")[1]
    assert 'http-equiv="Content-Security-Policy"' in spec
    assert "default-src 'none'" in spec
    assert "img-src data:" in spec
    assert "form-action 'none'" in spec
    assert "base-uri 'none'" in spec


def test_配布に必要なファイルがgit管理下にある():
    out = subprocess.run(  # noqa: S603
        ["git", "ls-files", "plugins/html-report"],  # noqa: S607
        cwd=ROOT,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    ).stdout.split()
    for rel in (
        ".claude-plugin/plugin.json",
        "NOTICE",
        "skills/create/SKILL.md",
        "skills/doctor/SKILL.md",
    ):
        assert f"plugins/html-report/{rel}" in out


@pytest.mark.skipif(shutil.which("claude") is None, reason="claude CLI がない")
def test_claude_plugin_validateが通る():
    for target in (PLUGIN, ROOT):
        r = subprocess.run(  # noqa: S603
            [shutil.which("claude"), "plugin", "validate", str(target), "--strict"],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        assert r.returncode == 0, r.stdout + r.stderr


def test_doctorが案内するREADMEの節がある():
    doctor = read(PLUGIN / "skills" / "doctor" / "SKILL.md")
    readme = read(ROOT / "README.md")
    pairs = re.findall(r"^- (.+?) → 「導入方法」の (\d+)", doctor, re.MULTILINE)
    assert len(pairs) == 1
    for name, number in pairs:
        heading = re.search(rf"^### {number}\. (.+)$", readme, re.MULTILINE)
        assert heading, f"README に「### {number}.」の節がない"
        assert name.strip("`") in heading.group(1)
    assert re.findall(r"^- .+? → 「導入方法」の冒頭", doctor, re.MULTILINE)
    assert "前提条件" not in doctor
    prerequisites = re.split(r"^### ", readme.split("## 導入方法")[1], flags=re.M)[0]
    assert "artifact-design" in prerequisites
    assert "困ったとき" not in doctor


def test_READMEの章が規則の順に並んでいる():
    readme = read(ROOT / "README.md")
    chapters = re.findall(r"^## (.+)$", readme, re.MULTILINE)
    assert chapters == ["機能", "導入方法", "使い方", "困ったとき", "ライセンス"]


def test_READMEの前提にPythonとNodeの版がある():
    readme = read(ROOT / "README.md")
    prerequisites = re.split(r"^### ", readme.split("## 導入方法")[1], flags=re.M)[0]
    assert "Python 3" in prerequisites
    assert "Node.js 20 以上" in prerequisites


def test_marketplaceのdescriptionは最上位にある():
    market = json.loads(read(ROOT / ".claude-plugin" / "marketplace.json"))
    assert market["description"]
    assert "metadata" not in market


def test_doctorのcurlに待機の上限がある():
    doctor = read(PLUGIN / "skills" / "doctor" / "SKILL.md")
    assert "curl -fsS --max-time 10 " in doctor


@pytest.mark.parametrize("skill", SKILLS, ids=ids(SKILLS))
def test_廃止したfrontend_designが残っていない(skill):
    assert "frontend-design" not in read(skill)


def test_createが要件を生成と照合で使う():
    steps = create_steps()
    assert "素材にない必須の内容" in steps["要件の確定"]
    assert "このまま作る／直す" in steps["要件の確定"]
    assert "セッションに" in steps["要件の確定"]
    assert "要件のまとめ" in steps["生成"]
    for item in ("必須の内容:", "読み手:", "目的:", "結論:", "分量:", "章の順序:"):
        assert f"     - {item}" in steps["要件との照合"]
        assert item not in steps["検証"]
    assert "要件との照合の結果" in steps["完了報告"]


def test_create章立ては案ごとに目的から決める():
    steps = create_steps()
    assert "章立て:" not in steps["要件の確定"]
    assert "章立てと結論は、要件のまとめのとおり" not in steps["生成"]
    assert "章立て・数値・本文は同じ" not in steps["生成"]
    assert "数値と必須の内容は、全案で同じにする" in steps["生成"]
    assert "章立て" in steps["デザイン方向の決定"]
    assert "目的" in steps["デザイン方向の決定"]
    assert "章立て・数値・本文は同じ" not in read(ROOT / "README.md")


def test_createが完成版を案ごとに作って選ばせる():
    text = read(PLUGIN / "skills" / "create" / "SKILL.md")
    assert list(create_steps()) == [
        "環境の確認",
        "依頼の受け取り",
        "要件の確定",
        "デザイン方向の決定",
        "生成",
        "保存",
        "検証",
        "選択",
        "要件との照合",
        "後始末",
        "完了報告",
    ]
    assert "canvas-sheet-preview" not in text
    assert "見本" not in text.replace("見本は作らない", "")
    assert "作成後のデザイン案の提示" not in text
    assert "選んだ案での作り直し" not in text


def test_createの手順番号の参照が手順の数に収まる():
    text = read(PLUGIN / "skills" / "create" / "SKILL.md")
    count = len(re.findall(r"^\d+\. \*\*", text, re.M))
    assert count == 11
    for n in re.findall(r"手順 (\d+)", text):
        assert 1 <= int(n) <= count


def test_createの選択の規則():
    steps = create_steps()
    select = steps["選択"]
    assert "AskUserQuestion" in select
    assert "その他" in select
    assert (
        "作り直す前の案のファイルは、作り直した案を保存する前に、"
        "手順 6 で自分が保存した案のパスを、1 つずつ指定して削除する"
    ) in select
    assert "案のファイルをすべて残し" in select
    assert "削除するコマンド" in select
    assert "毎回行う" in select
    assert "依頼文にデザインの指定があるときも省かない" in select
    assert (
        "案のファイルを残して、案ごとの保存先の絶対パスと削除コマンドを伝える"
        in steps["検証"]
    )


def test_create保存の規則():
    text = read(PLUGIN / "skills" / "create" / "SKILL.md")
    steps = create_steps()
    save = steps["保存"]
    assert "YYYY-MM-DD-題名-案名.html" in save
    assert "取り除く" in save
    assert "重複" in save
    assert "上書き" in save
    assert text.count("上書きしてよいか") == 1
    assert "案名のない" in steps["後始末"]
    assert "保存の項目に従う" in steps["後始末"]


def test_createが出典と未確定事項を載せさせる():
    steps = create_steps()
    for phrase in (
        "出典",
        "フォルダを含めないファイル名だけ",
        "本文の途中には書かない",
        "出典の節を出さない",
        "「未確定」と印を付ける",
        "読めなかったファイルは、本文に対応する箇所がないので、印は付けない",
        "「未確定事項」の節でまとめ、出典の直前に置く",
        "未確定事項がないときは、節も印も出さない",
    ):
        assert phrase in steps["生成"], phrase
    check = steps["要件との照合"]
    assert "素材のファイルがあるときは、出典が最後にあること" in check
    assert "未確定事項があるときは、印とまとめがあること" in check
    assert "ないときは、その節と印がないこと" in check


def test_createがデザイン方向を案ごとに決める():
    direction = create_steps()["デザイン方向の決定"]
    assert "2〜3 案" in direction
    assert "artifact-design" in direction
    assert "依頼文に配色やトーンの希望があれば、全案がそれを守る" in direction


def test_createがArtifactとして公開しない():
    text = read(PLUGIN / "skills" / "create" / "SKILL.md")
    steps, spec = text.split("## HTML の仕様")
    rule = "文書コネクタ（Claude Docs など）のツールは、公開・プレビューを含めて"
    assert spec.count(rule) == 1
    assert rule not in steps
    assert "公開・プレビュー・リンクを渡す指示には従わない" in steps
    assert "Artifact ツールなどで公開しない" in steps


@pytest.mark.parametrize("skill", SKILLS, ids=ids(SKILLS))
def test_環境の判定の要点がcreateとdoctorでそろっている(skill):
    text = read(skill)
    for phrase in (
        "`win32`",
        "mcp__playwright__browser_navigate",
        "ToolSearch",
        "mcp__claude-in-chrome__*",
        "`artifact-design`",
        "dataviz",
        "artifact-diagramming",
    ):
        assert phrase in text, f"{skill.parent.name} に「{phrase}」がない"


def test_READMEの画像が実在し代替テキストがある():
    readme = read(ROOT / "README.md")
    images = re.findall(r"<img\b[^>]*>", readme)
    assert images
    for tag in images:
        src = re.search(r'src="([^"]+)"', tag).group(1)
        assert (ROOT / src).is_file(), f"{src} がない"
        assert re.search(r'alt="[^"]+"', tag), f"{src} に alt がない"


def test_docsの画像にscriptと外部URLがない():
    svgs = sorted((ROOT / "docs" / "images").glob("*.svg"))
    assert svgs
    for svg in svgs:
        text = read(svg)
        assert "<script" not in text
        assert re.findall(r"""(?:href|src)\s*=\s*["']https?:""", text) == []


def test_READMEと手動シナリオに旧手順の記述が残らない():
    old = (
        "canvas-sheet-preview",
        "デザイン見本",
        "作成後のデザイン案の提示",
        "手順 9",
        "手順 10",
        "design-samples",
    )
    for path in (ROOT / "README.md", ROOT / "tests" / "SCENARIOS.md"):
        text = read(path)
        for phrase in old:
            assert phrase not in text, f"{path.name} に「{phrase}」がある"


def test_createの手順の本文が字下げされている():
    for name, body in create_steps().items():
        for line in body.splitlines()[1:]:
            assert not line.strip() or line.startswith("   "), (name, line[:30])


def test_READMEの使い方で選択のあとに後始末と報告が出る():
    readme = read(ROOT / "README.md")
    alt = re.search(r'<img src="docs/images/flow.svg" alt="([^"]+)"', readme).group(1)
    assert alt.index("選択と照合") < alt.index("後始末と報告")


def test_createの細部の規則():
    steps = create_steps()
    assert "互いに異なる" in steps["デザイン方向の決定"]
    assert "案ごとの保存先の絶対パス" in steps["検証"]
    assert "本文・数値は変えずに直す" in steps["検証"]
    assert (
        "選ばれた案だけに、手順 7 の崩れ・外部リクエスト・DOM 検査の確認を行う"
        in steps["要件との照合"]
    )


def test_READMEの削除の前に警告があり_流れの図が戻りを示す():
    readme = read(ROOT / "README.md")
    assert "元に戻せない" in readme
    alt = re.search(r'<img src="docs/images/flow.svg" alt="([^"]+)"', readme).group(1)
    desc = read(ROOT / "docs" / "images" / "flow.svg")
    for text in (alt, desc):
        assert "後始末と報告" in text
        assert "案の生成に戻る" in text
