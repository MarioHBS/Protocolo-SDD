from __future__ import annotations

import argparse

from sdd_cli.cli import build_parser
from sdd_cli.content import CONTENT_DIR


def test_every_top_level_command_is_in_usage_manual():
    manual = (CONTENT_DIR / "USAGE.md").read_text(encoding="utf-8")
    parser = build_parser()
    action = next(item for item in parser._actions if isinstance(item, argparse._SubParsersAction))
    missing = [name for name in action.choices if f"`sdd {name}" not in manual]
    assert not missing, f"undocumented commands: {', '.join(missing)}"


def test_every_parser_action_has_help_when_it_is_user_facing():
    def walk(parser):
        for action in parser._actions:
            if action.dest not in {"help", "==SUPPRESS=="} and not isinstance(action, argparse._SubParsersAction):
                assert action.help is not None, f"missing help for {parser.prog} {action.dest}"
            if isinstance(action, argparse._SubParsersAction):
                for child in action.choices.values():
                    walk(child)
    walk(build_parser())
