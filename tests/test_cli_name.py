"""N-03: managed text teaches the current command name, never the deprecated alias."""

from __future__ import annotations

import argparse
import re

from sdd_cli.cli import _HELP_DETAILS, build_parser
from sdd_cli.content import CLI_NAME, CONTENT_DIR, LEGACY_CLI_NAME

_TEXT_SUFFIXES = {".md", ".mdc", ".toml"}


def _commands() -> list[str]:
    action = next(a for a in build_parser()._actions if isinstance(a, argparse._SubParsersAction))
    return sorted(action.choices)


def _legacy_invocation() -> re.Pattern[str]:
    """`sdd <real subcommand>`, but not `sddkit ...`, `.sdd ...` or `sdd-...`."""
    names = "|".join(_commands())
    return re.compile(rf"(?<![\w.-]){re.escape(LEGACY_CLI_NAME)} ({names})\b")


def test_the_new_name_is_not_a_prefix_trap():
    assert CLI_NAME == "sddkit" and LEGACY_CLI_NAME == "sdd"
    assert not _legacy_invocation().search("run `sddkit doctor` after .sdd init and sdd-close")


def test_the_guard_does_catch_the_old_spelling():
    assert _legacy_invocation().search("then run `sdd doctor`")


def test_no_managed_file_teaches_the_old_command():
    rx = _legacy_invocation()
    offenders = []
    for path in sorted(CONTENT_DIR.rglob("*")):
        if path.is_file() and path.suffix in _TEXT_SUFFIXES:
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if rx.search(line):
                    offenders.append(f"{path.relative_to(CONTENT_DIR)}:{number}")
    assert not offenders, "managed text still says `sdd <command>`: " + ", ".join(offenders)


def test_no_help_text_teaches_the_old_command():
    rx = _legacy_invocation()
    offenders = [key for key, (description, examples) in _HELP_DETAILS.items()
                 if rx.search(description) or rx.search(examples)]
    assert not offenders, f"help for {', '.join(offenders)} still says `sdd <command>`"


def test_the_manual_and_readme_explain_the_alias():
    manual = (CONTENT_DIR / "USAGE.md").read_text(encoding="utf-8")
    readme = (CONTENT_DIR / "sdd" / "README.md").read_text(encoding="utf-8")
    assert "deprecated" in manual and "removed in v5" in manual and "`sdd`" in manual
    assert "still works until v5" in " ".join(readme.split())
