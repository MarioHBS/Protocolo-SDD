"""K-02: the hash the manifest records does not depend on the line endings on disk.

P1 (KNN) kept getting `manifest_eol_drift` after `fix --manifest`: the kit hashed the raw bytes
(CRLF, as it had just written them), Git then normalised the checkout to LF, and the recorded
value no longer matched. The recorded hash is now the one of the LF form, so a checkout cannot
move it, while manifests written before keep working.
"""
from __future__ import annotations

import hashlib
import types
from pathlib import Path

import pytest
from test_update import KIT_VERSION, _run, _seed_project

from sdd_cli import manifest
from sdd_cli.cli import _doctor_payload, cmd_fix

README = ".sdd/README.md"


def _raw_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]


def _set_eol(path: Path, eol: bytes) -> None:
    path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", eol))


def _fix_manifest(root: Path) -> int | None:
    args = types.SimpleNamespace(path=str(root), dry_run=False, json=False, mojibake=False, eol=False,
                                 links=False, features=False, gitignore=False, manifest=True, all=False)
    try:
        cmd_fix(args)
    except SystemExit as done:
        return done.code
    return None


def test_the_hash_is_the_same_for_lf_and_crlf(tmp_path):
    f = tmp_path / "a.md"
    f.write_bytes(b"one\ntwo\n")
    lf = manifest.hash_file(f)
    f.write_bytes(b"one\r\ntwo\r\n")
    assert manifest.hash_file(f) == lf == _raw_hash(b"one\ntwo\n")


def test_a_hash_recorded_by_an_older_kit_still_matches(tmp_path):
    f = tmp_path / "a.md"
    f.write_bytes(b"one\r\ntwo\r\n")
    assert manifest.matches_recorded(f, _raw_hash(b"one\r\ntwo\r\n"))  # raw CRLF, 4.8.0 and before
    f.write_bytes(b"one\ntwo\n")
    assert manifest.matches_recorded(f, _raw_hash(b"one\r\ntwo\r\n"))  # ... after Git went to LF


def test_fix_manifest_leaves_a_value_that_survives_a_checkout_in_either_form(tmp_path):
    root = _seed_project(tmp_path, KIT_VERSION)
    readme = root / README
    data = manifest.load(root)
    _set_eol(readme, b"\r\n")
    data["managed_files"][README] = _raw_hash(readme.read_bytes())  # as 4.8.0 wrote it
    manifest.save(root, data)
    _set_eol(readme, b"\n")  # Git normalised the checkout
    assert "manifest_eol_drift" in [f["code"] for f in _doctor_payload(root)["findings"]]

    assert _fix_manifest(root) == 1
    assert "manifest_eol_drift" not in [f["code"] for f in _doctor_payload(root)["findings"]]
    _set_eol(readme, b"\r\n")  # and back: the drift that used to return
    assert "manifest_eol_drift" not in [f["code"] for f in _doctor_payload(root)["findings"]]
    assert _fix_manifest(root) is None  # nothing left to repair


@pytest.mark.parametrize("eol", [b"\n", b"\r\n"])
def test_update_records_the_normalised_hash_and_sees_no_drift(capsys, tmp_path, eol):
    root = _seed_project(tmp_path, KIT_VERSION)
    for path in (root / ".sdd").rglob("*.md"):
        _set_eol(path, eol)  # the checkout in either form
    _run(capsys, root)
    data = manifest.load(root)
    for rel, recorded in data["managed_files"].items():
        path = root / rel
        if path.is_file():
            assert recorded == manifest.hash_file(path), rel
    assert "manifest_eol_drift" not in [f["code"] for f in _doctor_payload(root)["findings"]]


def test_an_old_manifest_against_an_lf_checkout_is_not_a_hand_edit(capsys, tmp_path):
    root = _seed_project(tmp_path, KIT_VERSION)
    readme = root / README
    data = manifest.load(root)
    _set_eol(readme, b"\r\n")
    data["managed_files"][README] = _raw_hash(readme.read_bytes())
    manifest.save(root, data)
    _set_eol(readme, b"\n")
    out, _ = _run(capsys, root)
    assert "hand-edited" not in out


def test_an_old_exact_hash_on_a_crlf_checkout_is_not_drift(tmp_path):
    # Most Windows projects: recorded by 4.8.0 on CRLF and still CRLF. Nothing has drifted, so the
    # new hashing must not announce a rehash for every one of them.
    root = _seed_project(tmp_path, KIT_VERSION)
    readme = root / README
    data = manifest.load(root)
    _set_eol(readme, b"\r\n")
    data["managed_files"][README] = _raw_hash(readme.read_bytes())
    manifest.save(root, data)
    assert "manifest_eol_drift" not in [f["code"] for f in _doctor_payload(root)["findings"]]
    assert _fix_manifest(root) is None
