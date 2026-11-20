"""E-01 and E-02: `sddkit fix --slim` and `sddkit doctor --slim`.

`fix --slim` removes only the comments that are still exactly the bundled template's, keeps the
file's own line endings and leaves a copy under `.sdd/.pre-fix-backup/`. `doctor --slim` is
read-only: it prints the bytes each section costs, the long lines with the file each belongs in
and what `fix --slim` would remove.
"""
from __future__ import annotations

import json
import re
import types
from pathlib import Path

from sdd_cli import _slim
from sdd_cli._findings import describe
from sdd_cli.cli import _doctor_payload, cmd_doctor, cmd_fix
from sdd_cli.content import CONTENT_DIR


def _template() -> str:
    return (CONTENT_DIR / "sdd" / "constitution.md").read_text(encoding="utf-8").replace("\r\n", "\n")


def _template_comment() -> str:
    """One multi-line comment of the bundled template (what a fresh project carries)."""
    return max(_slim._template_comments(), key=len)


def _project(tmp_path: Path, text: str, newline: str = "\n") -> Path:
    (tmp_path / ".sdd").mkdir()
    (tmp_path / ".sdd" / "constitution.md").write_bytes(text.replace("\n", newline).encode("utf-8"))
    return tmp_path


def _fix(root: Path, capsys, **flags) -> tuple[dict, int | None]:
    values = {"path": str(root), "json": True, "dry_run": False, "slim": True}
    values.update(flags)
    code = None
    try:
        cmd_fix(types.SimpleNamespace(**values))
    except SystemExit as exit_:
        code = exit_.code
    return json.loads(capsys.readouterr().out), code


def _read(root: Path) -> bytes:
    return (root / ".sdd" / "constitution.md").read_bytes()


# ---- E-01: fix --slim ------------------------------------------------------------------------

def test_a_template_comment_is_removed_and_nothing_else(tmp_path, capsys):
    comment = _template_comment()
    root = _project(tmp_path, f"# Constitution\n\n## Settings\n\n- **Language:** en\n\n{comment}\n\n"
                              "## 1. Vision\n\nWhat the owner wrote.\n")
    result, code = _fix(root, capsys)
    assert code == 1  # a repair happened
    assert [r["kind"] for r in result["repairs"]] == ["slim_template_comments"]
    text = _read(root).decode("utf-8")
    assert comment not in text
    assert "What the owner wrote." in text and "- **Language:** en" in text
    assert "\n\n\n" not in text  # no double blank line where the comment sat


def test_an_edited_comment_stays(tmp_path, capsys):
    edited = _template_comment().replace("-->", "and the owner added this -->")
    root = _project(tmp_path, f"# Constitution\n\n## Settings\n\n{edited}\n")
    before = _read(root)
    result, code = _fix(root, capsys)
    assert result["repairs"] == [] and code is None
    assert _read(root) == before


def test_a_constitution_without_comments_has_nothing_to_do(tmp_path, capsys):
    root = _project(tmp_path, "# Constitution\n\n## 1. Vision\n\nText.\n")
    result, code = _fix(root, capsys)
    assert result["repairs"] == [] and result["status"] == 0 and code is None


def test_a_comment_inside_a_code_fence_is_not_touched(tmp_path, capsys):
    comment = _template_comment()
    text = f"# Constitution\n\n```md\n{comment}\n```\n"
    root = _project(tmp_path, text)
    result, _ = _fix(root, capsys)
    assert result["repairs"] == []
    assert _read(root).decode("utf-8") == text


def test_a_comment_that_shares_its_line_loses_only_the_comment(tmp_path, capsys):
    one_line = next(c for c in _slim._template_comments() if "\n" not in c)
    root = _project(tmp_path, f"# Constitution\n\n- **Language:** en {one_line}\n- **Next:** x\n")
    _fix(root, capsys)
    assert _read(root).decode("utf-8") == "# Constitution\n\n- **Language:** en\n- **Next:** x\n"


def test_dry_run_reports_and_writes_nothing(tmp_path, capsys):
    root = _project(tmp_path, f"# Constitution\n\n{_template_comment()}\n")
    before = _read(root)
    result, code = _fix(root, capsys, dry_run=True)
    assert result["repairs"][0]["comments"] == 1 and result["repairs"][0]["bytes"] > 0
    assert code == 1
    assert _read(root) == before
    assert not (root / ".sdd" / ".pre-fix-backup").exists()


def test_a_backup_with_the_exact_original_bytes_is_left(tmp_path, capsys):
    root = _project(tmp_path, f"# Constitution\n\n{_template_comment()}\n")
    before = _read(root)
    _fix(root, capsys)
    backups = list((root / ".sdd" / ".pre-fix-backup").glob("*/constitution.md"))
    assert len(backups) == 1 and backups[0].read_bytes() == before


def test_crlf_files_stay_crlf(tmp_path, capsys):
    root = _project(tmp_path, f"# Constitution\n\n{_template_comment()}\n\n## 1. Vision\n\nText.\n",
                    newline="\r\n")
    _fix(root, capsys)
    data = _read(root)
    assert b"\r\n" in data and not re.search(rb"(?<!\r)\n", data)


def test_a_second_run_finds_nothing(tmp_path, capsys):
    root = _project(tmp_path, f"# Constitution\n\n{_template_comment()}\n")
    _fix(root, capsys)
    result, code = _fix(root, capsys)
    assert result["repairs"] == [] and code is None


def test_slim_is_opt_in_and_not_part_of_the_default_fix(tmp_path, capsys):
    comment = _template_comment()
    root = _project(tmp_path, f"# Constitution\n\n{comment}\n")
    result, _ = _fix(root, capsys, slim=False)
    assert all(r["kind"] != "slim_template_comments" for r in result["repairs"])
    assert comment in _read(root).decode("utf-8")


def test_the_bundled_template_itself_is_not_slimmed_beyond_its_comments():
    new_text, removed = _slim.slim_text(_template())
    assert len(removed) == len(_slim._template_comments()) and "<!--" not in new_text
    assert "## 5. Stage index" in new_text and "## 7. Project decision conventions" in new_text


# ---- E-02: doctor --slim ---------------------------------------------------------------------

BIG = "x" * 700


def _big_constitution() -> str:
    return (
        "# Constitution\n\n## Settings\n\n- **Language:** en\n\n## 3. Locked structural decisions\n\n"
        f"| D-001 | decision | {BIG} |\n| D-002 | short | ok |\n\n"
        "## 4. Open questions\n\n"
        f"| Q-001 | {BIG} |\n\n"
        "## 5. Stage index (CANONICAL)\n\n"
        f"| 001 | first | done | {BIG} |\n\n"
        "## 6. Structural change history\n\n"
        f"- 2026-01-01 {BIG}\n"
    )


def test_the_plan_lists_each_long_line_with_the_file_it_belongs_in():
    plan = _slim.plan(_big_constitution())
    where = {item["section"]: item["destination"] for item in plan["long_lines"]}
    assert where == {"3. Locked structural decisions": "CHANGELOG.md",
                     "4. Open questions": None,
                     "5. Stage index (CANONICAL)": "backlog.md",
                     "6. Structural change history": "CHANGELOG.md"}
    assert all(item["bytes"] > _slim.LONG_LINE_BYTES for item in plan["long_lines"])
    assert [i["line"] for i in plan["long_lines"]] == sorted(i["line"] for i in plan["long_lines"])


def test_the_plan_costs_every_section_and_names_the_limit():
    plan = _slim.plan(_big_constitution())
    assert [s["heading"] for s in plan["sections"]][-1] == "6. Structural change history"
    assert plan["limit"] == 24 * 1024 and plan["over_by"] == 0
    assert plan["bytes"] == len(_big_constitution().encode("utf-8"))


def test_the_plan_counts_what_fix_slim_would_remove():
    text = _big_constitution() + f"\n{_template_comment()}\n"
    plan = _slim.plan(text)
    assert plan["template_comments"]["count"] == 1
    assert plan["template_comments"]["bytes"] == _slim.recoverable_bytes(text)


def test_doctor_slim_is_read_only_and_prints_the_plan(tmp_path, capsys):
    root = _project(tmp_path, _big_constitution())
    before = _read(root)
    cmd_doctor(types.SimpleNamespace(path=str(root), json=False, slim=True))
    out = capsys.readouterr().out
    assert "where the bytes are" in out and "CHANGELOG.md" in out and "backlog.md" in out
    assert "decide with the owner" in out and "sddkit fix --slim --dry-run" in out
    assert _read(root) == before
    assert not (root / ".sdd" / ".pre-fix-backup").exists()


def test_doctor_slim_json_has_the_same_content(tmp_path, capsys):
    root = _project(tmp_path, _big_constitution())
    cmd_doctor(types.SimpleNamespace(path=str(root), json=True, slim=True))
    payload = json.loads(capsys.readouterr().out)
    assert payload["mode"] == "slim" and len(payload["long_lines"]) == 4
    assert payload["instruction"] == _slim.INSTRUCTION


def test_the_cold_note_says_the_limit_the_sections_and_what_slim_recovers(tmp_path):
    body = "\n".join(f"| {i} | {'y' * 400} |" for i in range(80))
    root = _project(tmp_path, f"# Constitution\n\n## Settings\n\n{_template_comment()}\n\n## 1. Vision\n\n"
                              f"## 3. Locked structural decisions\n\n{body}\n")
    finding = next(f for f in _doctor_payload(root)["findings"]
                   if f["code"] == "cold_file_oversized" and f["path"] == ".sdd/constitution.md")
    assert finding["limit"] == 24 * 1024 and finding["slim_bytes"] > 0 and finding["severity"] == "note"
    message, hint = describe(finding)
    assert "limit 24576" in message and "3. Locked structural decisions" in message
    assert "sddkit doctor --slim" in hint and f"{finding['slim_bytes']} B" in hint
