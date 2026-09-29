"""The entry point: argument errors, the safety net for unexpected failures, and quiet exits."""

from __future__ import annotations

import argparse

import pytest

from sdd_cli import cli


def _fake_cli(monkeypatch, func) -> None:
    """Make `sdd boom` call `func`, so main()'s error handling can be exercised in isolation."""
    parser = argparse.ArgumentParser(prog="sdd")
    parser.add_subparsers(dest="command", required=True).add_parser("boom").set_defaults(func=func)
    monkeypatch.setattr(cli, "build_parser", lambda: parser)


def test_version_flag_prints_the_kit_version(capsys):
    with pytest.raises(SystemExit) as error:
        cli.main(["--version"])
    assert error.value.code == 0
    assert capsys.readouterr().out.strip().startswith("sdd ")


def test_a_missing_command_is_a_usage_error(capsys):
    with pytest.raises(SystemExit) as error:
        cli.main([])
    assert error.value.code == 2
    assert "usage" in capsys.readouterr().err.lower()


def test_an_unknown_command_is_a_usage_error():
    with pytest.raises(SystemExit) as error:
        cli.main(["frobnicate"])
    assert error.value.code == 2


def test_an_unexpected_failure_is_a_one_line_error_not_a_traceback(monkeypatch, capsys):
    def boom(_args):
        raise PermissionError("[Errno 13] Permission denied: '.sdd/README.md'")

    monkeypatch.delenv("SDD_DEBUG", raising=False)
    _fake_cli(monkeypatch, boom)
    with pytest.raises(SystemExit) as error:
        cli.main(["boom"])
    assert error.value.code == 1
    err = capsys.readouterr().err
    assert err.startswith("error: unexpected error:") and "Permission denied" in err
    assert "Traceback" not in err


def test_sdd_debug_shows_the_traceback(monkeypatch):
    def boom(_args):
        raise RuntimeError("kaboom")

    _fake_cli(monkeypatch, boom)
    monkeypatch.setenv("SDD_DEBUG", "1")
    with pytest.raises(RuntimeError, match="kaboom"):
        cli.main(["boom"])


def test_ctrl_c_exits_quietly(monkeypatch, capsys):
    def interrupted(_args):
        raise KeyboardInterrupt

    _fake_cli(monkeypatch, interrupted)
    with pytest.raises(SystemExit) as error:
        cli.main(["boom"])
    assert error.value.code in (1, 130)
    assert "Traceback" not in capsys.readouterr().err


def test_a_deliberate_exit_code_is_not_swallowed_by_the_safety_net(monkeypatch):
    def refuse(_args):
        raise SystemExit(2)

    _fake_cli(monkeypatch, refuse)
    with pytest.raises(SystemExit) as error:
        cli.main(["boom"])
    assert error.value.code == 2


def test_docs_alias_still_prints_the_manual(capsys):
    cli.main(["docs"])
    assert "usage manual" in capsys.readouterr().out


def test_output_is_utf8_even_when_the_stream_uses_the_console_code_page(monkeypatch):
    import io
    import sys

    raw = io.BytesIO()
    monkeypatch.setattr(sys, "stdout", io.TextIOWrapper(raw, encoding="cp1252", newline="\n", write_through=True))
    cli._use_utf8_streams()
    print("\u2014 \u00a7 \u65e5")                       # cp1252 has no CJK: must not crash
    assert raw.getvalue().decode("utf-8") == "\u2014 \u00a7 \u65e5\n"


def test_a_stream_without_reconfigure_is_left_alone(monkeypatch):
    import sys

    class Plain:
        def write(self, text):
            return len(text)

    monkeypatch.setattr(sys, "stdout", Plain())
    monkeypatch.setattr(sys, "stderr", Plain())
    cli._use_utf8_streams()                                # must not raise
