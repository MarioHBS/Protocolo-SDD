"""The spec-lock gate (S-01 to S-05): the `sdd-audit` skill and agent, `audit.md`, the
`Locked-by-audit:` line and what `sddkit doctor` can tell from files alone.

Only open stages are ever looked at: a closed stage (it has a `report.md`) is history.
"""
from __future__ import annotations

import json
import types
from pathlib import Path

import pytest
from test_update import _seed_project

from sdd_cli import _index_checks as ix
from sdd_cli import providers
from sdd_cli.cli import _doctor_payload, cmd_init, cmd_update
from sdd_cli.content import CONTENT_DIR, KIT_VERSION

_SDD = CONTENT_DIR / "sdd"

CONSTITUTION = """# Constitution

## 1. Settings

- **Language:** en

## 5. Stage index (CANONICAL)

| Stage | Slug | Status | Depends on | Weight |
|-------|------|--------|------------|--------|
| 001 | big | in progress | — | |
| 002 | small | in progress | — | light: fixes a typo |
| 003 | closed-one | done | — | |

## 6. History
"""

SPEC = """# Spec — Stage {name}

- **Status:** {status}
- **Created:** 2026-11-13
- **Touches:**
  - paths: {paths}
{header}
---
"""

AUDIT = """# Audit — Stage 001: big

## Round 1 — 2026-11-10

- **Mode:** full
- **Verdict:** NOT READY TO LOCK
- **Counts:** BLOCKER 1 · MAJOR 1 · MINOR 0

| Id | Severity | Lens | Where | State | Pointer |
|----|----------|------|-------|-------|---------|
| F-01 | BLOCKER | 3 | spec.md §4 | fixed | rewritten |
| F-02 | MAJOR | 5 | spec.md §2 | fixed | added |

## Round 2 — 2026-11-12

- **Mode:** delta
- **Verdict:** READY TO LOCK <!-- READY TO LOCK | NOT READY TO LOCK -->
- **Counts:** BLOCKER 0 · MAJOR 0 · MINOR 1

| Id | Severity | Lens | Where | State | Pointer |
|----|----------|------|-------|-------|---------|
| F-03 | MINOR | 2 | todo.md | dismissed | owner: wording only |
"""

LINE = "- **Locked-by-audit:** round 2 · 2026-11-12 · fixed 1/1 · dismissed 1"


def _project(tmp_path: Path) -> Path:
    sdd = tmp_path / ".sdd"
    (sdd / "stages").mkdir(parents=True)
    (sdd / "constitution.md").write_text(CONSTITUTION, encoding="utf-8")
    return tmp_path


def _stage(root: Path, name: str, *, status="locked", header="", paths="`src/**`", audit=None,
           report=False) -> Path:
    stage = root / ".sdd" / "stages" / name
    stage.mkdir(parents=True)
    (stage / "spec.md").write_text(SPEC.format(name=name, status=status, header=header, paths=paths),
                                   encoding="utf-8")
    if audit is not None:
        (stage / "audit.md").write_text(audit, encoding="utf-8")
    if report:
        (stage / "report.md").write_text("# Report\n", encoding="utf-8")
    return stage


def _codes(root: Path) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for finding in _doctor_payload(root)["findings"]:
        out.setdefault(finding["code"], []).append(finding)
    return out


# ------------------------------------------------- S-01 / S-02: kit content ---

def test_the_kit_bundles_the_audit_skill_the_template_and_the_agent():
    skill = (_SDD / "skills" / "sdd-audit" / "SKILL.md").read_text(encoding="utf-8")
    assert skill.startswith("---\nname: sdd-audit\n")
    for phrase in ("READY TO LOCK", "NOT READY TO LOCK", "Locked-by-audit:", "audit-lenses.md",
                   "delta round", "read-only", "Mode: self-audit", "untested (who, when)"):
        assert phrase in skill, phrase
    assert "Ready with reservations" not in skill or "does not exist" in skill
    template = (_SDD / "templates" / "audit.template.md").read_text(encoding="utf-8")
    assert "## Round 1" in template and "| Id | Severity | Lens | Where | State | Pointer |" in template
    agent = (CONTENT_DIR / "agents" / "claude-sdd-audit.md").read_text(encoding="utf-8")
    assert agent.startswith("---\nname: sdd-audit\n") and "tools: Read, Glob, Grep, Bash" in agent
    assert "Edit" not in agent.split("---")[1] and "Write" not in agent.split("---")[1]  # read-only


def test_the_audit_skill_is_cross_cutting_and_listed_where_the_agent_looks():
    readme = (_SDD / "README.md").read_text(encoding="utf-8")
    assert "`sdd-audit`" in readme and "Five skills are **cross-cutting utilities**" in readme
    for shim in sorted((CONTENT_DIR / "shims").iterdir()):
        assert "sdd-audit" in shim.read_text(encoding="utf-8"), shim.name


def test_specify_step_six_follows_the_weight_and_asks_for_the_record():
    text = " ".join((_SDD / "skills" / "sdd-specify" / "SKILL.md").read_text(encoding="utf-8").split())
    assert "`sdd-audit`" in text and "Locked-by-audit:" in text and "`audit.md`" in text
    assert "light" in text and "basic review" in text


def test_the_spec_template_has_the_optional_line_and_the_measurements_section():
    text = (_SDD / "templates" / "spec.template.md").read_text(encoding="utf-8")
    assert "Locked-by-audit:" in text and "To measure before implementing" in text
    assert text.index("To measure before implementing") > text.index("## 6. Risks")


def test_close_copies_the_audit_numbers_to_the_report():
    text = " ".join((_SDD / "skills" / "sdd-close" / "SKILL.md").read_text(encoding="utf-8").split())
    assert "Locked-by-audit:" in text


# ------------------------------------------------------- provider agent ---

def test_only_the_claude_provider_has_an_agent():
    with_agent = [p.key for p in providers.PROVIDERS if p.agent_path]
    assert with_agent == ["claude"]
    assert (CONTENT_DIR / "agents" / providers.get("claude").agent_source).is_file()


def _init_args(path: Path) -> types.SimpleNamespace:
    return types.SimpleNamespace(path=str(path), provider=["claude"], language="en", estimation=False,
                                 docs=False, tracks=False, edd=False, dashboard_ui="rich",
                                 force=False, yes=True)


def test_init_installs_the_agent_and_records_it(tmp_path):
    cmd_init(_init_args(tmp_path))
    agent = tmp_path / ".claude" / "agents" / "sdd-audit.md"
    assert agent.is_file()
    data = json.loads((tmp_path / ".sdd" / ".sdd-manifest.json").read_text(encoding="utf-8"))
    assert ".claude/agents/sdd-audit.md" in data["managed_files"]


def test_init_never_overwrites_an_agent_of_the_owner(tmp_path):
    own = tmp_path / ".claude" / "agents" / "sdd-audit.md"
    own.parent.mkdir(parents=True)
    own.write_text("my own agent\n", encoding="utf-8")
    cmd_init(_init_args(tmp_path))
    assert own.read_text(encoding="utf-8") == "my own agent\n"
    data = json.loads((tmp_path / ".sdd" / ".sdd-manifest.json").read_text(encoding="utf-8"))
    assert ".claude/agents/sdd-audit.md" not in data["managed_files"]


def _seed_claude(tmp_path: Path, version: str) -> Path:
    root = _seed_project(tmp_path, version)
    data = json.loads((root / ".sdd" / ".sdd-manifest.json").read_text(encoding="utf-8"))
    data["providers"] = ["claude"]
    (root / ".sdd" / ".sdd-manifest.json").write_text(json.dumps(data), encoding="utf-8")
    return root


def _update(capsys, root: Path, **flags) -> str:
    values = {"path": str(root), "dry_run": False, "notes": False, "global_skill": False}
    values.update(flags)
    try:
        cmd_update(types.SimpleNamespace(**values))
    except SystemExit:
        pass
    captured = capsys.readouterr()
    return captured.out + captured.err


def test_update_adds_the_agent_and_never_touches_one_the_owner_already_has(capsys, tmp_path):
    root = _seed_claude(tmp_path / "new", "v4.5.0")
    _update(capsys, root)
    assert (root / ".claude" / "agents" / "sdd-audit.md").is_file()
    data = json.loads((root / ".sdd" / ".sdd-manifest.json").read_text(encoding="utf-8"))
    assert ".claude/agents/sdd-audit.md" in data["managed_files"]

    other = _seed_claude(tmp_path / "own", "v4.5.0")
    mine = other / ".claude" / "agents" / "sdd-audit.md"
    mine.parent.mkdir(parents=True)
    mine.write_text("owner's agent\n", encoding="utf-8")
    _update(capsys, other)
    assert mine.read_text(encoding="utf-8") == "owner's agent\n"
    data = json.loads((other / ".sdd" / ".sdd-manifest.json").read_text(encoding="utf-8"))
    assert ".claude/agents/sdd-audit.md" not in data["managed_files"]


def test_update_dry_run_does_not_write_the_agent(capsys, tmp_path):
    root = _seed_claude(tmp_path, "v4.5.0")
    out = _update(capsys, root, dry_run=True)
    assert "sdd-audit.md" in out and "(provider agent)" in out
    assert not (root / ".claude").exists()


def test_a_hand_edited_agent_is_preserved_on_update(capsys, tmp_path):
    root = _seed_claude(tmp_path, "v4.5.0")
    _update(capsys, root)
    agent = root / ".claude" / "agents" / "sdd-audit.md"
    agent.write_text(agent.read_text(encoding="utf-8") + "\nmy rule\n", encoding="utf-8")
    data = json.loads((root / ".sdd" / ".sdd-manifest.json").read_text(encoding="utf-8"))
    data["kit_version"] = "v4.5.0"
    (root / ".sdd" / ".sdd-manifest.json").write_text(json.dumps(data), encoding="utf-8")
    out = _update(capsys, root)
    assert "my rule" in agent.read_text(encoding="utf-8") and "hand-edited" in out


# --------------------------------------------- S-03: Locked-by-audit line ---

def test_a_locked_full_stage_without_the_line_is_a_note(tmp_path):
    root = _project(tmp_path)
    _stage(root, "001-big")
    finding = _codes(root)["lock_without_audit"][0]
    assert finding["stage"] == "001-big" and finding["severity"] == "note"
    assert _doctor_payload(root)["status"] == 0


def test_a_draft_stage_is_not_asked_for_the_line(tmp_path):
    root = _project(tmp_path)
    _stage(root, "001-big", status="draft")
    assert "lock_without_audit" not in _codes(root)


def test_a_light_stage_may_lock_without_the_audit(tmp_path):
    root = _project(tmp_path)
    _stage(root, "002-small")
    assert "lock_without_audit" not in _codes(root)


def test_a_closed_stage_is_never_asked_for_anything(tmp_path):
    root = _project(tmp_path)
    _stage(root, "003-closed-one", report=True)
    _stage(root, "001-big", header=LINE, audit="garbage", report=True)
    codes = _codes(root)
    assert "lock_without_audit" not in codes and "lock_audit_mismatch" not in codes


def test_a_queue_stage_weight_is_found_by_its_bare_slug(tmp_path):
    root = _project(tmp_path)
    text = (root / ".sdd" / "constitution.md").read_text(encoding="utf-8")
    text += "\n### Provisional queue\n\n| Slug | Status | Depends on | Notes | Weight |\n" \
            "|------|--------|------------|-------|--------|\n| tiny | queued | — | | light: typo |\n"
    (root / ".sdd" / "constitution.md").write_text(text, encoding="utf-8")
    _stage(root, "007-tiny")
    assert "lock_without_audit" not in _codes(root)


def test_a_line_that_agrees_with_audit_md_is_clean(tmp_path):
    root = _project(tmp_path)
    _stage(root, "001-big", header=LINE, audit=AUDIT)
    codes = _codes(root)
    assert "lock_without_audit" not in codes and "lock_audit_mismatch" not in codes


@pytest.mark.parametrize("line, fragment", [
    ("- **Locked-by-audit:** round 3 · 2026-11-12 · fixed 1/1 · dismissed 1", "round 3, audit.md has 2"),
    ("- **Locked-by-audit:** round 2 · 2026-11-12 · fixed 2/1 · dismissed 1", "fixed 2/1"),
    ("- **Locked-by-audit:** round 2 · 2026-11-12 · fixed 1/1 · dismissed 0", "dismissed"),
])
def test_a_line_that_disagrees_with_audit_md_is_a_warning(tmp_path, line, fragment):
    root = _project(tmp_path)
    _stage(root, "001-big", header=line, audit=AUDIT)
    finding = _codes(root)["lock_audit_mismatch"][0]
    assert finding["severity"] == "warn" and fragment in finding["detail"]


def test_a_line_without_audit_md_or_with_a_last_round_not_ready_is_a_warning(tmp_path):
    root = _project(tmp_path)
    _stage(root, "001-big", header=LINE)
    assert "audit.md is missing" in _codes(root)["lock_audit_mismatch"][0]["detail"]

    other = _project(tmp_path / "b")
    _stage(other, "001-big", header=LINE, audit=AUDIT.replace("READY TO LOCK <!--", "NOT READY TO LOCK <!--"))
    assert "not READY TO LOCK" in _codes(other)["lock_audit_mismatch"][0]["detail"]


def test_an_open_blocker_in_audit_md_contradicts_a_locked_stage(tmp_path):
    root = _project(tmp_path)
    audit = AUDIT.replace("| F-01 | BLOCKER | 3 | spec.md §4 | fixed |", "| F-01 | BLOCKER | 3 | spec.md §4 | open |")
    _stage(root, "001-big", header=LINE, audit=audit)
    assert "open BLOCKER or MAJOR" in _codes(root)["lock_audit_mismatch"][0]["detail"]


def test_the_template_comment_is_not_mistaken_for_a_real_line(tmp_path):
    root = _project(tmp_path)
    stage = _stage(root, "001-big")
    spec = stage / "spec.md"
    spec.write_text(spec.read_text(encoding="utf-8") + f"\n<!-- {LINE} -->\n", encoding="utf-8")
    assert "lock_without_audit" in _codes(root)


def test_a_track_stage_is_checked_too(tmp_path):
    root = _project(tmp_path)
    stage = root / ".sdd" / "tracks" / "t1" / "stages" / "010-in-track"
    stage.mkdir(parents=True)
    (stage / "spec.md").write_text(SPEC.format(name="010-in-track", status="locked", header="", paths="`x/**`"),
                                   encoding="utf-8")
    assert _codes(root)["lock_without_audit"][0]["stage"] == "010-in-track"


# ---------------------------------------------------- S-04: triggers ---

LENSES = """# Audit lenses

## Extra lenses

- Payments: webhook replay. Mentions `not/a/trigger` only as prose.

## Triggers

- `src/server/auth/**`
- Anything under `supabase/migrations/**` and the file `src/proxy.ts`
- A decision other stages will inherit (not a path, ignored by the doctor).
"""


def test_triggers_are_the_backticked_globs_under_the_triggers_heading(tmp_path):
    root = _project(tmp_path)
    (root / ".sdd" / "audit-lenses.md").write_text(LENSES, encoding="utf-8")
    assert ix.audit_triggers(root / ".sdd") == [
        "src/server/auth/**", "supabase/migrations/**", "src/proxy.ts"]
    assert ix.audit_triggers(tmp_path / "nowhere") == []


def test_a_light_stage_touching_a_trigger_path_is_a_warning(tmp_path):
    root = _project(tmp_path)
    (root / ".sdd" / "audit-lenses.md").write_text(LENSES, encoding="utf-8")
    _stage(root, "002-small", paths="`src/server/auth/session.ts`, `docs/**`")
    finding = _codes(root)["light_hits_audit_trigger"][0]
    assert finding["severity"] == "warn" and finding["trigger"] == "src/server/auth/**"
    assert finding["path"] == "src/server/auth/session.ts"


def test_a_light_stage_elsewhere_and_a_full_stage_on_a_trigger_are_fine(tmp_path):
    root = _project(tmp_path)
    (root / ".sdd" / "audit-lenses.md").write_text(LENSES, encoding="utf-8")
    _stage(root, "002-small", paths="`docs/**`, `src/ui/button.tsx`")
    _stage(root, "001-big", paths="`src/server/auth/**`", header=LINE, audit=AUDIT)
    assert "light_hits_audit_trigger" not in _codes(root)


def test_no_lenses_file_means_no_trigger_check(tmp_path):
    root = _project(tmp_path)
    _stage(root, "002-small", paths="`src/server/auth/**`")
    assert "light_hits_audit_trigger" not in _codes(root)


@pytest.mark.parametrize("a, b, overlap", [
    ("src/server/auth/**", "src/server/auth/session.ts", True),
    ("src/**", "src/server/auth/**", True),
    ("**/auth/**", "src/server/auth/**", True),
    ("src/ui/**", "src/server/**", False),
    ("docs/**", "src/proxy.ts", False),
    ("src/proxy.ts", "src/proxy.ts", True),
])
def test_path_globs_overlap_conservatively(a, b, overlap):
    assert ix._paths_overlap(a, b) is overlap


def test_the_scaffold_regex_of_the_spec_is_not_disturbed_by_the_template():
    text = (_SDD / "templates" / "spec.template.md").read_text(encoding="utf-8")
    section5 = text[text.index("## 5."):text.index("## 6.")]
    assert "To measure before implementing" not in section5


def test_the_release_notes_announce_the_gate():
    notes = (CONTENT_DIR / "RELEASE-NOTES.md").read_text(encoding="utf-8")
    assert f"## {KIT_VERSION.lstrip('v')}" in notes and "sdd-audit" in notes
