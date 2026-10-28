from __future__ import annotations

import subprocess
import types
import webbrowser
from pathlib import Path

import pytest

from sdd_cli import _proposals, _proposals_send
from sdd_cli.cli import cmd_proposals

FILE_A = """\
## IP-001 — Gate sem critério
- **Data:** 2026-08-02
- **Status:** aberta

**Contexto (episódio real).** Rodei no projeto e nada avisou.

## IP-002 — Já resolvido
- **Data:** 2026-08-03
- **Status:** absorvida pelo kit (4.2.0)

**Contexto (episódio real).** Corrigido.
"""

FILE_B = """\
## IP-001 — Outro atrito
- **Data:** 2026-09-01
- **Status:** proposta

**Proposta para o kit.** Algo diferente.
"""


def _project(base: Path, name: str, proposals: str) -> Path:
    root = base / name
    (root / ".sdd").mkdir(parents=True)
    (root / ".sdd" / "improvement-proposals.md").write_text(proposals, encoding="utf-8", newline="\n")
    return root


@pytest.fixture
def inbox(tmp_path, monkeypatch):
    path = tmp_path / "inbox"
    monkeypatch.setenv("SDD_PROPOSALS_INBOX", str(path))
    monkeypatch.chdir(tmp_path)
    _proposals.collect([_project(tmp_path, "secretapp", FILE_A), _project(tmp_path, "otherapp", FILE_B)], path)
    return path


def _send(**values):
    base = {"proposals_command": "send", "ids": [], "source": None, "via": "file", "all": False,
            "output": None, "snapshot": None, "yes": False}
    return types.SimpleNamespace(**{**base, **values})


def _terminal(monkeypatch, answers: list[str] | None, tty: bool = True):
    """Fake a terminal that answers each prompt from ``answers`` in turn."""
    monkeypatch.setattr("sys.stdin", types.SimpleNamespace(isatty=lambda: tty))
    queue = list(answers or [])
    prompts: list[str] = []

    def fake_input(prompt=""):
        prompts.append(prompt)
        return queue.pop(0)

    monkeypatch.setattr("builtins.input", fake_input)
    return prompts


# ------------------------------------------------------------------- scan

@pytest.mark.parametrize(("text", "kind"), [
    ("escreva para dono@example.com", "email"),
    ("abri C:\\Users\\maria\\projeto\\x.md", "path"),
    ("abri C:/Users/maria/projeto", "path"),
    ("fica em /home/maria/app", "path"),
    ("fica em /Users/maria/app", "path"),
    ("a api_key vazou", "secret"),
    ("o Token expirou", "secret"),
    ("a senha foi trocada", "secret"),
])
def test_scan_finds_each_kind(text, kind):
    assert [h["kind"] for h in _proposals_send.scan_private(text)] == [kind]


@pytest.mark.parametrize("text", [
    "veja https://github.com/x/y e http://example.org",
    "a lista de tokens do contexto",
    "um caminho relativo docs/release/PLAN.md",
    "",
])
def test_scan_is_quiet_on_ordinary_text(text):
    assert _proposals_send.scan_private(text) == []


def test_scan_reports_line_number_and_context():
    hit = _proposals_send.scan_private("primeira\nfale com a@b.co hoje\n")[0]
    assert (hit["line"], hit["match"]) == (2, "a@b.co")
    assert "fale com" in hit["context"]


def test_scan_flags_real_project_names_but_not_short_ones_or_substrings():
    text = "no SecretApp deu erro; secretapps não conta; em ab também não"
    hits = _proposals_send.scan_private(text, ["secretapp", "ab"])
    assert [(h["kind"], h["match"]) for h in hits] == [("project-name", "SecretApp")]


# ---------------------------------------------------------------- package

def test_package_uses_anonymous_codes_and_drops_folder_names(inbox):
    entries = _proposals.load(inbox)
    codes = _proposals.aliases(entries, inbox)
    title, text = _proposals_send.build_package(entries, codes, "4.4.0")
    assert "### P1-IP-001 — Outro atrito" not in text  # otherapp is P2
    assert "### P2-IP-001 — Outro atrito" in text and "### P1-IP-001 — Gate sem critério" in text
    assert "**Kit version:** 4.4.0" in text and "## Friction and failures" in text
    assert "secretapp" not in text and "otherapp" not in text
    assert title.startswith("sdd-cli improvement proposals (3 from 2")


def test_package_appends_the_snapshot_as_a_json_block(inbox):
    entries = _proposals.load(inbox)[:1]
    _, text = _proposals_send.build_package(entries, _proposals.aliases(entries, inbox), "4.4.0", '{"a": 1}\n')
    assert "## Context and performance" in text and '```json\n{"a": 1}\n```' in text


# ------------------------------------------------------------- via file

def test_send_via_file_needs_no_network_and_skips_absorbed_by_default(inbox, tmp_path, monkeypatch, capsys):
    _terminal(monkeypatch, None, tty=False)
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: pytest.fail("no process may run"))
    monkeypatch.setattr(webbrowser, "open", lambda *a, **k: pytest.fail("no browser may open"))
    cmd_proposals(_send(output=str(tmp_path / "out" / "pkg.md")))
    text = (tmp_path / "out" / "pkg.md").read_text(encoding="utf-8")
    assert "Gate sem critério" in text and "Outro atrito" in text
    assert "Já resolvido" not in text
    assert "Nothing was sent" in capsys.readouterr().out


def test_send_all_includes_absorbed(inbox, tmp_path, monkeypatch):
    _terminal(monkeypatch, None, tty=False)
    cmd_proposals(_send(all=True, output=str(tmp_path / "pkg.md")))
    assert "Já resolvido" in (tmp_path / "pkg.md").read_text(encoding="utf-8")


def test_send_named_ids_only(inbox, tmp_path, monkeypatch):
    _terminal(monkeypatch, None, tty=False)
    cmd_proposals(_send(ids=["otherapp-IP-001"], output=str(tmp_path / "pkg.md")))
    text = (tmp_path / "pkg.md").read_text(encoding="utf-8")
    assert "Outro atrito" in text and "Gate sem critério" not in text


def test_send_ambiguous_or_unknown_id_fails(inbox, monkeypatch, capsys):
    _terminal(monkeypatch, None, tty=False)
    with pytest.raises(SystemExit):
        cmd_proposals(_send(ids=["IP-001"]))
    assert "otherapp-IP-001" in capsys.readouterr().err
    with pytest.raises(SystemExit):
        cmd_proposals(_send(ids=["nope-IP-009"]))
    assert "no proposal nope-IP-009" in capsys.readouterr().err


def test_send_never_overwrites_an_existing_package(inbox, tmp_path, monkeypatch, capsys):
    _terminal(monkeypatch, None, tty=False)
    target = tmp_path / "pkg.md"
    target.write_text("mine", encoding="utf-8")
    with pytest.raises(SystemExit):
        cmd_proposals(_send(output=str(target)))
    assert target.read_text(encoding="utf-8") == "mine"
    assert "already exists" in capsys.readouterr().err


def test_send_with_an_empty_inbox_says_what_to_do(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("SDD_PROPOSALS_INBOX", str(tmp_path / "empty"))
    with pytest.raises(SystemExit):
        cmd_proposals(_send())
    assert "sdd proposals collect" in capsys.readouterr().err


def test_send_leaves_inbox_and_projects_untouched(inbox, tmp_path, monkeypatch):
    _terminal(monkeypatch, None, tty=False)
    before = {p: p.read_bytes() for p in sorted(tmp_path.rglob("*")) if p.is_file()}
    cmd_proposals(_send(output=str(tmp_path / "pkg.md")))
    after = {p: p.read_bytes() for p in sorted(tmp_path.rglob("*")) if p.is_file() and p.name != "pkg.md"}
    assert after == before


# --------------------------------------------------------- private data

def _dirty_inbox(tmp_path, monkeypatch, line: str) -> Path:
    path = tmp_path / "inbox2"
    monkeypatch.setenv("SDD_PROPOSALS_INBOX", str(path))
    monkeypatch.chdir(tmp_path)
    body = FILE_B.replace("Algo diferente.", line)
    _proposals.collect([_project(tmp_path, "dirty", body)], path)
    return path


def test_a_hit_without_a_terminal_stops_everything(tmp_path, monkeypatch, capsys):
    _dirty_inbox(tmp_path, monkeypatch, "Fale com dono@example.com.")
    _terminal(monkeypatch, None, tty=False)
    with pytest.raises(SystemExit):
        cmd_proposals(_send(output=str(tmp_path / "pkg.md"), yes=True))
    assert not (tmp_path / "pkg.md").exists()
    assert "dono@example.com" in capsys.readouterr().out


def test_declining_one_hit_aborts_and_writes_nothing(tmp_path, monkeypatch, capsys):
    _dirty_inbox(tmp_path, monkeypatch, "Veja C:\\Users\\maria\\x e dono@example.com.")
    prompts = _terminal(monkeypatch, ["y", "n"])
    cmd_proposals(_send(output=str(tmp_path / "pkg.md")))
    assert len(prompts) == 2
    assert not (tmp_path / "pkg.md").exists()
    assert "aborted; nothing was sent" in capsys.readouterr().out


def test_every_hit_is_asked_separately_and_yes_lets_the_file_through(tmp_path, monkeypatch):
    _dirty_inbox(tmp_path, monkeypatch, "Veja C:\\Users\\maria\\x e dono@example.com.")
    prompts = _terminal(monkeypatch, ["y", "y"])
    cmd_proposals(_send(output=str(tmp_path / "pkg.md")))
    assert len(prompts) == 2 and (tmp_path / "pkg.md").is_file()


def test_the_yes_flag_does_not_skip_the_hit_prompts(tmp_path, monkeypatch):
    _dirty_inbox(tmp_path, monkeypatch, "Fale com dono@example.com.")
    prompts = _terminal(monkeypatch, ["n"])
    monkeypatch.setattr(webbrowser, "open", lambda *a, **k: pytest.fail("must not open"))
    cmd_proposals(_send(via="url", yes=True))
    assert len(prompts) == 1


# ----------------------------------------------------------- via url/issue

def test_url_shows_the_text_asks_and_opens_a_prefilled_issue(inbox, monkeypatch, capsys):
    prompts = _terminal(monkeypatch, ["y"])
    opened: list[str] = []
    monkeypatch.setattr(webbrowser, "open", lambda url, *a, **k: opened.append(url) or True)
    cmd_proposals(_send(via="url"))
    out = capsys.readouterr().out
    assert "Gate sem critério" in out and "end of package" in out
    assert len(prompts) == 1 and "via url" in prompts[0]
    assert opened[0].startswith(f"https://github.com/{_proposals_send.KIT_REPO}/issues/new?title=")
    assert "secretapp" not in opened[0]


def test_url_declined_opens_nothing(inbox, monkeypatch, capsys):
    _terminal(monkeypatch, ["n"])
    monkeypatch.setattr(webbrowser, "open", lambda *a, **k: pytest.fail("must not open"))
    cmd_proposals(_send(via="url"))
    assert "nothing was sent" in capsys.readouterr().out


def test_url_without_a_terminal_requires_yes(inbox, monkeypatch, capsys):
    _terminal(monkeypatch, None, tty=False)
    with pytest.raises(SystemExit):
        cmd_proposals(_send(via="url"))
    assert "requires --yes" in capsys.readouterr().err


def test_url_too_long_degrades_to_a_file_with_a_warning(inbox, tmp_path, monkeypatch, capsys):
    _terminal(monkeypatch, None, tty=False)
    monkeypatch.setattr(_proposals_send, "URL_LIMIT", 50)
    monkeypatch.setattr(webbrowser, "open", lambda *a, **k: pytest.fail("must not open"))
    cmd_proposals(_send(via="url", yes=True, output=str(tmp_path / "pkg.md")))
    assert (tmp_path / "pkg.md").is_file()
    assert "too long" in capsys.readouterr().out


def test_create_issue_runs_gh_with_the_body_on_stdin():
    calls: list[tuple[list[str], dict]] = []

    def run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        out = "https://github.com/x/y/issues/7\n" if cmd[1] == "issue" else ""
        return subprocess.CompletedProcess(cmd, 0, stdout=out, stderr="")

    created, reason = _proposals_send.create_issue("title", "body", which=lambda name: "gh", run=run)
    assert (created, reason) == ("https://github.com/x/y/issues/7", "")
    command, kwargs = calls[-1]
    assert command[:3] == ["gh", "issue", "create"] and kwargs["input"] == "body"
    assert command[command.index("--repo") + 1] == _proposals_send.KIT_REPO


@pytest.mark.parametrize(("which", "run_result", "reason"), [
    (lambda name: None, None, "not installed"),
    (lambda name: "gh", subprocess.CompletedProcess([], 1, stdout="", stderr="not logged in"), "not authenticated"),
])
def test_create_issue_reports_why_it_cannot_run(which, run_result, reason):
    created, why = _proposals_send.create_issue(
        "t", "b", which=which, run=lambda *a, **k: run_result)
    assert created is None and reason in why


def test_create_issue_reports_a_gh_failure():
    def run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 1 if cmd[1] == "issue" else 0, stdout="", stderr="HTTP 403")

    created, why = _proposals_send.create_issue("t", "b", which=lambda name: "gh", run=run)
    assert created is None and "HTTP 403" in why


def test_issue_without_gh_falls_back_to_a_file_and_says_so(inbox, tmp_path, monkeypatch, capsys):
    _terminal(monkeypatch, None, tty=False)
    monkeypatch.setattr(_proposals_send, "create_issue", lambda t, b: (None, "the GitHub CLI (gh) is not installed"))
    cmd_proposals(_send(via="issue", yes=True, output=str(tmp_path / "pkg.md")))
    out = capsys.readouterr().out
    assert "warning: the GitHub CLI (gh) is not installed" in out
    assert (tmp_path / "pkg.md").is_file()


def test_issue_success_prints_the_created_link(inbox, monkeypatch, capsys):
    _terminal(monkeypatch, ["y"])
    monkeypatch.setattr(_proposals_send, "create_issue", lambda t, b: ("https://github.com/x/y/issues/7", ""))
    cmd_proposals(_send(via="issue"))
    assert "created https://github.com/x/y/issues/7" in capsys.readouterr().out


def test_closed_stdin_at_a_prompt_counts_as_no(tmp_path, monkeypatch, capsys):
    _dirty_inbox(tmp_path, monkeypatch, "Fale com dono@example.com.")
    _terminal(monkeypatch, None)

    def closed(prompt=""):
        raise EOFError

    monkeypatch.setattr("builtins.input", closed)
    cmd_proposals(_send(output=str(tmp_path / "pkg.md")))
    assert not (tmp_path / "pkg.md").exists()
    assert "aborted; nothing was sent" in capsys.readouterr().out
