"""Tests for the mojibake toolkit (Parte B).

Covers the three decisions locked in memory/mojibake-toolkit-decisions:
  1. v1 (`?` accent-loss) is audit-only and ambiguous (suspect, not a verdict);
  2. v2 (double-encoding) is deterministic, ERROR-class, and fixable;
  3. one shared detector backs both doctor (report) and migrate (gate).
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from sdd_cli import _mojibake, _user_files

# Double-encoding mojibake (v2): the 4-byte sequence a single accent becomes
# when its UTF-8 bytes are decoded as Latin-1 and UTF-8-encoded again. A clean
# accent is UTF-8 `c3 X` (X = 2nd byte, always in 0x80-0xbf). Double-encoding
# turns it into `c3 83 c2 X` (the `c3`->`Ã`->`c3 83`; the `X`-byte -> its Latin-1
# char -> `c2 X`). So the span's 4th byte IS the accent's UTF-8 2nd byte.
# Verified against the sandbox_diagnosis corpus (130 spans, all this branch).
V2_PAI = {
    "ç":  (0xc3, 0x83, 0xc2, 0xa7),   # c3 a7
    "ã":  (0xc3, 0x83, 0xc2, 0xa3),   # c3 a3
    "é":  (0xc3, 0x83, 0xc2, 0xa9),   # c3 a9
    "á":  (0xc3, 0x83, 0xc2, 0xa1),   # c3 a1
    "ó":  (0xc3, 0x83, 0xc2, 0xb3),   # c3 b3
    "ê":  (0xc3, 0x83, 0xc2, 0xaa),   # c3 aa
    "ú":  (0xc3, 0x83, 0xc2, 0xba),   # c3 ba
    "õ":  (0xc3, 0x83, 0xc2, 0xb5),   # c3 b5
}


def _bytes(seq) -> bytes:
    return bytes(seq)


# ----------------------------------------------------------- detection (v2)

def test_v2_detected_at_byte_level():
    raw = b"Decis\xc3\x83\xc2\xb5es da constitui\xc3\x83\xc2\xa7\xc3\x83\xc2\xa3o"
    rep = _mojibake.FileReport(path=Path("x"), v2=[], v1=[], is_utf8=True)
    # exercise the real scanner
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        f.write(raw)
        p = Path(f.name)
    try:
        rep = _mojibake.scan_file(p)
        assert len(rep.v2) == 3, rep.v2
        assert rep.is_utf8 is True
    finally:
        p.unlink()


def test_v2_zero_false_positives_for_legitimate_a_tilde():
    """The only legitimate Ã in PT prose (the standalone letter in "NÃO") must
    NOT be flagged. Its following byte is `o` (0x6f), not c2/c3."""
    raw = "Não fale NÃO agora.".encode("utf-8")
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        f.write(raw)
        p = Path(f.name)
    try:
        rep = _mojibake.scan_file(p)
        assert rep.v2 == []
        assert rep.v1 == []
    finally:
        p.unlink()


@pytest.mark.parametrize("accent,seq", sorted(V2_PAI.items()))
def test_each_accent_round_trips_through_repair(accent, seq):
    bad = _bytes(seq).decode("utf-8")
    fixed = _mojibake.repair_v2_text(bad)
    assert fixed == accent, (bad, fixed, accent)


# ----------------------------------------------------------- detection (v1)

def test_v1_question_mark_glued_to_letter_is_suspect():
    """A `?` between letters (or a run of `?` between letters) is the lost-accent
    signature: `Decis?es`, `aplica??o`, `pr?prias`. `2?` is NOT (digit left)."""
    raw = b"Decis?es e aplica??o pr?prias 2? seculo"
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        f.write(raw)
        p = Path(f.name)
    try:
        rep = _mojibake.scan_file(p)
        # Decis?es (1) + aplica??o (first ? only) + pr?prias (1) == 3; `2?` no
        assert len(rep.v1) == 3, rep.v1
        assert rep.v2 == [], "a `?`-only file must not be classed as v2"
    finally:
        p.unlink()


def test_v1_sentence_end_question_mark_is_ignored():
    """A `?` at the end of a sentence (`it?`, `Why?`, `[y/N]?`, `?"`) is NOT
    flagged — the right neighbour is not a letter. This is what keeps the
    detector off genuine English questions."""
    raw = b"What now? Why? Then ? ? ok [y/N]? \"x\"? end"
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        f.write(raw)
        p = Path(f.name)
    try:
        rep = _mojibake.scan_file(p)
        assert rep.v1 == [], rep.v1
    finally:
        p.unlink()


def test_v1_truly_standalone_question_mark_is_ignored():
    """A `?` surrounded by whitespace on both sides is never a suspect."""
    raw = b"see ? ok\n? ?\nend"
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        f.write(raw)
        p = Path(f.name)
    try:
        rep = _mojibake.scan_file(p)
        assert rep.v1 == [], rep.v1
    finally:
        p.unlink()


# --------------------------------------------------------- classification

def test_classify_splits_v2_and_v1_only():
    import tempfile
    v2 = b"constitui\xc3\x83\xc2\xa7\xc3\x83\xc2\xa3o"
    v1 = b"Decis?es pr?prias"
    clean = "Decisões próprias sem mojibake".encode("utf-8")
    files = []
    for content in (v2, v1, clean):
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            f.write(content)
            files.append(Path(f.name))
    try:
        reports = [_mojibake.scan_file(p) for p in files]
    finally:
        for p in files:
            p.unlink()
    v2_files, v1_only = _mojibake.classify_reports(reports)
    assert len(v2_files) == 1
    assert len(v1_only) == 1
    assert v2_files[0].v2 and not v2_files[0].v1


# ------------------------------------------------------------------- repair

def test_repair_v2_file_round_trips():
    clean = "A constituição aplica decisões próprias do século NÃO incluídas."
    # synthesize double-encoding: encode utf-8, decode latin-1, encode utf-8
    corrupted = clean.encode("utf-8").decode("latin-1").encode("utf-8")
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        f.write(corrupted)
        p = Path(f.name)
    try:
        n = _mojibake.repair_v2_file(p)
        assert n > 0
        assert p.read_text(encoding="utf-8") == clean
    finally:
        p.unlink()


def test_repair_v2_file_idempotent():
    import tempfile
    corrupted = "cação".encode("utf-8").decode("latin-1").encode("utf-8")
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        f.write(corrupted)
        p = Path(f.name)
    try:
        assert _mojibake.repair_v2_file(p) > 0
        assert _mojibake.repair_v2_file(p) == 0  # second pass: no v2 left
    finally:
        p.unlink()


def test_repair_preserves_non_v2_bytes():
    """A file with a mix of v2 mojibake AND legitimate content (including an
    inline code `?` and the word NÃo) repairs only the v2 spans. All non-ASCII
    chars here are single-codepoint Latin-range accents (the exact shape v2
    targets); a 3-byte char like an em-dash is intentionally excluded — it
    lies outside what a double-encode of Traceable UTF-8 produces and would
    muddy the round-trip."""
    clean = "NÃO usar `self?` em aplicações, decisão."
    corrupted = clean.encode("utf-8").decode("latin-1").encode("utf-8")
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        f.write(corrupted)
        p = Path(f.name)
    try:
        n = _mojibake.repair_v2_file(p)
        # the 5 accents çã + ã + çã + õ + ã = NÃO(Ã) aplicações(ç,õ) nãoã(ã)
        assert n >= 4, (n, p.read_text(encoding="utf-8"))
        assert p.read_text(encoding="utf-8") == clean
    finally:
        p.unlink()


# ----------------------------------------------------------------- end-to-end

def _sdd_project(tmp_path: Path, *, stages: dict | None = None,
                 changelog: bool = False) -> Path:
    """Build a minimal .sdd/ tree. `stages` maps folder name -> dict of files."""
    sdd = tmp_path / ".sdd"
    (sdd / "stages").mkdir(parents=True)
    if changelog:
        (sdd / "CHANGELOG.md").write_text("# Structural change log\n", encoding="utf-8")
    for name, files in (stages or {}).items():
        d = sdd / "stages" / name
        d.mkdir()
        for fname, content in files.items():
            (d / fname).write_text(content, encoding="utf-8")
    return sdd


def test_doctor_reports_v2_and_exits_nonzero(tmp_path, capsys, monkeypatch):
    sdd_d = _sdd_project(tmp_path, stages={
        "001-dirty": {"spec.md": "constitui\xc3\x83\xc2\xa7\xc3\x83\xc2\xa3o moji"},
    })
    # scan_tree works on bytes; write mojibake bytes directly
    bad = b"constitui\xc3\x83\xc2\xa7\xc3\x83\xc2\xa3o moji"
    (sdd_d / "stages" / "001-dirty" / "spec.md").write_bytes(bad)

    from sdd_cli import cli
    args = cli.build_parser().parse_args(["doctor", str(tmp_path)])
    with pytest.raises(SystemExit) as exc:
        cli.cmd_doctor(args)
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "double-encoding" in out.lower() or "v2" in out


def test_doctor_clean_exits_zero(tmp_path, capsys):
    _sdd_project(tmp_path, stages={
        "001-clean": {"spec.md": "Sem mojibake aqui.", "todo.md": "- [x] done\n",
                      "report.md": "# ok\n"},
    }, changelog=True)
    from sdd_cli import cli
    args = cli.build_parser().parse_args(["doctor", str(tmp_path)])
    cli.cmd_doctor(args)  # must not raise SystemExit
    out = capsys.readouterr().out
    assert "no mojibake" in out and "clean" in out


def test_migrate_blocks_on_v2_without_fix(tmp_path, capsys, monkeypatch):
    sdd_d = _sdd_project(tmp_path, stages={
        "001-dirty": {"spec.md": "x"},
    })
    bad = b"constitui\xc3\x83\xc2\xa7\xc3\x83\xc2\xa3o"
    (sdd_d / "stages" / "001-dirty" / "spec.md").write_bytes(bad)
    # need a manifest so migrate proceeds past the v1-preflight checks
    (sdd_d / ".sdd-manifest.json").write_text("{}", encoding="utf-8")

    from sdd_cli import cli
    args = cli.build_parser().parse_args(["migrate", "--to", "v4", str(tmp_path)])
    with pytest.raises(SystemExit) as exc:
        cli.cmd_migrate(args)
    assert exc.value.code == 1
    # the dirty file must be untouched (gate fires before any write)
    assert (sdd_d / "stages" / "001-dirty" / "spec.md").read_bytes() == bad
    out = capsys.readouterr().out
    assert "Nothing was written" in out


def test_migrate_fix_mojibake_repairs_v2(tmp_path):
    """Exercises the same repair+rescan sequence that `migrate --fix-mojibake`
    runs in its gate. We call the repair directly (migrate's full path needs
    the content pack installed) and assert the post-fix re-scan is clean —
    which is the invariant the gate enforces before proceeding."""
    sdd_d = _sdd_project(tmp_path, stages={
        "001-dirty": {"spec.md": "x", "report.md": "done"},
    })
    bad = b"constitui\xc3\x83\xc2\xa7\xc3\x83\xc2\xa3o decis\xc3\x83\xc2\xb5es"
    spec = sdd_d / "stages" / "001-dirty" / "spec.md"
    spec.write_bytes(bad)

    # repair (as the --fix-mojibake gate does): 3 spans = ç, ã, õ
    n = _mojibake.repair_v2_file(spec)
    assert n == 3
    assert spec.read_text("utf-8") == "constituição decisões"

    # re-scan: the gate asserts no v2 remains after repair
    still_v2, _ = _mojibake.classify_reports(_mojibake.scan_tree(sdd_d))
    assert still_v2 == []


# -------------------------------------------------- user_files hygiene

def test_closed_stage_with_open_todo_flagged(tmp_path):
    sdd = _sdd_project(tmp_path, stages={
        "027-like": {
            "spec.md": "x",
            "todo.md": "- [x] done\n- [ ] leftover\n",
            "report.md": "# closed\n",
        },
    })
    hyg = _user_files.scan_hygiene(sdd)
    assert len(hyg.closed_with_open_todo) == 1
    d = hyg.closed_with_open_todo[0]
    assert d.stage == "027-like"
    assert d.open_checkboxes == 1
    assert d.total_checkboxes == 2


def test_open_stage_not_flagged(tmp_path):
    sdd = _sdd_project(tmp_path, stages={
        "005-open": {
            "spec.md": "x",
            "todo.md": "- [ ] todo\n- [ ] more\n",
            # no report.md -> stage is open, open boxes are expected
        },
    })
    hyg = _user_files.scan_hygiene(sdd)
    assert hyg.closed_with_open_todo == []


def test_spec_without_todo_flagged(tmp_path):
    sdd = _sdd_project(tmp_path, stages={
        "010-nospec": {"spec.md": "x"},  # spec, no todo, no report
    })
    hyg = _user_files.scan_hygiene(sdd)
    assert "010-nospec" in hyg.spec_without_todo


def test_changelog_detection(tmp_path):
    sdd = _sdd_project(tmp_path, changelog=True)
    assert _user_files.scan_hygiene(sdd).changelog_exists is True
    sdd2 = _sdd_project(tmp_path / "x")
    assert _user_files.scan_hygiene(sdd2).changelog_exists is False
