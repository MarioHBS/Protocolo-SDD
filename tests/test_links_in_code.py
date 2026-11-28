"""K-09: `file:///` written as code, or with no target, is not an absolute link.

P11 (IP-002): the constitution's own guidance says not to use `file:///`, in backticks. The doctor
warned and pointed at `fix --links`, which found nothing to repair, so the warning never left.
"""

from __future__ import annotations

import types
from pathlib import Path

import pytest

from sdd_cli._markdown import mask_code
from sdd_cli.cli import _doctor_payload, cmd_fix


def _project(tmp_path: Path, body: str) -> Path:
    (tmp_path / ".sdd").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".sdd" / "constitution.md").write_text(
        "## Settings\n\n- **Language:** en\n\n## 2. Notes\n\n" + body, encoding="utf-8", newline="\n")
    return tmp_path


def _hits(root: Path) -> list[int]:
    return [f["line"] for f in _doctor_payload(root)["findings"] if f["code"] == "abs_file_links"]


def _fix_links(root: Path, capsys) -> None:
    try:
        cmd_fix(types.SimpleNamespace(path=str(root), json=False, dry_run=False, links=True, mojibake=False,
                                      eol=False, features=False, gitignore=False, manifest=False,
                                      weight=False, slim=False))
    except SystemExit:
        pass
    capsys.readouterr()


@pytest.mark.parametrize("body", [
    "<!-- Never write `file:///` links. -->\n",
    "Never write file:/// links.\n",
    "Example: `file:///C:/x/.sdd/stages/001` is wrong.\n",
    "```text\nfile:///C:/x/.sdd/stages/001\n```\n",
    "A span that wraps `like\nfile:///C:/x/y` is still code.\n",
    "| Rule | ``file:///C:/x`` is wrong |\n",
])
def test_text_about_the_scheme_is_not_a_link(tmp_path, body):
    assert _hits(_project(tmp_path, body)) == []


@pytest.mark.parametrize("body,line", [
    ("See [spec](file:///C:/x/.sdd/stages/001/spec.md).\n", 7),
    ("A lone ` backtick, then file:///C:/x/y\n", 7),
    ("```\nan open fence\nfile:///C:/x/y\n", 9),
    ("| a ` | b |\n| [x](file:///C:/x/y) ` | c |\n", 8),
])
def test_a_real_link_is_still_reported_with_its_line(tmp_path, body, line):
    assert _hits(_project(tmp_path, body)) == [line]


def test_fix_rewrites_the_link_and_leaves_the_code_alone(tmp_path, capsys):
    target = (tmp_path / ".sdd" / "stages" / "001-first" / "spec.md").resolve().as_posix()
    link = f"file:///{target.lstrip('/')}"
    root = _project(tmp_path, f"Never `{link}`.\n\n[spec]({link})\n")
    _fix_links(root, capsys)
    text = (root / ".sdd" / "constitution.md").read_text(encoding="utf-8")
    assert f"Never `{link}`." in text and "[spec](stages/001-first/spec.md)" in text
    assert _hits(root) == []


def test_masking_keeps_length_and_newlines():
    text = "a `b?c` d\n\n```py\nx?y\n```\ne\r\n"
    masked = mask_code(text)
    assert len(masked) == len(text) and masked.count("\n") == text.count("\n")
    assert "?" not in masked and masked.startswith("a ") and masked.endswith("e\r\n")
