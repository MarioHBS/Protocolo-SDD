"""K-06: `sddkit doctor` notes a project whose kit is older than the installed CLI.

Before 4.9.1 only the opposite direction (`cli_older_than_project`) was checked, so a project
left on 4.0.0 while the CLI moved to 4.9.0 came out of the doctor clean.
"""
from __future__ import annotations

from test_update import _seed_project

from sdd_cli._findings import describe
from sdd_cli.cli import _doctor_payload
from sdd_cli.content import KIT_VERSION


def _version_findings(root):
    return [f for f in _doctor_payload(root)["findings"]
            if f["code"] in {"kit_behind", "cli_older_than_project"}]


def test_an_older_kit_is_a_note_that_names_both_versions(tmp_path):
    root = _seed_project(tmp_path, "v4.0.0")
    found = _version_findings(root)
    assert found == [{"severity": "note", "code": "kit_behind", "kit": "v4.0.0", "cli": KIT_VERSION}]


def test_the_note_never_changes_the_exit_status(tmp_path):
    root = _seed_project(tmp_path, "v4.0.0")
    assert _doctor_payload(root)["status"] == 0


def test_the_hint_points_to_the_read_only_commands(tmp_path):
    root = _seed_project(tmp_path, "v4.0.0")
    finding = _version_findings(root)[0]
    message, hint = describe(finding)
    assert "v4.0.0" in message and KIT_VERSION in message
    assert "sddkit update --notes" in hint and "sddkit update --dry-run" in hint


def test_a_current_kit_says_nothing(tmp_path):
    root = _seed_project(tmp_path, KIT_VERSION)
    assert _version_findings(root) == []


def test_a_newer_kit_keeps_the_old_warning_only(tmp_path):
    root = _seed_project(tmp_path, "v99.0.0")
    assert [f["code"] for f in _version_findings(root)] == ["cli_older_than_project"]


def test_an_unparseable_version_is_ignored(tmp_path):
    root = _seed_project(tmp_path, "not-a-version")
    assert _version_findings(root) == []
