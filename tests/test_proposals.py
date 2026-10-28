from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from sdd_cli import _proposals
from sdd_cli.cli import cmd_proposals

# Trimmed from the real P1 file: out-of-order IDs, a `## Resolvidas` section
# that is not an entry, and a multi-line "Fase afetada".
P1_FILE = """\
# Propostas de melhoria do kit

## Como registrar

Acrescente uma entrada `## IP-NNN` por episódio.

## IP-005 — Gate sem critério
- **Data:** 2026-08-02
- **Status:** aberta
- **Fase afetada:** specify,
  plan

**Contexto (episódio real).** O gate passou sem critério objetivo.

**Proposta para o kit.** Exigir um critério por gate.

## IP-010 — Atalho do comando
- **Data:** 2026-08-09
- **Status:** contorno local

**Proposta para o kit.** Documentar o atalho.

## Resolvidas

## IP-001 — Nome do arquivo
- **Data:** 2026-07-01
- **Status:** absorvida pelo kit (4.2.0)

**Contexto (episódio real).** O nome divergia do template.
"""

P2_FILE = """\
## IP-001 — Outro atrito
- **Data:** 2026-09-01
- **Status:** proposta

**Proposta para o kit.** Algo diferente do IP-001 de P1.
"""


def _project(base: Path, name: str, proposals: str | None) -> Path:
    root = base / name
    (root / ".sdd").mkdir(parents=True)
    if proposals is not None:
        (root / ".sdd" / "improvement-proposals.md").write_text(proposals, encoding="utf-8", newline="\n")
    return root


def _snapshot(root: Path) -> dict[str, bytes]:
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


# ------------------------------------------------------------------ parse

def test_parse_reads_only_ip_headings_in_file_order():
    entries = _proposals.parse(P1_FILE)
    assert [e["id"] for e in entries] == ["IP-005", "IP-010", "IP-001"]
    assert entries[0]["title"] == "Gate sem critério"


def test_parse_entry_ends_at_next_heading_of_any_kind():
    ip010 = _proposals.parse(P1_FILE)[1]
    assert "Documentar o atalho" in ip010["body"]
    assert "Resolvidas" not in ip010["body"]
    assert "IP-001" not in ip010["body"]


def test_parse_reads_optional_fields_and_joins_wrapped_phase():
    first = _proposals.parse(P1_FILE)[0]
    assert (first["date"], first["status"]) == ("2026-08-02", "aberta")
    assert first["phase"] == "specify, plan"
    second = _proposals.parse(P1_FILE)[1]
    assert second["phase"] is None


def test_parse_never_requires_the_optional_fields():
    entries = _proposals.parse("## IP-007 — Só o cabeçalho\n\nTexto livre.\n")
    assert entries[0]["id"] == "IP-007"
    assert entries[0]["date"] is None and entries[0]["status"] is None


def test_parse_ignores_files_without_entries():
    assert _proposals.parse("# Propostas\n\n## Como registrar\n\nNada ainda.\n") == []


# ------------------------------------------------------------------ inbox

def test_inbox_dir_env_override_wins(tmp_path):
    env = {"SDD_PROPOSALS_INBOX": str(tmp_path / "caixa")}
    assert _proposals.inbox_dir(env, platform="win32") == tmp_path / "caixa"


@pytest.mark.parametrize(("platform", "env", "expected"), [
    ("win32", {"APPDATA": "C:/Users/u/AppData/Roaming"}, Path("C:/Users/u/AppData/Roaming/sdd-cli/proposals")),
    ("linux", {"XDG_DATA_HOME": "/data"}, Path("/data/sdd-cli/proposals")),
])
def test_inbox_dir_follows_platform_conventions(platform, env, expected):
    assert _proposals.inbox_dir(env, platform=platform) == expected


def test_inbox_dir_falls_back_to_home_when_nothing_is_set(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    assert _proposals.inbox_dir({}, platform="linux") == tmp_path / ".local/share/sdd-cli/proposals"
    assert _proposals.inbox_dir({}, platform="darwin") == (
        tmp_path / "Library/Application Support/sdd-cli/proposals")


# ---------------------------------------------------------------- collect

def test_collect_writes_one_file_per_entry_named_by_project_and_id(tmp_path):
    p1 = _project(tmp_path, "P1", P1_FILE)
    p2 = _project(tmp_path, "P2", P2_FILE)
    inbox = tmp_path / "inbox"
    result = _proposals.collect([p1, p2], inbox)
    assert sorted(f.name for f in inbox.iterdir()) == [
        "P1-IP-001.md", "P1-IP-005.md", "P1-IP-010.md", "P2-IP-001.md"]
    assert result["created"] == 4 and result["updated"] == 0 and result["unchanged"] == 0
    assert "Algo diferente" in (inbox / "P2-IP-001.md").read_text(encoding="utf-8")
    assert "O nome divergia" in (inbox / "P1-IP-001.md").read_text(encoding="utf-8")


def test_collect_twice_changes_nothing(tmp_path):
    p1 = _project(tmp_path, "P1", P1_FILE)
    inbox = tmp_path / "inbox"
    _proposals.collect([p1], inbox)
    before = _snapshot(inbox)
    result = _proposals.collect([p1], inbox)
    assert (result["created"], result["updated"], result["unchanged"]) == (0, 0, 3)
    assert _snapshot(inbox) == before


def test_collect_turns_an_edited_entry_into_an_update(tmp_path):
    p1 = _project(tmp_path, "P1", P1_FILE)
    inbox = tmp_path / "inbox"
    _proposals.collect([p1], inbox)
    edited = P1_FILE.replace("- **Status:** contorno local",
                             "- **Status:** absorvida pelo kit (4.3.0)")
    (p1 / ".sdd" / "improvement-proposals.md").write_text(edited, encoding="utf-8", newline="\n")
    result = _proposals.collect([p1], inbox)
    assert (result["created"], result["updated"], result["unchanged"]) == (0, 1, 2)
    assert "absorvida pelo kit (4.3.0)" in (inbox / "P1-IP-010.md").read_text(encoding="utf-8")


def test_collect_keeps_an_entry_that_vanished_from_the_source(tmp_path):
    p1 = _project(tmp_path, "P1", P1_FILE)
    inbox = tmp_path / "inbox"
    _proposals.collect([p1], inbox)
    (p1 / ".sdd" / "improvement-proposals.md").write_text(P2_FILE, encoding="utf-8", newline="\n")
    _proposals.collect([p1], inbox)
    assert (inbox / "P1-IP-005.md").is_file()


def test_collect_keeps_the_first_of_a_repeated_id_and_warns(tmp_path):
    repeated = P2_FILE + "\n## IP-001 — Repetida\n\nOutro texto.\n"
    root = _project(tmp_path, "P2", repeated)
    inbox = tmp_path / "inbox"
    report = _proposals.collect([root], inbox)["projects"][0]
    assert report["entries"] == 1 and len(report["warnings"]) == 1
    assert "Outro texto" not in (inbox / "P2-IP-001.md").read_text(encoding="utf-8")


def test_collect_reports_a_project_without_the_file(tmp_path):
    bare = _project(tmp_path, "P3", None)
    result = _proposals.collect([bare], tmp_path / "inbox")
    assert result["projects"][0]["source"] is None
    assert result["created"] == 0


def test_collect_treats_the_plural_filename_as_missing(tmp_path):
    root = _project(tmp_path, "P4", None)
    (root / ".sdd" / "improvements-proposals.md").write_text(P2_FILE, encoding="utf-8")
    result = _proposals.collect([root], tmp_path / "inbox")
    assert result["projects"][0]["source"] is None
    assert not (tmp_path / "inbox").exists()


def test_collect_never_touches_the_source_project(tmp_path):
    p1 = _project(tmp_path, "P1", P1_FILE)
    before = _snapshot(p1)
    _proposals.collect([p1], tmp_path / "inbox")
    _proposals.collect([p1], tmp_path / "inbox")
    assert _snapshot(p1) == before


def test_collect_refuses_two_projects_with_the_same_folder_name(tmp_path):
    first = _project(tmp_path / "a", "app", P1_FILE)
    second = _project(tmp_path / "b", "app", P2_FILE)
    with pytest.raises(ValueError, match="same project code"):
        _proposals.collect([first, second], tmp_path / "inbox")
    assert not (tmp_path / "inbox").exists()


# ------------------------------------------------------------------- scan

def test_scan_finds_every_folder_with_sdd_and_skips_the_rest(tmp_path):
    _project(tmp_path, "P1", P1_FILE)
    _project(tmp_path, "P3", None)
    (tmp_path / "plain").mkdir()
    (tmp_path / "plain" / "notes.txt").write_text("x", encoding="utf-8")
    found = _proposals.scan(tmp_path)
    assert [p.name for p in found] == ["P1", "P3"]


# -------------------------------------------------------------------- cli

def _args(**values):
    base = {"proposals_command": "collect", "projects": [], "scan": None, "json": False}
    base.update(values)
    return types.SimpleNamespace(**base)


def test_cmd_proposals_collect_json_and_text(tmp_path, monkeypatch, capsys):
    p1 = _project(tmp_path, "P1", P1_FILE)
    monkeypatch.setenv("SDD_PROPOSALS_INBOX", str(tmp_path / "inbox"))
    cmd_proposals(_args(projects=[str(p1)], json=True))
    payload = json.loads(capsys.readouterr().out)
    assert payload["created"] == 3
    cmd_proposals(_args(projects=[str(p1)]))
    assert "3 unchanged" in capsys.readouterr().out


def test_cmd_proposals_collect_scan(tmp_path, monkeypatch, capsys):
    _project(tmp_path / "work", "P1", P1_FILE)
    _project(tmp_path / "work", "P2", P2_FILE)
    monkeypatch.setenv("SDD_PROPOSALS_INBOX", str(tmp_path / "inbox"))
    cmd_proposals(_args(scan=str(tmp_path / "work"), json=True))
    assert json.loads(capsys.readouterr().out)["created"] == 4


def test_cmd_proposals_collect_needs_a_project_or_scan(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("SDD_PROPOSALS_INBOX", str(tmp_path / "inbox"))
    with pytest.raises(SystemExit) as error:
        cmd_proposals(_args())
    assert error.value.code == 1
    assert "error:" in capsys.readouterr().err
