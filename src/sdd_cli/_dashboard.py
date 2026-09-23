"""The read-only dashboard: one data model, four renderers.

``build_views`` turns the doctor/context data the CLI already computes into six
plain-text views. ``render_plain`` needs nothing, ``render_rich`` and ``make_app``
(Textual) import their optional libraries lazily, so a missing extra is an
explained error, never an ``ImportError`` traceback.
"""

from __future__ import annotations

from pathlib import Path

from . import _findings

VIEW_NAMES = ("Overview", "Constitution", "Stages / Tracks", "EDD", "Doctor / Fix", "Session")
INSTALL_HINT = ("the {ui} dashboard needs an optional package. From the sdd-cli folder run\n"
                "  pipx install --force './sdd-cli[dashboard]'      (or: pip install rich textual)\n"
                "or use the dependency-free view:  sdd dashboard --ui plain")


def _health(findings: list[dict]) -> tuple[int, int, int]:
    errors = sum(x["severity"] == "error" for x in findings)
    warnings = sum(x["severity"] == "warn" for x in findings)
    return max(0, 100 - errors * 25 - warnings * 5), errors, warnings


def _stage_status(stage: Path) -> str:
    if (stage / "report.md").is_file():
        return "done"
    return "in progress" if (stage / "spec.md").is_file() else "pending"


def build_views(root: Path, doctor: dict, context: dict, sections: list[tuple[str, int]],
                session: dict | None, edd_on: bool) -> dict[str, str]:
    sdd = root / ".sdd"
    findings = doctor["findings"]
    score, errors, warnings = _health(findings)

    overview = [f"kit: {doctor.get('sdd') or 'not initialized'}",
                f"state: {context.get('state') or 'unknown'}",
                f"active stage: {context.get('active_stage') or '(none)'}",
                f"health: {score}/100 ({errors} error(s), {warnings} warning(s))"]
    if "startup_estimated_tokens" in context:
        overview.append(f"startup cost: ~{context['startup_estimated_tokens']} tokens "
                        f"(reading the whole constitution would be ~{context.get('full_read_estimated_tokens', '?')})")

    hot = {"Settings", "Current state"}
    constitution = [f"{size:>8} B  {'hot ' if name in hot else 'cold'}  {name}" for name, size in sections]
    if constitution:
        constitution.append("\nhot = read at every session start; cold = only when a task needs it")

    stage_dirs = sorted(p for p in (sdd / "stages").iterdir() if p.is_dir()) if (sdd / "stages").is_dir() else []
    track_dirs = sorted(p for p in (sdd / "tracks").iterdir() if p.is_dir() and not p.name.startswith(".")) \
        if (sdd / "tracks").is_dir() else []
    stages = [f"stages ({len(stage_dirs)}):"] + [f"  {p.name}  [{_stage_status(p)}]" for p in stage_dirs]
    tracks = [f"tracks ({len(track_dirs)}):"]
    for p in track_dirs:
        claims = p / "claims.json"
        tracks.append(f"  {p.name}  ({'footprint declared' if claims.is_file() else 'no footprint'})")

    edd: list[str] = []
    by_stage: dict[str, list[str]] = {}
    for item in findings:
        if item["code"].startswith("edd_") and item.get("stage"):
            by_stage.setdefault(item["stage"], []).append(
                f"{item['eval']} has no evidence" if item.get("eval") else item["code"].removeprefix("edd_"))
    for stage, notes in by_stage.items():
        edd.append(f"{stage}: " + "; ".join(notes))
    edd += [_findings.describe(f)[0] for f in findings
            if f["code"] in {"edd_milestone_without_evaluation", "milestone_not_contiguous",
                             "edd_missing_performance_doc"}]

    grouped = _findings.group(findings)
    order = {"error": 0, "warn": 1, "note": 2}
    fix = []
    for item in sorted(grouped, key=lambda g: order.get(g["severity"], 3)):
        count = f" (x{item['count']})" if item["count"] > 1 else ""
        fix.append(f"{item['severity'].upper():5} {item['code']}{count}\n      {item['message']}"
                   + (f"\n      fix: {item['hint']}" if item["hint"] else ""))

    if session and not session.get("invalid"):
        lines = [f"state: {session.get('state')}", f"stage: {session.get('active_stage') or '(none)'}",
                 f"branch: {session.get('branch') or '(not recorded)'}"]
        if session.get("active_task"):
            lines.append(f"task: {session['active_task'].get('id')}")
        if session.get("interruption_reason"):
            lines.append(f"paused: {session['interruption_reason']} at {session.get('interrupted_at')}")
        lines += [f"hint: {hint}" for hint in session.get("resume_hints", [])]
        session_text = "\n".join(lines)
    else:
        session_text = "session file is invalid" if session else "no session (nothing to resume)"

    return {
        "Overview": "\n".join(overview),
        "Constitution": "\n".join(constitution) or "no constitution found",
        "Stages / Tracks": "\n".join(stages + [""] + tracks),
        "EDD": "\n".join(edd) or ("no eval gaps found" if edd_on else "Eval Driven Development is off"),
        "Doctor / Fix": "\n\n".join(fix) or "clean",
        "Session": session_text,
    }


def render_plain(views: dict[str, str]) -> str:
    out = ["SDD Dashboard"]
    for name, text in views.items():
        out += ["", f"== {name} ==", text]
    return "\n".join(out)


def render_html(views: dict[str, str], generated: str) -> str:
    """One self-contained HTML page (inline CSS, no scripts, no network): open it in the IDE or a browser."""
    from html import escape

    nav = "".join(f'<a href="#v{i}">{escape(name)}</a>' for i, name in enumerate(views))
    body = "".join(f'<section id="v{i}"><h2>{escape(name)}</h2><pre>{escape(text)}</pre></section>'
                   for i, (name, text) in enumerate(views.items()))
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1"><title>SDD Dashboard</title>'
        "<style>:root{--bg:#fff;--fg:#1f2328;--card:#f6f8fa;--line:#d0d7de;--accent:#0969da}"
        "@media(prefers-color-scheme:dark){:root{--bg:#0d1117;--fg:#e6edf3;--card:#161b22;--line:#30363d;--accent:#58a6ff}}"
        "body{margin:0 auto;max-width:960px;padding:16px;background:var(--bg);color:var(--fg);"
        "font:15px/1.5 system-ui,sans-serif}nav{display:flex;flex-wrap:wrap;gap:8px 16px;margin:12px 0}"
        "a{color:var(--accent)}section{background:var(--card);border:1px solid var(--line);"
        "border-radius:8px;padding:0 16px 8px;margin:12px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere;"
        "font:13px/1.45 ui-monospace,Consolas,monospace}small{color:var(--accent)}</style></head><body>"
        f"<h1>SDD Dashboard</h1><small>read-only snapshot generated {escape(generated)} "
        f"- regenerate with <code>sdd dashboard --ui web</code></small><nav>{nav}</nav>{body}</body></html>")


def render_rich(views: dict[str, str], console=None) -> None:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text

    console = console or Console()
    console.print(Text("SDD Dashboard", style="bold"))
    for name, text in views.items():
        console.print(Panel(Text(text), title=name, title_align="left"))


def make_app(views: dict[str, str]):
    from rich.text import Text
    from textual.app import App, ComposeResult
    from textual.containers import VerticalScroll
    from textual.widgets import Footer, Header, Static, TabbedContent, TabPane

    class SDDDashboard(App):
        TITLE = "SDD Dashboard"
        BINDINGS = [("q", "quit", "Quit")]

        def compose(self) -> ComposeResult:
            yield Header()
            with TabbedContent():
                for index, (name, text) in enumerate(views.items()):
                    with TabPane(name, id=f"view-{index}"):
                        with VerticalScroll():
                            yield Static(Text(text))
            yield Footer()

    return SDDDashboard()
