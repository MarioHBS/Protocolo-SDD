"""K-10: a `?` inside code is not accent loss, and the doctor says where each hit is.

P11 (IP-003): the optional `?` of a file-extension regex, in backticks, came back as `accent-loss`.
The report gave only a file name and a count, so the agent hunted for the line, picked the wrong
character and declared the warning reviewed.
"""

from __future__ import annotations

import types
from pathlib import Path

import pytest

from sdd_cli import _mojibake
from sdd_cli.cli import cmd_doctor


@pytest.mark.parametrize("raw", [
    b"Images match `\\.(jpe?g|png)$`.\n",
    b"```js\nconst re = /https?s/;\n```\n",
    "Extensões: ``jpe?g`` apenas.\n".encode(),
])
def test_a_question_mark_in_code_is_not_accent_loss(tmp_path, raw):
    path = tmp_path / "a.md"
    path.write_bytes(raw)
    assert _mojibake.scan_file(path).v1 == []


@pytest.mark.parametrize("raw,expected", [
    (b"A decis?o `jpe?g` foi tomada.\n", 1),
    (b"Lone ` backtick: decis?o\n", 1),
    (b"```\nunclosed fence\ndecis?o\n", 1),
])
def test_prose_around_code_still_counts(tmp_path, raw, expected):
    path = tmp_path / "a.md"
    path.write_bytes(raw)
    assert len(_mojibake.scan_file(path).v1) == expected


def test_the_hit_keeps_its_byte_position_after_accented_text(tmp_path):
    path = tmp_path / "a.md"
    path.write_bytes("Ação à vontade, Å `x?y`.\nA decis?o.\n".encode())
    (hit,) = _mojibake.scan_file(path).v1
    raw = path.read_bytes()
    assert raw[hit.offset:hit.offset + 3] == b"s?o" and hit.line == 2


def test_json_is_not_read_as_markdown(tmp_path):
    path = tmp_path / "a.json"
    path.write_bytes(b'{"x": "`decis?o`"}\n')
    assert len(_mojibake.scan_file(path).v1) == 1


def test_double_encoding_is_reported_even_in_code(tmp_path):
    path = tmp_path / "a.md"
    path.write_bytes("`ç`".encode().decode("latin-1").encode())
    assert len(_mojibake.scan_file(path).v2) == 1


def _doctor(root: Path, capsys, **flags) -> str:
    values = {"path": str(root), "json": False, "slim": False, "all": False}
    values.update(flags)
    try:
        cmd_doctor(types.SimpleNamespace(**values))
    except SystemExit:
        pass
    return capsys.readouterr().out


def _project(tmp_path: Path, lines: int) -> Path:
    stage = tmp_path / ".sdd" / "stages" / "001-first"
    stage.mkdir(parents=True)
    (tmp_path / ".sdd" / "constitution.md").write_text("## Settings\n\n- **Language:** pt-BR\n",
                                                       encoding="utf-8", newline="\n")
    (stage / "spec.md").write_text("# Spec\n\n" + "A decis?o.\n" * lines, encoding="utf-8", newline="\n")
    return tmp_path


def test_a_few_hits_are_listed_with_line_and_column_without_all(tmp_path, capsys):
    out = _doctor(_project(tmp_path, 2), capsys)
    assert "3:" in out and "4:" in out and "decis?o" in out
    assert "doctor --all" not in out


def test_many_hits_point_at_all(tmp_path, capsys):
    root = _project(tmp_path, 11)
    out = _doctor(root, capsys)
    assert "decis?o" not in out and "doctor --all lists each line" in out
    full = _doctor(root, capsys, all=True)
    assert "13:" in full and "doctor --all lists each line" not in full
