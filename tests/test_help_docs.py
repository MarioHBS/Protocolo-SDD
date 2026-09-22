"""The CLI's --help and the manual agents read must stay complete and truthful.

The 4.0.0 manual documented five commands while the CLI had thirteen; these tests
make that regression impossible: a command, an option or an example that is not
documented (or does not parse) fails the suite.
"""

from __future__ import annotations

import argparse
import re
import shlex

from sdd_cli import _findings
from sdd_cli.cli import build_parser
from sdd_cli.content import CONTENT_DIR


def _walk(parser: argparse.ArgumentParser, path: tuple[str, ...] = ()):
    """Yield (command path, parser) for every sub-command, recursively."""
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for name, child in action.choices.items():
                yield (*path, name), child
                yield from _walk(child, (*path, name))


def _manual() -> str:
    return (CONTENT_DIR / "USAGE.md").read_text(encoding="utf-8")


def _documented(manual: str, path: tuple[str, ...]) -> bool:
    """`sdd a b` spelled out, or `b` listed in the `sdd a <b|c|d>` heading of its parent."""
    if f"sdd {' '.join(path)}" in manual:
        return True
    if len(path) == 2:
        return bool(re.search(rf"sdd {re.escape(path[0])} <[^>]*\b{re.escape(path[1])}\b[^>]*>", manual))
    return False


def test_every_command_and_subcommand_is_in_the_usage_manual():
    manual = _manual()
    missing = [" ".join(path) for path, _ in _walk(build_parser()) if not _documented(manual, path)]
    assert not missing, f"undocumented commands: {', '.join(missing)}"


def test_every_parser_action_has_help_when_it_is_user_facing():
    def check(parser):
        for action in parser._actions:
            if action.dest not in {"help", "==SUPPRESS=="} and not isinstance(action, argparse._SubParsersAction):
                assert action.help is not None, f"missing help for {parser.prog} {action.dest}"
            if isinstance(action, argparse._SubParsersAction):
                for child in action.choices.values():
                    check(child)
    check(build_parser())


def test_every_command_explains_itself_and_every_subcommand_is_listed_with_help():
    parser = build_parser()
    for path, child in _walk(parser):
        assert child.description, f"sdd {' '.join(path)} has no description"
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            assert all(item.help for item in action._choices_actions), "a top-level command has no help line"


def test_every_documented_example_actually_parses():
    parser = build_parser()
    checked = 0
    for path, child in _walk(parser):
        for line in (child.epilog or "").splitlines():
            line = line.strip()
            if not line.startswith("sdd ") or "|" in line:
                continue
            argv = shlex.split(re.split(r"\s+#\s", line)[0])[1:]
            try:
                parser.parse_args(argv)
            except SystemExit as exc:  # argparse exits on an invalid command line
                raise AssertionError(f"example does not parse: {line!r} (from sdd {' '.join(path)})") from exc
            checked += 1
    assert checked >= 20  # guards against the loop silently checking nothing


def test_manual_mentions_every_doctor_finding_code():
    manual = _manual()
    undocumented = [code for code in _findings._TEXT if f"`{code}`" not in manual
                    and code not in {"track_not_started", "track_not_incorporated"}]
    # The two track hygiene codes are documented together in one row; every other code has its own mention.
    assert not undocumented, f"doctor codes missing from the manual: {', '.join(undocumented)}"


def test_deprecated_docs_alias_says_so():
    parser = build_parser()
    docs = dict(_walk(parser))[("docs",)]
    description = (docs.description or "").lower()
    assert "deprecated" in description
    assert "v5" in description  # the -h text itself must say when it's removed, not just the full manual


def test_docs_md_without_a_file_writes_inside_sdd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".sdd").mkdir()
    parser = build_parser()
    args = parser.parse_args(["docs", "--md"])
    args.func(args)
    assert (tmp_path / ".sdd" / "SDD-USAGE.md").exists()
    assert not (tmp_path / "SDD-USAGE.md").exists()
