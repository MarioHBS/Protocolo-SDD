from __future__ import annotations

import json
import os
import subprocess
import sys
import types
from pathlib import Path

import pytest

from sdd_cli import _lock, _tracks
from sdd_cli.cli import (
    _doctor_payload,
    _relativize_file_links,
    cmd_fix,
    cmd_seq,
    cmd_track,
)

SRC = Path(__file__).resolve().parents[1] / "src"


def _args(**values):
    return types.SimpleNamespace(path=".", json=False, **values)


def _claim(slug, paths, **extra):
    return _args(track_command="claim", slug=slug, stage="001", path_claim=paths, seq=extra.get("seq"),
                 runtime=extra.get("runtime"), stability_sensitive=extra.get("stability", False))


def test_track_check_detects_shared_path(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    for slug in ("left", "right"):
        (tmp_path / ".sdd" / "tracks" / slug).mkdir(parents=True)
    cmd_track(_claim("left", ["src/**"]))
    cmd_track(_claim("right", ["src/app.py"]))
    with pytest.raises(SystemExit) as error:
        cmd_track(_args(track_command="check"))
    assert error.value.code == 1
    assert "conflict path" in capsys.readouterr().out


def test_track_check_allows_disjoint_paths(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    for slug in ("api", "web"):
        (tmp_path / ".sdd" / "tracks" / slug).mkdir(parents=True)
    cmd_track(_claim("api", ["api/**"]))
    cmd_track(_claim("web", ["web/**"]))
    cmd_track(_args(track_command="check"))
    assert "clean" in capsys.readouterr().out


@pytest.mark.parametrize(("left", "right", "expected"), [
    ("**/*.tsx", "src/App.tsx", True),          # wildcard-anywhere must not hide a real overlap
    ("**/*.tsx", "src/App.ts", False),
    ("src/comp", "src/components", False),      # prefixes compare by path component, not by characters
    ("src/components", "src/components/a/b.tsx", True),
    ("src/*.ts", "src/components/**", False),   # a single star does not cross directories
    ("src/**/x.ts", "src/a/**", True),
    ("api/**", "web/**", False),
    ("src/a.ts", "src/a.ts", True),
])
def test_overlap_rules(left, right, expected):
    assert _tracks._overlap(left, right) is expected


def test_conflicts_cover_runtime_sequence_and_stability(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for slug in ("a", "b"):
        (tmp_path / ".sdd" / "tracks" / slug).mkdir(parents=True)
    cmd_track(_claim("a", ["a/**"], runtime=["db-write"], seq=["migration"]))
    cmd_track(_claim("b", ["b/**"], runtime=["db-write"], seq=["migration"], stability=True))
    kinds = {c["kind"] for c in _tracks.check(tmp_path)}
    assert kinds == {"runtime", "sequence", "stability"}


def test_concluded_track_claims_are_ignored(tmp_path):
    for slug in ("live", "done"):
        (tmp_path / ".sdd" / "tracks" / slug).mkdir(parents=True)
    (tmp_path / ".sdd" / "constitution.md").write_text(
        "### Active tracks\n\n| Track | State |\n| --- | --- |\n| `live` | open |\n\n## 1. V\n", encoding="utf-8")
    for slug in ("live", "done"):
        _tracks.save(tmp_path, slug, {"version": 1, "claims": [{"stage": "001", "paths": ["src/**"]}]})
    assert _tracks.check(tmp_path) == []


def _git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def test_track_verify_flags_unclaimed_git_change(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _git(tmp_path, "init")
    (tmp_path / ".sdd" / "tracks" / "api").mkdir(parents=True)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "api.py").write_text("before\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("before\n", encoding="utf-8")
    _git(tmp_path, "add", ".")
    (tmp_path / "src" / "api.py").write_text("after\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("after\n", encoding="utf-8")
    cmd_track(_claim("api", ["src/**"]))
    with pytest.raises(SystemExit) as error:
        cmd_track(_args(track_command="verify", slug="api", since=None))
    assert error.value.code == 1
    assert "README.md" in capsys.readouterr().out


def test_verify_sees_untracked_files_and_ignores_sibling_and_sdd_work(tmp_path):
    _git(tmp_path, "init")
    for slug in ("api", "web"):
        (tmp_path / ".sdd" / "tracks" / slug).mkdir(parents=True)
    (tmp_path / "api").mkdir()
    (tmp_path / "web").mkdir()
    _tracks.save(tmp_path, "api", {"version": 1, "claims": [{"stage": "001", "paths": ["api/**"]}]})
    _tracks.save(tmp_path, "web", {"version": 1, "claims": [{"stage": "001", "paths": ["web/**"]}]})
    (tmp_path / "api" / "new.py").write_text("x", encoding="utf-8")   # untracked, mine
    (tmp_path / "web" / "page.ts").write_text("x", encoding="utf-8")  # the sibling's work
    (tmp_path / "stray.txt").write_text("x", encoding="utf-8")        # nobody's
    findings = _tracks.verify(tmp_path, "api")
    assert [f["path"] for f in findings] == ["stray.txt"]


def test_verify_flags_file_claimed_by_two_tracks(tmp_path):
    _git(tmp_path, "init")
    for slug in ("a", "b"):
        (tmp_path / ".sdd" / "tracks" / slug).mkdir(parents=True)
        _tracks.save(tmp_path, slug, {"version": 1, "claims": [{"stage": "001", "paths": ["shared/**"]}]})
    (tmp_path / "shared").mkdir()
    (tmp_path / "shared" / "x.py").write_text("x", encoding="utf-8")
    findings = _tracks.verify(tmp_path, "a")
    assert findings == [{"kind": "track_shared_touch", "path": "shared/x.py", "tracks": ["a", "b"]}]


def test_sequence_reservation_skips_existing_and_reserved_numbers(tmp_path, capsys):
    (tmp_path / ".sdd").mkdir()
    migrations = tmp_path / "supabase" / "migrations"
    migrations.mkdir(parents=True)
    (migrations / "0023_existing.sql").write_text("-- migration\n", encoding="utf-8")
    args = types.SimpleNamespace(path=str(tmp_path), name="migration", track="api", json=False)
    cmd_seq(args)
    cmd_seq(args)
    assert capsys.readouterr().out.splitlines() == ["0024", "0025"]


def test_declared_sequence_and_duplicate_detection(tmp_path):
    (tmp_path / ".sdd").mkdir()
    (tmp_path / ".sdd" / "constitution.md").write_text(
        "## 7. Conventions\n\n- **Sequences:** `migration` = `db/NNNN_*.sql`\n", encoding="utf-8")
    db = tmp_path / "db"
    db.mkdir()
    (db / "0023_seed.sql").write_text("x", encoding="utf-8")
    (db / "0023_limit.sql").write_text("x", encoding="utf-8")
    (db / "0024_other.sql").write_text("x", encoding="utf-8")
    assert _tracks.sequences(tmp_path) == {"migration": "db/NNNN_*.sql"}
    duplicates = _tracks.duplicate_numbers(tmp_path)
    assert [(d["sequence"], d["number"]) for d in duplicates] == [("migration", 23)]
    codes = {f["code"] for f in _doctor_payload(tmp_path)["findings"]}
    assert "sequence_duplicate" in codes
    assert _tracks.reserve_sequence(tmp_path, "migration")["number"] == "0025"


def test_unknown_sequence_is_reported(tmp_path):
    (tmp_path / ".sdd").mkdir()
    with pytest.raises(ValueError, match="unknown sequence"):
        _tracks.reserve_sequence(tmp_path, "nope")


# ---------------------------------------------------------- incorporation

INDEX = (
    "## 5. Stage index (CANONICAL)\n\n"
    "| Stage | Slug | Status | Spec | Report |\n| --- | --- | --- | --- | --- |\n"
    "| 001 | base | concluída | [spec](stages/001-base/spec.md) | [report](stages/001-base/report.md) |\n"
    "| 002 | api | concluída | [spec](stages/002-api/spec.md) | [report](stages/002-api/report.md) |\n\n"
    "### Provisional queue\n\n- later\n\n## 6. History\n"
)


def _incorporation_project(root: Path, *tracks: str, newline: str = "\n") -> None:
    sdd = root / ".sdd"
    for number, name in ((1, "base"), (2, "api")):
        (sdd / "stages" / f"{number:03d}-{name}").mkdir(parents=True)
    (sdd / "constitution.md").write_bytes(INDEX.replace("\n", newline).encode("utf-8"))
    for slug in tracks:
        stage = sdd / "tracks" / slug / "stages" / f"001-{slug}-work"
        stage.mkdir(parents=True)
        (stage / "report.md").write_text("done", encoding="utf-8")
        _tracks.save(root, slug, {"version": 1, "claims": [
            {"stage": f"001-{slug}-work", "paths": [f"{slug}/**"]}]})


def test_incorporate_moves_stage_appends_row_and_releases_claims(tmp_path):
    _incorporation_project(tmp_path, "billing")
    stage = tmp_path / ".sdd" / "tracks" / "billing" / "stages" / "001-billing-work"
    result = _tracks.incorporate(tmp_path, "billing", stage)
    assert result["number"] == "003"
    assert not stage.exists()
    assert (tmp_path / ".sdd" / "stages" / "003-billing-work" / "report.md").is_file()
    text = (tmp_path / ".sdd" / "constitution.md").read_text(encoding="utf-8")
    rows = [line for line in text.splitlines() if line.startswith("| 00")]
    assert rows[-1] == ("| 003 | billing-work | concluída | [spec](stages/003-billing-work/spec.md) "
                        "| [report](stages/003-billing-work/report.md) |")
    assert text.index(rows[-1]) < text.index("### Provisional queue")
    assert _tracks.load(tmp_path, "billing")["claims"] == []
    ledger = json.loads((tmp_path / ".sdd" / ".reservations.json").read_text(encoding="utf-8"))
    assert ledger["sequences"]["stage"] == [{"number": "003", "track": "billing"}]


def test_incorporate_dry_run_writes_nothing(tmp_path):
    _incorporation_project(tmp_path, "billing")
    stage = tmp_path / ".sdd" / "tracks" / "billing" / "stages" / "001-billing-work"
    before = (tmp_path / ".sdd" / "constitution.md").read_bytes()
    result = _tracks.incorporate(tmp_path, "billing", stage, dry_run=True)
    assert result["number"] == "003" and result["dry_run"] is True
    assert stage.exists()
    assert (tmp_path / ".sdd" / "constitution.md").read_bytes() == before


def test_incorporate_requires_a_report(tmp_path):
    _incorporation_project(tmp_path, "billing")
    stage = tmp_path / ".sdd" / "tracks" / "billing" / "stages" / "001-billing-work"
    (stage / "report.md").unlink()
    with pytest.raises(ValueError, match="report.md"):
        _tracks.incorporate(tmp_path, "billing", stage)


def test_incorporate_preserves_crlf_line_endings(tmp_path):
    _incorporation_project(tmp_path, "billing", newline="\r\n")
    stage = tmp_path / ".sdd" / "tracks" / "billing" / "stages" / "001-billing-work"
    _tracks.incorporate(tmp_path, "billing", stage)
    raw = (tmp_path / ".sdd" / "constitution.md").read_bytes()
    assert raw.count(b"\n") == raw.count(b"\r\n")


def test_concurrent_incorporations_never_share_a_number(tmp_path):
    slugs = ("alpha", "beta", "gamma")
    _incorporation_project(tmp_path, *slugs)
    env = {**os.environ, "PYTHONPATH": str(SRC)}
    procs = [subprocess.Popen(
        [sys.executable, "-m", "sdd_cli", "track", "incorporate", slug, f"001-{slug}-work", str(tmp_path),
         "--json"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for slug in slugs]
    numbers = []
    for proc in procs:
        out, err = proc.communicate(timeout=60)
        assert proc.returncode == 0, err
        numbers.append(json.loads(out)["number"])
    assert sorted(numbers) == ["003", "004", "005"]
    rows = [line for line in (tmp_path / ".sdd" / "constitution.md").read_text(encoding="utf-8").splitlines()
            if line.startswith("| 00")]
    assert len(rows) == 5 and len({r.split("|")[1].strip() for r in rows}) == 5


# ------------------------------------------------------------------ lock

def test_lock_times_out_while_held_and_breaks_stale_locks(tmp_path):
    path = tmp_path / ".lock"
    with _lock.file_lock(path):
        with pytest.raises(_lock.LockTimeout):
            with _lock.file_lock(path, timeout=0.2, poll=0.02):
                pass
    assert not path.exists()
    path.write_text("{}", encoding="utf-8")
    old = path.stat().st_mtime - 3600
    os.utime(path, (old, old))
    with _lock.file_lock(path, stale=60):
        assert path.exists()


# ------------------------------------------- doctor, branches and worktrees

def test_doctor_reports_session_on_another_branch(tmp_path):
    _git(tmp_path, "init", "-b", "main")
    (tmp_path / ".sdd").mkdir()
    (tmp_path / ".sdd" / ".session.json").write_text(json.dumps(
        {"version": 1, "state": "IMPLEMENTING", "active_stage": None, "branch": "trail/other"}), encoding="utf-8")
    finding = next(f for f in _doctor_payload(tmp_path)["findings"] if f["code"] == "session_branch_mismatch")
    assert finding["expected"] == "trail/other"


def test_fix_gitignore_adds_worktree_folders_once(tmp_path, capsys):
    (tmp_path / ".sdd").mkdir()
    (tmp_path / ".git").mkdir()
    (tmp_path / ".kilo" / "worktrees").mkdir(parents=True)
    (tmp_path / ".gitignore").write_text("node_modules", encoding="utf-8")
    args = types.SimpleNamespace(path=str(tmp_path), gitignore=True, dry_run=False, json=False)
    with pytest.raises(SystemExit):  # status 1 = repairs applied
        cmd_fix(args)
    text = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert "node_modules\n" in text and "/.kilo/worktrees/" in text
    cmd_fix(args)  # idempotent: nothing left to repair, no SystemExit
    assert (tmp_path / ".gitignore").read_text(encoding="utf-8") == text


def test_relative_links_are_relative_to_sdd_dir(tmp_path):
    root_uri = tmp_path.resolve().as_uri()
    text = (f"[a]({root_uri}/.sdd/stages/001-x/spec.md) [b]({root_uri}/src/app.ts) "
            "[c](file:///z:/old/checkout/.sdd/stages/002-y/report.md) [d](file:///elsewhere/file.md)")
    assert _relativize_file_links(text, tmp_path) == (
        "[a](stages/001-x/spec.md) [b](../src/app.ts) [c](stages/002-y/report.md) "
        "[d](file:///elsewhere/file.md)")


def test_the_template_placeholder_is_not_a_declared_sequence(tmp_path):
    from sdd_cli.content import CONTENT_DIR

    (tmp_path / ".sdd").mkdir()
    template = (CONTENT_DIR / "sdd" / "constitution.md").read_text(encoding="utf-8")
    (tmp_path / ".sdd" / "constitution.md").write_text(template, encoding="utf-8")
    assert _tracks.sequences(tmp_path) == {}   # the commented example must not become a sequence


def test_track_parked_on_hold_is_not_reported_as_not_started(tmp_path):
    from sdd_cli import _user_files
    for slug in ("parked", "forgotten"):
        (tmp_path / ".sdd" / "tracks" / slug).mkdir(parents=True)
    (tmp_path / ".sdd" / "constitution.md").write_text(
        "### Active tracks\n\n| Track | State |\n| --- | --- |\n| `parked` | on hold (waiting for the client) |\n"
        "| `forgotten` | open |\n\n## 1. V\n", encoding="utf-8")
    flagged = [d.track for d in _user_files._scan_tracks_v4(tmp_path / ".sdd") if d.kind == "not_started"]
    assert flagged == ["forgotten"]
    assert _user_files.on_hold_track_slugs(tmp_path / ".sdd") == {"parked"}
