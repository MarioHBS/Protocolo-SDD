"""Tests for `sdd update` — selective patch/minor sync of managed files.

Unlike `sdd migrate`, this never wipes `.sdd/skills/`/`.sdd/templates/`
wholesale: it diffs each managed file's old-bundled vs new-bundled content
and only touches what actually changed, preserving hand-edited files (backed
up, not overwritten). It requires an existing manifest as a diff baseline and
refuses to run across a major-version boundary.

Pattern follows `test_doctor.py`: direct `sdd_cli` imports (`conftest`
already puts `src/` on `sys.path`), `cmd_update` driven with a
`SimpleNamespace` args stub, `tmp_path` fixtures, `capsys` for output.

Since `cmd_update` reads the REAL installed package's `CONTENT_DIR`/
`KIT_VERSION` as "new" content, a project seeded straight from that same
content has nothing to diff for most files (old == new bytes) -- that is a
real, valid scenario (a patch bump whose delta doesn't touch a given file),
exercised by `test_patch_bump_no_hand_edits`. To exercise a file that
*actually* changed between versions, one managed file (README.md) is seeded
with deliberately different content recorded as its "old" baseline hash,
while the real bundled content plays "new".
"""
from __future__ import annotations

import json
import shutil
import tomllib
import types
from pathlib import Path

from sdd_cli import manifest
from sdd_cli.cli import cmd_update
from sdd_cli.content import CONTENT_DIR, KIT_VERSION


def _args(path: Path, dry_run: bool = False) -> types.SimpleNamespace:
    return types.SimpleNamespace(path=str(path), dry_run=dry_run)


def _run(capsys, path: Path, dry_run: bool = False):
    """Run cmd_update, returning (stdout+stderr combined, exit_code-or-None).

    `die()` prints to stderr; ordinary progress output goes to stdout. Tests
    that only care about "was the right message printed" check the combined
    text so they don't need to know which stream a given code path uses.
    """
    try:
        cmd_update(_args(path, dry_run))
    except SystemExit as exc:
        captured = capsys.readouterr()
        return captured.out + captured.err, exc.code
    captured = capsys.readouterr()
    return captured.out + captured.err, None


def _seed_project(tmp_path: Path, kit_version: str,
                   stale_readme: bool = False) -> Path:
    """Seed a `.sdd/` whose managed files mirror the REAL bundled kit
    content, with a manifest stamped at `kit_version`.

    If `stale_readme` is True, README.md's recorded manifest hash (and its
    on-disk content) are set to a deliberately different "old" version, so
    `cmd_update` sees a genuine stale-vs-current-bundled diff for that one
    file without needing a second full kit snapshot in the repo.
    """
    sdd = tmp_path / ".sdd"
    src_sdd = CONTENT_DIR / "sdd"
    recorded: dict[str, str] = {}

    for name in ("README.md",):
        dst = sdd / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_sdd / name, dst)
        recorded[f".sdd/{name}"] = manifest.hash_file(dst)

    for d in ("skills", "templates"):
        for item in sorted((src_sdd / d).rglob("*")):
            if item.is_dir():
                continue
            rel = item.relative_to(src_sdd)
            dst = sdd / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dst)
            recorded[f".sdd/{rel.as_posix()}"] = manifest.hash_file(dst)

    if stale_readme:
        old_content = (src_sdd / "README.md").read_text(encoding="utf-8")
        old_content += "\n<!-- old version marker, pre-dates current bundle -->\n"
        old_path = tmp_path / "_old_readme_baseline.md"
        old_path.write_text(old_content, encoding="utf-8")
        recorded[".sdd/README.md"] = manifest.hash_file(old_path)
        (sdd / "README.md").write_text(old_content, encoding="utf-8")

    (sdd / "stages").mkdir(exist_ok=True)
    m = manifest.build(kit_version, "en", ["generic"],
                       {"estimation": False, "documentation": False}, recorded)
    manifest.save(tmp_path, m)
    return tmp_path


def _one_patch_below(version: str) -> str:
    major, minor, patch = manifest.parse_version(version)
    if patch > 0:
        return f"v{major}.{minor}.{patch - 1}"
    return f"v{major}.{max(minor - 1, 0)}.0"


# ------------------------------------------------------------ patch bump ---

def test_patch_bump_no_hand_edits(capsys, tmp_path):
    old_version = _one_patch_below(KIT_VERSION)
    root = _seed_project(tmp_path, old_version)
    out, code = _run(capsys, root)
    assert code in (None, 0)
    assert "preserved(hand-edited)=0" in out
    m = manifest.load(root)
    assert m["kit_version"] == KIT_VERSION


def test_patch_bump_updates_a_genuinely_changed_file(capsys, tmp_path):
    old_version = _one_patch_below(KIT_VERSION)
    root = _seed_project(tmp_path, old_version, stale_readme=True)
    readme = root / ".sdd" / "README.md"
    before = readme.read_bytes()
    out, code = _run(capsys, root)
    assert code in (None, 0)
    assert "updated" in out
    assert ".sdd/README.md" in out
    after = readme.read_bytes()
    assert after != before
    assert after == (CONTENT_DIR / "sdd" / "README.md").read_bytes()
    m = manifest.load(root)
    assert m["managed_files"][".sdd/README.md"] == \
        manifest.hash_file(CONTENT_DIR / "sdd" / "README.md")


# -------------------------------------------------------------- hand-edit --

def test_patch_bump_preserves_hand_edited_file(capsys, tmp_path):
    old_version = _one_patch_below(KIT_VERSION)
    root = _seed_project(tmp_path, old_version, stale_readme=True)
    hand_edited = "# hand-edited by the user, do not overwrite\n"
    (root / ".sdd" / "README.md").write_text(hand_edited, encoding="utf-8")

    out, code = _run(capsys, root)
    assert code in (None, 0)
    assert "hand-edited" in out
    assert (root / ".sdd" / "README.md").read_text(encoding="utf-8") == hand_edited

    backup_root = root / ".sdd" / ".pre-migrate-backup"
    assert backup_root.exists()
    backups = list(backup_root.rglob("README.md"))
    assert any(b.read_text(encoding="utf-8") == hand_edited for b in backups)


# ------------------------------------------------------------- new files ---

def test_minor_bump_adds_new_template_file(capsys, tmp_path):
    old_version = _one_patch_below(KIT_VERSION)
    root = _seed_project(tmp_path, old_version)
    target = root / ".sdd" / "templates" / "estimates.template.md"
    m = manifest.load(root)
    del m["managed_files"][".sdd/templates/estimates.template.md"]
    manifest.save(root, m)
    target.unlink()

    out, code = _run(capsys, root)
    assert code in (None, 0)
    assert "added" in out
    assert target.exists()
    assert target.read_bytes() == \
        (CONTENT_DIR / "sdd" / "templates" / "estimates.template.md").read_bytes()
    m2 = manifest.load(root)
    assert ".sdd/templates/estimates.template.md" in m2["managed_files"]


# --------------------------------------------------------- major boundary --

def test_refuses_across_major_boundary(capsys, tmp_path):
    root = _seed_project(tmp_path, "v2.9.9")
    before = {
        p: p.read_bytes()
        for p in (root / ".sdd").rglob("*") if p.is_file()
    }
    out, code = _run(capsys, root)
    assert code == 1
    assert "sdd migrate --to v" in out
    after = {
        p: p.read_bytes()
        for p in (root / ".sdd").rglob("*") if p.is_file()
    }
    assert before == after


# ---------------------------------------------------------------- no-op ---

def test_idempotent_when_already_up_to_date(capsys, tmp_path):
    root = _seed_project(tmp_path, KIT_VERSION)
    before = {
        p: p.read_bytes()
        for p in (root / ".sdd").rglob("*") if p.is_file()
    }
    out, code = _run(capsys, root)
    assert code in (None, 0)
    assert "up to date" in out
    after = {
        p: p.read_bytes()
        for p in (root / ".sdd").rglob("*") if p.is_file()
    }
    assert before == after


# --------------------------------------------------------------- dry-run --

def test_dry_run_writes_nothing(capsys, tmp_path):
    old_version = _one_patch_below(KIT_VERSION)
    root = _seed_project(tmp_path, old_version, stale_readme=True)
    before = {
        p: p.read_bytes()
        for p in (root / ".sdd").rglob("*") if p.is_file()
    }
    out, code = _run(capsys, root, dry_run=True)
    assert code in (None, 0)
    assert "DRY RUN" in out
    after = {
        p: p.read_bytes()
        for p in (root / ".sdd").rglob("*") if p.is_file()
    }
    assert before == after
    m = manifest.load(root)
    assert m["kit_version"] == old_version


# -------------------------------------------------------------- legacy ----

def test_legacy_project_without_manifest_refused(capsys, tmp_path):
    sdd = tmp_path / ".sdd"
    (sdd / "stages").mkdir(parents=True)
    (sdd / "stages" / ".gitkeep").touch()

    out, code = _run(capsys, tmp_path)
    assert code == 1
    assert "migrate --to v2" in out


# --------------------------------------------------------- version drift --

def test_pyproject_version_matches_bundled_kit_version():
    """content/VERSION and pyproject.toml are two independently hand-edited
    sources of truth for the package version -- they have drifted before
    (see CHANGELOG's 3.0.1 entry). This turns that drift into a hard test
    failure instead of a silent bug the next time only one file is bumped.
    """
    pyproject_path = CONTENT_DIR.parent.parent.parent / "pyproject.toml"
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    assert data["project"]["version"] == KIT_VERSION.lstrip("v")
