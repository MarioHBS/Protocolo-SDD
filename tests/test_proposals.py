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
    assert sorted(f.name for f in inbox.glob("*.md")) == [
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


# ------------------------------------------------------------ anonymous codes

def test_collect_gives_each_project_with_entries_a_stable_anonymous_code(tmp_path):
    p1 = _project(tmp_path, "alpha", P1_FILE)
    p2 = _project(tmp_path, "beta", P2_FILE)
    p3 = _project(tmp_path, "gamma", None)
    inbox = tmp_path / "inbox"
    _proposals.collect([p1, p3], inbox)
    assert _proposals.read_codes(inbox) == {"alpha": "P1"}
    _proposals.collect([p2, p1], inbox)
    assert _proposals.read_codes(inbox) == {"alpha": "P1", "beta": "P2"}


def test_collect_does_not_rewrite_the_codes_when_nothing_is_new(tmp_path):
    p1 = _project(tmp_path, "alpha", P1_FILE)
    inbox = tmp_path / "inbox"
    _proposals.collect([p1], inbox)
    before = (inbox / ".codes.json").stat().st_mtime_ns
    _proposals.collect([p1], inbox)
    assert (inbox / ".codes.json").stat().st_mtime_ns == before


def test_aliases_keep_recorded_codes_and_number_unknown_projects_without_writing(tmp_path):
    inbox = tmp_path / "inbox"
    _proposals.collect([_project(tmp_path, "alpha", P1_FILE)], inbox)
    entries = _proposals.load(inbox)
    entries.append({**entries[0], "project": "zed"})
    assert _proposals.aliases(entries, inbox) == {"alpha": "P1", "zed": "P2"}
    assert _proposals.read_codes(inbox) == {"alpha": "P1"}


def test_load_ignores_the_codes_file_and_a_corrupt_one_reads_as_empty(tmp_path):
    inbox = tmp_path / "inbox"
    _proposals.collect([_project(tmp_path, "alpha", P1_FILE)], inbox)
    (inbox / ".codes.json").write_text("{not json", encoding="utf-8")
    assert _proposals.read_codes(inbox) == {}
    assert len(_proposals.load(inbox)) == 3


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


# ------------------------------------------------------------ list / show

@pytest.mark.parametrize(("status", "word"), [
    ("aberta", "aberta"),
    ("Contorno local (até a 4.5)", "contorno local"),
    ("absorvida pelo kit (4.2.0)", "absorvida pelo kit"),
    ("proposta", "proposta"),
    ("em análise (semana que vem)", "em"),
    (None, ""),
])
def test_status_keyword_reads_the_leading_word_without_a_closed_list(status, word):
    assert _proposals.status_keyword(status) == word


@pytest.fixture
def collected(tmp_path, monkeypatch):
    inbox = tmp_path / "inbox"
    monkeypatch.setenv("SDD_PROPOSALS_INBOX", str(inbox))
    _proposals.collect([_project(tmp_path, "P1", P1_FILE), _project(tmp_path, "P2", P2_FILE)], inbox)
    return inbox


def _view(**values):
    return _args(**{"proposals_command": "list", "all": False, "id": None, **values})


def test_load_orders_by_project_then_numeric_id(collected):
    assert [e["key"] for e in _proposals.load(collected)] == [
        "P1-IP-001", "P1-IP-005", "P1-IP-010", "P2-IP-001"]


def test_load_skips_files_that_are_not_inbox_entries(collected):
    (collected / "notes.md").write_text("# not ours\n\n## IP-009 — stray\n", encoding="utf-8")
    assert len(_proposals.load(collected)) == 4


def test_load_of_a_missing_inbox_is_empty(tmp_path):
    assert _proposals.load(tmp_path / "nowhere") == []


def test_list_hides_absorbed_by_default_and_all_shows_them(collected, capsys):
    cmd_proposals(_view())
    out = capsys.readouterr().out
    assert "P1-IP-005" in out and "P1-IP-010" in out and "P2-IP-001" in out
    assert "P1-IP-001" not in out
    assert "1 absorbed by the kit hidden" in out
    cmd_proposals(_view(all=True))
    assert "P1-IP-001" in capsys.readouterr().out


def test_list_json_carries_state_and_total(collected, capsys):
    cmd_proposals(_view(json=True))
    payload = json.loads(capsys.readouterr().out)
    assert payload["total"] == 4
    assert [p["key"] for p in payload["proposals"]] == ["P1-IP-005", "P1-IP-010", "P2-IP-001"]
    assert payload["proposals"][0]["state"] == "aberta"


def test_list_is_deterministic(collected, capsys):
    cmd_proposals(_view(all=True))
    first = capsys.readouterr().out
    cmd_proposals(_view(all=True))
    assert capsys.readouterr().out == first


def test_list_on_an_empty_inbox_points_at_collect(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("SDD_PROPOSALS_INBOX", str(tmp_path / "inbox"))
    cmd_proposals(_view())
    assert "sddkit proposals collect" in capsys.readouterr().out


def test_show_prints_the_full_text_of_the_qualified_id(collected, capsys):
    cmd_proposals(_view(proposals_command="show", id="p2-ip-001"))
    out = capsys.readouterr().out
    assert "Algo diferente do IP-001 de P1" in out
    assert "O nome divergia" not in out


def test_show_asks_for_the_qualified_id_when_a_bare_one_is_ambiguous(collected, capsys):
    with pytest.raises(SystemExit):
        cmd_proposals(_view(proposals_command="show", id="IP-001"))
    err = capsys.readouterr().err
    assert "P1-IP-001" in err and "P2-IP-001" in err


def test_show_accepts_a_bare_id_that_only_one_project_has(collected, capsys):
    cmd_proposals(_view(proposals_command="show", id="IP-005"))
    assert "O gate passou sem critério" in capsys.readouterr().out


def test_show_json_has_body_and_phase(collected, capsys):
    cmd_proposals(_view(proposals_command="show", id="P1-IP-005", json=True))
    payload = json.loads(capsys.readouterr().out)
    assert payload["phase"] == "specify, plan" and "Exigir um critério" in payload["body"]


def test_show_unknown_id_fails_with_a_hint(collected, capsys):
    with pytest.raises(SystemExit) as error:
        cmd_proposals(_view(proposals_command="show", id="P9-IP-001"))
    assert error.value.code == 1
    assert "no proposal P9-IP-001" in capsys.readouterr().err


# --------------------------------------------- projects without the file (C-05)

def test_scan_notes_each_project_without_the_file_and_still_succeeds(tmp_path, monkeypatch, capsys):
    _project(tmp_path / "work", "P1", P1_FILE)
    _project(tmp_path / "work", "P3", None)
    typo = _project(tmp_path / "work", "P4", None)
    (typo / ".sdd" / "improvements-proposals.md").write_text(P2_FILE, encoding="utf-8")
    monkeypatch.setenv("SDD_PROPOSALS_INBOX", str(tmp_path / "inbox"))
    cmd_proposals(_args(scan=str(tmp_path / "work")))
    out = capsys.readouterr().out
    assert "note: P3: no .sdd/improvement-proposals.md" in out
    assert "note: P4: no .sdd/improvement-proposals.md" in out
    assert "P1: 3 entries" in out and "error" not in out
    assert not (tmp_path / "inbox" / "P4-IP-001.md").exists()


def test_json_carries_the_note_only_for_projects_without_the_file(tmp_path, monkeypatch, capsys):
    _project(tmp_path / "work", "P1", P1_FILE)
    _project(tmp_path / "work", "P3", None)
    monkeypatch.setenv("SDD_PROPOSALS_INBOX", str(tmp_path / "inbox"))
    cmd_proposals(_args(scan=str(tmp_path / "work"), json=True))
    reports = {r["project"]: r for r in json.loads(capsys.readouterr().out)["projects"]}
    assert reports["P1"]["note"] is None
    assert "no .sdd/improvement-proposals.md" in reports["P3"]["note"]
