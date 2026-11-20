"""Provider hooks that run the checks the SDD flow already has, without waiting for someone to ask.

Only Claude Code has a tool hook among the providers the kit installs, so this module speaks its
protocol (``PreToolUse`` / ``PostToolUse``, JSON on stdin, JSON on stdout) and nothing else.

Three rules keep the hook from ever getting in the way:

* a hook never blocks. The strongest answer is ``ask``, which hands the decision back to the
  owner; there is no ``deny``;
* a hook never fails the edit. Every error inside ``run`` is swallowed and answers with nothing;
* a hook is a reinforcement. ``track check``, ``track guard`` and ``doctor`` run by hand give the
  same answers with no hook installed.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from collections.abc import Callable
from pathlib import Path

from . import _tracks

EDIT_MATCHER = "Edit|Write|MultiEdit"
EVENTS = {"pre-edit": "PreToolUse", "post-edit": "PostToolUse"}
_TIMEOUTS = {"pre-edit": 10, "post-edit": 60}
_REPORT_RE = re.compile(r"^\.sdd/(?:.+/)?report\.md\Z")
_MAX_CODES = 8


# ------------------------------------------------------------------ paths

def project_root(payload: dict) -> Path | None:
    """The project the hook fired in: ``CLAUDE_PROJECT_DIR``, else the payload's ``cwd`` walked up."""
    start = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd()
    here = Path(start).resolve()
    for candidate in (here, *here.parents):
        if (candidate / ".sdd").is_dir():
            return candidate
    return None


def relative_path(root: Path, raw: str) -> str | None:
    """``raw`` (absolute, with the host's separators) relative to ``root``, or ``None`` outside it."""
    try:
        target = Path(raw)
        if not target.is_absolute():
            target = root / target
        # relative_to compares case-insensitively on Windows and keeps the path's own case.
        return target.resolve().relative_to(root.resolve()).as_posix()
    except (OSError, ValueError):
        return None


# ----------------------------------------------------------------- events

def _pre_edit(root: Path, rel: str) -> dict | None:
    result = _tracks.guard(root, rel)
    shared = [f for f in result["findings"] if f["kind"] == "track_shared_touch"]
    outside = [f for f in result["findings"] if f["kind"] == "track_outside_footprint"]
    if shared:
        reason = (f"{rel} is claimed by more than one active track ({', '.join(shared[0]['tracks'])}): "
                  "editing it can collide. Confirm, or sequence the later stage after the earlier one.")
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask",
                                       "permissionDecisionReason": reason}}
    if outside:
        found = outside[0]
        who = f" It belongs to track {', '.join(found['owned_by'])}." if found["owned_by"] else ""
        note = (f"track {found['track']}: {rel} is outside this track's declared footprint.{who} "
                "Declare it with `track claim` if this track owns it.")
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": note}}
    return None


def _summarize(payload: dict) -> str:
    counts: dict[str, dict[str, int]] = {"error": {}, "warn": {}}
    notes = 0
    for finding in payload.get("findings", []):
        severity = finding.get("severity")
        if severity in counts:
            code = finding.get("code", "?")
            counts[severity][code] = counts[severity].get(code, 0) + 1
        else:
            notes += 1
    errors, warnings = sum(counts["error"].values()), sum(counts["warn"].values())
    if not errors and not warnings:
        return "sddkit doctor after report.md: clean" + (f" ({notes} note(s))." if notes else ".")
    parts = [f"{code} x{n}" if n > 1 else code
             for severity in ("error", "warn")
             for code, n in sorted(counts[severity].items(), key=lambda item: -item[1])]
    shown = ", ".join(parts[:_MAX_CODES]) + (f", +{len(parts) - _MAX_CODES} more" if len(parts) > _MAX_CODES else "")
    return (f"sddkit doctor after report.md: {errors} error(s), {warnings} warning(s) ({shown}). "
            "Run `sddkit doctor` for the details.")


def _post_edit(root: Path, rel: str, doctor_payload: Callable[[Path], dict]) -> dict | None:
    if not _REPORT_RE.match(rel):
        return None
    return {"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                   "additionalContext": _summarize(doctor_payload(root))}}


def run(event: str, stdin_text: str, doctor_payload: Callable[[Path], dict]) -> str:
    """Answer one hook call. Returns the JSON to print, or an empty string for "nothing to say"."""
    try:
        payload = json.loads(stdin_text) if stdin_text.strip() else {}
        if not isinstance(payload, dict):
            return ""
        tool_input = payload.get("tool_input")
        raw = tool_input.get("file_path") if isinstance(tool_input, dict) else None
        root = project_root(payload)
        if not isinstance(raw, str) or not raw or root is None:
            return ""
        rel = relative_path(root, raw)
        if rel is None:
            return ""
        answer = _pre_edit(root, rel) if event == "pre-edit" else _post_edit(root, rel, doctor_payload)
        return json.dumps(answer) if answer else ""
    except Exception:  # noqa: BLE001 - a hook must never fail the edit it watches
        return ""


# --------------------------------------------------------------- settings

def settings_path(root: Path, local: bool = False) -> Path:
    return root / ".claude" / ("settings.local.json" if local else "settings.json")


def command(event: str, cli_name: str) -> str:
    """The shell line the provider runs. ``|| true`` is not decoration: an older kit that lacks
    ``hooks`` exits 2 on the argparse error, and for Claude Code exit 2 blocks the edit."""
    return f"{cli_name} hooks run {event} || true"


def _is_ours(command: object, cli_name: str) -> bool:
    return isinstance(command, str) and command.startswith(f"{cli_name} hooks run ")


def _load(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path.name} is not valid JSON ({exc}); fix it first, nothing was written") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} must hold a JSON object; nothing was written")
    hooks = data.get("hooks", {})
    if not isinstance(hooks, dict) or any(not isinstance(v, list) for v in hooks.values()):
        raise ValueError(f"{path.name}: 'hooks' has an unexpected shape; nothing was written")
    return data


def _commands(groups: list, cli_name: str) -> list[str]:
    found = []
    for group in groups:
        for hook in group.get("hooks", []) if isinstance(group, dict) else []:
            if isinstance(hook, dict) and _is_ours(hook.get("command"), cli_name):
                found.append(hook["command"])
    return found


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def tracked_by_git(root: Path, path: Path) -> bool | None:
    """Whether Git already tracks ``path`` (None: not a Git repository, or Git is missing)."""
    try:
        done = subprocess.run(["git", "-C", str(root), "ls-files", "--error-unmatch", str(path)],
                              capture_output=True, text=True, timeout=10)
        inside = subprocess.run(["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
                                capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    if inside.returncode != 0:
        return None
    return done.returncode == 0


def _versioned(root: Path, path: Path, local: bool) -> bool:
    """True when the file the hooks go to is one Git tracks or would track (H-05): then every
    clone runs the hook, including people without ``bash`` or the CLI."""
    if local:
        return False
    tracked = tracked_by_git(root, path)
    if tracked is None:
        return False
    if tracked:
        return True
    ignored = subprocess.run(["git", "-C", str(root), "check-ignore", "-q", str(path)], capture_output=True)
    return ignored.returncode != 0


def install(root: Path, cli_name: str, local: bool = False, dry_run: bool = False) -> dict:
    """Register the kit's hooks next to the owner's, once. Returns what was added and where.

    With ``dry_run`` nothing is written; ``preview`` holds the entries that would be added."""
    path = settings_path(root, local)
    data = _load(path)
    hooks = data.setdefault("hooks", {})
    added = []
    preview: dict[str, list] = {}
    for name, event in EVENTS.items():
        line = command(name, cli_name)
        groups = hooks.setdefault(event, [])
        if line in _commands(groups, cli_name):
            continue
        # shell=bash: the `|| true` above is not valid in Windows PowerShell 5.1, which is what
        # Claude Code falls back to when Git Bash is missing; without bash the hook just does not run.
        group = {"matcher": EDIT_MATCHER, "hooks": [
            {"type": "command", "command": line, "shell": "bash", "timeout": _TIMEOUTS[name]}]}
        groups.append(group)
        preview.setdefault(event, []).append(group)
        added.append(name)
    if added and not dry_run:
        _write(path, data)
    return {"file": path, "added": added, "dry_run": dry_run, "preview": preview,
            "versioned": _versioned(root, path, local) if added else False}


def uninstall(root: Path, cli_name: str, local: bool = False, dry_run: bool = False) -> dict:
    """Remove only the entries the kit wrote; the owner's own hooks stay."""
    path = settings_path(root, local)
    data = _load(path)
    hooks = data.get("hooks", {})
    removed = []
    for event in list(hooks):
        kept_groups = []
        for group in hooks[event]:
            inner = group.get("hooks") if isinstance(group, dict) else None
            if not isinstance(inner, list):
                kept_groups.append(group)
                continue
            kept = [h for h in inner if not (isinstance(h, dict) and _is_ours(h.get("command"), cli_name))]
            removed += [h["command"] for h in inner if h not in kept]
            if kept:
                kept_groups.append({**group, "hooks": kept})
        if kept_groups:
            hooks[event] = kept_groups
        else:
            del hooks[event]
    if removed:
        if not hooks:
            data.pop("hooks", None)
        _write(path, data)
    return {"file": path, "removed": removed}


def status(root: Path, cli_name: str) -> dict:
    """Which of the kit's hooks are registered, in either settings file."""
    registered: dict[str, list[str]] = {name: [] for name in EVENTS}
    for local in (False, True):
        path = settings_path(root, local)
        try:
            hooks = _load(path).get("hooks", {})
        except ValueError:
            continue
        for name, event in EVENTS.items():
            if command(name, cli_name) in _commands(hooks.get(event, []), cli_name):
                registered[name].append(path.name)
    return {"hooks": registered, "installed": all(registered.values())}
