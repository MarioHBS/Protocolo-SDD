"""`sdd migrate --to v4` and `sdd update`, driven on a synthetic project shaped like the
real Antologias Biló install (kit v3.3.0, one provider, hand-written user files).

Nothing here copies client data: the project is generated from scratch.
"""

from __future__ import annotations

import hashlib
import json
import types
from pathlib import Path

import pytest

from sdd_cli import manifest
from sdd_cli.cli import cmd_migrate, cmd_update
from sdd_cli.content import CONTENT_DIR, KIT_VERSION

OLD_TEXT = "# old managed content (kit 3.3.0)\n"

USER_FILES = {
    ".sdd/constitution.md": "## Settings\n\n- **Language:** pt-BR\n- **Estimation tracking:** on\n\n"
                            "## Current state\n\n- **State:** IMPLEMENTING\n\n## 1. Vision\n\nmine\n",
    ".sdd/roadmap.md": "# my roadmap\n",
    ".sdd/CHANGELOG.md": "# my changelog\n",
    ".sdd/backlog.md": "## some-stage\n\nmy backlog\n",
    ".sdd/improvements-proposals.md": "# proposals the kit has never heard of\n",
    ".sdd/stages/001-base/spec.md": "my spec\n",
    ".sdd/stages/001-base/report.md": "my report\n",
    ".sdd/tracks/login/state.md": "my track\n",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)).replace("\\", "/"): _sha(p) for p in sorted(root.rglob("*")) if p.is_file()}


def _v33_project(root: Path, provider: str = "kilo") -> Path:
    """A project installed by kit 3.3.0: managed files with OLD content and their recorded hashes."""
    managed: dict[str, str] = {}

    def put(rel: str, text: str, record: bool) -> None:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        if record:
            managed[rel] = manifest.hash_file(path)

    put(".sdd/README.md", OLD_TEXT, True)
    for skill in ("sdd-close", "sdd-decide", "sdd-init", "sdd-reconcile", "sdd-roadmap", "sdd-specify",
                  "sdd-track", "sdd-document", "sdd-implement"):
        put(f".sdd/skills/{skill}/SKILL.md", OLD_TEXT, True)
    for template in ("spec", "todo", "report", "checklist", "roadmap"):
        put(f".sdd/templates/{template}.template.md", OLD_TEXT, True)
    put(".kilo/commands/sdd.md", OLD_TEXT, True)
    for rel, text in USER_FILES.items():
        put(rel, text, False)
    (root / ".sdd" / ".sdd-manifest.json").write_text(json.dumps({
        "kit_version": "v3.3.0", "language": "pt-BR", "providers": [provider],
        "features": {"estimation": True, "documentation": False},
        "managed_files": managed, "created_at": "2026-08-18", "updated_at": "2026-09-03"}), encoding="utf-8")
    return root


def _migrate(path: Path, **values):
    args = {"path": str(path), "to": "v4", "dry_run": False, "fix_mojibake": False, "provider": None}
    args.update(values)
    return cmd_migrate(types.SimpleNamespace(**args))


def _manifest(path: Path) -> dict:
    return json.loads((path / ".sdd" / ".sdd-manifest.json").read_text(encoding="utf-8"))


def test_dry_run_writes_nothing(tmp_path):
    _v33_project(tmp_path)
    before = _tree(tmp_path)
    _migrate(tmp_path, dry_run=True)
    assert _tree(tmp_path) == before


def test_migration_replaces_managed_files_and_never_touches_user_files(tmp_path):
    _v33_project(tmp_path)
    user_before = {rel: _sha(tmp_path / rel) for rel in USER_FILES}
    _migrate(tmp_path)

    assert {rel: _sha(tmp_path / rel) for rel in USER_FILES} == user_before
    # Compare as text: the checkout may use CRLF while installed files are always LF.
    assert (tmp_path / ".sdd" / "README.md").read_text(encoding="utf-8") == \
        (CONTENT_DIR / "sdd" / "README.md").read_text(encoding="utf-8")
    track_skill = (tmp_path / ".sdd" / "skills" / "sdd-track" / "SKILL.md").read_text(encoding="utf-8")
    assert "sdd track incorporate" in track_skill          # the 4.1 skill, not the old one
    assert (tmp_path / ".sdd" / "templates" / "cross-cutting.template.md").is_file()   # a template that is new in 4.1
    assert (tmp_path / ".sdd" / "templates" / "evals.template.md").is_file()           # EDD templates arrive too
    shim = (tmp_path / ".kilo" / "commands" / "sdd.md").read_text(encoding="utf-8")
    assert "sdd context" in shim and "linked git worktree" in shim


def test_manifest_moves_to_the_new_kit_and_keeps_what_the_owner_chose(tmp_path):
    _v33_project(tmp_path)
    _migrate(tmp_path)
    data = _manifest(tmp_path)
    assert data["kit_version"] == KIT_VERSION
    assert data["providers"] == ["kilo"]
    assert data["language"] == "pt-BR"
    assert data["features"]["estimation"] is True
    assert {"tracks", "edd"} <= set(data["features"])       # features that did not exist in 3.3.0
    assert ".sdd/skills/sdd-track/SKILL.md" in data["managed_files"]
    assert ".sdd/backlog.md" not in data["managed_files"]


def test_a_hand_edited_managed_file_is_backed_up_before_it_is_replaced(tmp_path):
    _v33_project(tmp_path)
    edited = tmp_path / ".sdd" / "skills" / "sdd-close" / "SKILL.md"
    edited.write_text("MY LOCAL TWEAK\n", encoding="utf-8")
    _migrate(tmp_path)
    backups = list((tmp_path / ".sdd" / ".pre-migrate-backup").rglob("SKILL.md"))
    assert any(b.read_text(encoding="utf-8") == "MY LOCAL TWEAK\n" for b in backups)
    assert edited.read_text(encoding="utf-8") != "MY LOCAL TWEAK\n"


def test_switching_provider_removes_only_an_untouched_old_shim(tmp_path):
    _v33_project(tmp_path)
    kit_kilo = (CONTENT_DIR / "shims" / "kilo.md").read_text(encoding="utf-8")
    (tmp_path / ".kilo" / "commands" / "sdd.md").write_text(kit_kilo, encoding="utf-8")   # byte-identical to the kit's
    _migrate(tmp_path, provider=["claude"])
    assert (tmp_path / ".claude" / "commands" / "sdd.md").is_file()
    assert not (tmp_path / ".kilo" / "commands" / "sdd.md").exists()
    assert _manifest(tmp_path)["providers"] == ["claude"]


def test_switching_provider_keeps_an_old_shim_the_owner_edited(tmp_path):
    _v33_project(tmp_path)
    (tmp_path / ".kilo" / "commands" / "sdd.md").write_text("my own kilo instructions\n", encoding="utf-8")
    _migrate(tmp_path, provider=["claude"])
    assert (tmp_path / ".kilo" / "commands" / "sdd.md").read_text(encoding="utf-8") == "my own kilo instructions\n"


def test_migrating_twice_is_a_no_op(tmp_path):
    _v33_project(tmp_path)
    _migrate(tmp_path)
    first = _tree(tmp_path)
    try:
        _migrate(tmp_path)
    except SystemExit as exc:      # "already at this version" may exit cleanly
        assert exc.code in (0, None)
    second = _tree(tmp_path)
    changed = {k for k in second if first.get(k) != second[k] and ".pre-migrate-backup" not in k}
    assert changed <= {".sdd/.sdd-manifest.json"}      # at most the manifest's updated_at moves


def test_an_unknown_target_is_refused(tmp_path):
    _v33_project(tmp_path)
    with pytest.raises(SystemExit):
        _migrate(tmp_path, to="v9")


# ------------------------------------------------------------------- update

def _project_at_4_0_0(root: Path) -> Path:
    """Install the bundled kit, then pretend it was 4.0.0 with one older managed file."""
    from sdd_cli.cli import cmd_init

    cmd_init(types.SimpleNamespace(path=str(root), provider=["claude"], language="pt-BR", estimation=False,
                                   docs=False, tracks=False, edd=True, dashboard_ui="rich", force=False, yes=True))
    data = _manifest(root)
    data["kit_version"] = "v4.0.0"
    old = root / ".sdd" / "skills" / "sdd-track" / "SKILL.md"
    old.write_text("old 4.0.0 track skill\n", encoding="utf-8", newline="\n")
    data["managed_files"][".sdd/skills/sdd-track/SKILL.md"] = manifest.hash_file(old)
    data["managed_files"].pop(".sdd/templates/cross-cutting.template.md", None)     # 4.0.0 had no such template
    (root / ".sdd" / "templates" / "cross-cutting.template.md").unlink()
    (root / ".sdd" / ".sdd-manifest.json").write_text(json.dumps(data), encoding="utf-8")
    return root


def test_update_from_4_0_0_syncs_managed_files_and_adds_new_ones(tmp_path):
    _project_at_4_0_0(tmp_path)
    for rel, text in {".sdd/backlog.md": "mine", ".sdd/documentation.json": "{}", ".sdd/.reservations.json": "{}",
                      ".sdd/tracks/login/claims.json": "{}"}.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(text, encoding="utf-8")
    cmd_update(types.SimpleNamespace(path=str(tmp_path), dry_run=False, major=False))
    assert "sdd track incorporate" in (tmp_path / ".sdd" / "skills" / "sdd-track" / "SKILL.md").read_text(encoding="utf-8")
    assert (tmp_path / ".sdd" / "templates" / "cross-cutting.template.md").is_file()
    assert _manifest(tmp_path)["kit_version"] == KIT_VERSION
    for rel, text in {".sdd/backlog.md": "mine", ".sdd/documentation.json": "{}",
                      ".sdd/.reservations.json": "{}", ".sdd/tracks/login/claims.json": "{}"}.items():
        assert (tmp_path / rel).read_text(encoding="utf-8") == text, rel
