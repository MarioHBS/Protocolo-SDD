"""F-01, F-02, F-03: the kit writes LF into projects even when the package holds CRLF.

A Windows checkout with ``core.autocrlf`` turns every file of ``content/`` into CRLF, the package is
built from that tree, and ``init`` and ``update`` used to copy those bytes into projects whose
``.gitattributes`` says ``eol=lf``. The doctor then said "clean" while ``fix --eol`` would rewrite
files.
"""
from __future__ import annotations

import json
import shutil
import types
from pathlib import Path

import pytest
from test_update import _run, _seed_project

import sdd_cli.cli as cli
from sdd_cli.cli import _doctor_payload, cmd_fix, cmd_init
from sdd_cli.content import CONTENT_DIR

TEXT = {".md", ".json", ".txt", ".yml", ".yaml", ".toml", ".sh", ".html"}


@pytest.fixture
def crlf_kit(tmp_path, monkeypatch) -> Path:
    """A copy of the bundled kit with every text file in CRLF, as a Windows build would carry."""
    dst = tmp_path / "crlf-content"
    shutil.copytree(CONTENT_DIR, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for path in dst.rglob("*"):
        if path.is_file() and path.suffix.lower() in TEXT:
            path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    monkeypatch.setattr(cli, "CONTENT_DIR", dst)
    return dst


def _crlf_files(root: Path) -> list[str]:
    found = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and ".git" not in path.parts and path.suffix.lower() in TEXT | {""}:
            try:
                if b"\r\n" in path.read_bytes():
                    found.append(str(path.relative_to(root)))
            except OSError:
                pass
    return found


def _init_args(path: Path) -> types.SimpleNamespace:
    return types.SimpleNamespace(path=str(path), provider=["claude"], language="pt-BR", estimation=False,
                                 docs=False, tracks=False, edd=False, dashboard_ui="rich", force=False,
                                 yes=True)


def test_the_fixture_really_carries_crlf(crlf_kit):
    assert b"\r\n" in (crlf_kit / "sdd" / "README.md").read_bytes()


def test_init_from_a_crlf_package_writes_lf(tmp_path, crlf_kit):
    project = tmp_path / "project"
    project.mkdir()
    cmd_init(_init_args(project))
    assert _crlf_files(project) == []
    assert (project / ".gitattributes").is_file()


def test_update_from_a_crlf_package_writes_lf(tmp_path, crlf_kit, capsys):
    project = _seed_project(tmp_path / "p", "v4.0.0", stale_readme=True)
    out, _ = _run(capsys, project)
    assert "README.md" in out  # the file the update rewrote
    assert b"\r\n" not in (project / ".sdd" / "README.md").read_bytes()


def test_a_crlf_package_does_not_make_an_intact_file_look_edited(tmp_path, crlf_kit, capsys):
    project = _seed_project(tmp_path / "p", "v4.0.0", stale_readme=True)
    _run(capsys, project)
    findings = [f["code"] for f in _doctor_payload(project)["findings"]]
    assert "managed_file_edited" not in findings and "manifest_eol_drift" not in findings


def test_a_binary_or_non_utf8_file_is_copied_as_it_is(tmp_path):
    src = tmp_path / "a.md"
    src.write_bytes(b"caf\xe9\r\nline\r\n")  # not UTF-8
    dst = tmp_path / "b.md"
    cli._install_file(src, dst)
    assert dst.read_bytes() == src.read_bytes()


def test_the_repository_pins_lf_for_what_it_ships():
    attributes = (Path(__file__).resolve().parents[1] / ".gitattributes").read_text(encoding="utf-8")
    assert "eol=lf" in attributes


# ---- F-02: the doctor says so, and fix --eol leaves the backups alone ----------------------------

def _crlf_project(tmp_path: Path) -> Path:
    project = _seed_project(tmp_path, "v4.9.0")
    readme = project / ".sdd" / "README.md"
    readme.write_bytes(readme.read_bytes().replace(b"\n", b"\r\n"))
    return project


def test_the_doctor_notes_managed_files_in_crlf(tmp_path):
    project = _crlf_project(tmp_path)
    found = [f for f in _doctor_payload(project)["findings"] if f["code"] == "eol_crlf"]
    assert len(found) == 1 and found[0]["severity"] == "note" and found[0]["count"] >= 1
    assert _doctor_payload(project)["status"] == 0


def test_the_doctor_is_quiet_when_everything_is_lf(tmp_path):
    project = _seed_project(tmp_path, "v4.9.0")
    for path in (project / ".sdd").rglob("*"):  # the seed copies this checkout, which may be CRLF
        if path.is_file() and path.suffix.lower() in TEXT:
            path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n"))
    assert [f for f in _doctor_payload(project)["findings"] if f["code"] == "eol_crlf"] == []


def _fix_eol(root: Path, capsys, dry_run: bool) -> dict:
    try:
        cmd_fix(types.SimpleNamespace(path=str(root), json=True, dry_run=dry_run, eol=True))
    except SystemExit:
        pass
    return json.loads(capsys.readouterr().out)


def test_fix_eol_repairs_what_the_doctor_notes(tmp_path, capsys):
    project = _crlf_project(tmp_path)
    result = _fix_eol(project, capsys, dry_run=False)
    assert any(r["kind"] == "encoding_eol" for r in result["repairs"])
    assert [f for f in _doctor_payload(project)["findings"] if f["code"] == "eol_crlf"] == []


@pytest.mark.parametrize("folder", [".pre-fix-backup", ".pre-migrate-backup"])
def test_fix_eol_leaves_the_kit_backups_alone(tmp_path, capsys, folder):
    project = _seed_project(tmp_path, "v4.9.0")
    backup = project / ".sdd" / folder / "20260101-000000" / "constitution.md"
    backup.parent.mkdir(parents=True)
    backup.write_bytes(b"# old\r\ntext\r\n")
    result = _fix_eol(project, capsys, dry_run=False)
    assert all(folder not in r["path"] for r in result["repairs"])
    assert backup.read_bytes() == b"# old\r\ntext\r\n"
