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
    assert capsys.readouterr().out.strip().startswith("sddkit ")


# ------------------------------------------------- the new name and the old alias

@pytest.mark.parametrize("argv0", [
    "sdd", "sdd.exe", "SDD.EXE", "/home/u/.local/bin/sdd", "C:\\Users\\u\\.local\\bin\\sdd.exe",
])
def test_the_old_name_gets_a_deprecation_notice(argv0):
    notice = cli.legacy_name_notice(argv0)
    assert notice is not None and "deprecated" in notice and "removed in v5" in notice
    assert "`sddkit`" in notice


@pytest.mark.parametrize("argv0", [
    "sddkit", "sddkit.exe", "C:\\bin\\sddkit.EXE", "/x/y/__main__.py", "pytest", "", None,
])
def test_the_new_name_and_module_runs_stay_quiet(argv0):
    assert cli.legacy_name_notice(argv0) is None


def test_the_notice_goes_to_stderr_and_stdout_is_untouched(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["sdd", "--version"])
    with pytest.raises(SystemExit):
        cli.main()
    out, err = capsys.readouterr()
    assert out.strip() == f"sddkit {cli.KIT_VERSION}"
    assert err.strip().startswith("warning: `sdd` is deprecated")


def test_the_new_name_prints_no_notice(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["sddkit", "--version"])
    with pytest.raises(SystemExit):
        cli.main()
    assert capsys.readouterr().err == ""


def test_explicit_argv_never_warns(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["sdd"])
    with pytest.raises(SystemExit):
        cli.main(["--version"])
    assert capsys.readouterr().err == ""


def test_both_entry_points_are_declared_for_the_same_function():
    import tomllib
    from pathlib import Path

    scripts = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"]["scripts"]
    assert scripts == {"sddkit": "sdd_cli.cli:main", "sdd": "sdd_cli.cli:main"}


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
