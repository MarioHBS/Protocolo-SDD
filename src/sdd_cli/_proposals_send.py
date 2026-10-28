"""Turn collected proposals into a package the maintainer can receive.

``build_package`` replaces each project's folder name with its anonymous code;
``scan_private`` then looks for what must not leave the machine by accident
(e-mails, absolute system paths, secret-looking words, the real project names).
The scan is a heuristic, not a guarantee: the caller shows every hit and asks
before anything is delivered. Nothing here touches the projects or the inbox.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import urllib.parse
from collections.abc import Callable
from pathlib import Path

KIT_REPO = "MarioHBS/Protocolo-SDD"
# Browsers and GitHub reject very long query strings; past this, `--via url` degrades to a file.
URL_LIMIT = 7000

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
# A drive path (C:\... or C:/...) or /home, /Users, /root. The lookbehind keeps
# the "p:/" inside "http://" from matching.
_PATH_RE = re.compile(r"(?<![\w.])(?:[A-Za-z]:[\\/]|/(?:home|Users|root)/)[^\s`\"'<>|)\]]*")
_SECRET_RE = re.compile(r"(?i)\b(?:api[_-]?key|token|secret|password|senha)\b")


# ---------------------------------------------------------------- package

def _demoted(entry: dict, alias: str) -> str:
    """The entry's text with its ``## IP-NNN`` heading rewritten as ``### <alias>-IP-NNN``."""
    _, _, rest = entry["body"].partition("\n")
    return f"### {alias}-{entry['id']} — {entry['title']}\n{rest}"


def build_package(entries: list[dict], codes: dict[str, str], kit_version: str,
                  snapshot: str | None = None) -> tuple[str, str]:
    """``(title, markdown)`` following the sections of ``kit-evaluation.template.md``."""
    projects = sorted({codes[e["project"]] for e in entries}, key=lambda c: (len(c), c))
    title = f"sdd-cli improvement proposals ({len(entries)} from {len(projects)} project(s))"
    lines = [
        "# Kit evaluation — improvement proposals", "",
        f"- **Kit version:** {kit_version}",
        f"- **Projects:** {', '.join(projects)} (anonymous codes)",
        f"- **Proposals:** {len(entries)}", "",
        "## Friction and failures", "",
    ]
    for entry in entries:
        lines += [_demoted(entry, codes[entry["project"]]).rstrip(), ""]
    if snapshot:
        lines += ["## Context and performance", "", "```json", snapshot.strip(), "```", ""]
    return title, "\n".join(lines)


# ------------------------------------------------------------------- scan

def scan_private(text: str, names: list[str] | None = None) -> list[dict]:
    """Every line-level hit as ``{"kind", "line", "match", "context"}``, in text order.

    ``names`` are the real project names; a name shorter than three characters
    is skipped, since it would match ordinary words.
    """
    named = [re.compile(rf"(?i)(?<![\w-]){re.escape(n)}(?![\w-])") for n in names or [] if len(n) >= 3]
    checks = [("email", _EMAIL_RE), ("path", _PATH_RE), ("secret", _SECRET_RE),
              *(("project-name", rx) for rx in named)]
    hits: list[dict] = []
    for number, line in enumerate(text.splitlines(), start=1):
        for kind, rx in checks:
            for match in rx.finditer(line):
                context = line.strip()
                hits.append({"kind": kind, "line": number, "match": match.group(0),
                             "context": context if len(context) <= 100 else context[:97] + "..."})
    return hits


# --------------------------------------------------------------- delivery

def issue_url(title: str, body: str, repo: str = KIT_REPO) -> str | None:
    """Pre-filled "new issue" page, or ``None`` when it would be too long to open."""
    query = urllib.parse.urlencode({"title": title, "body": body}, quote_via=urllib.parse.quote)
    url = f"https://github.com/{repo}/issues/new?{query}"
    return url if len(url) <= URL_LIMIT else None


def create_issue(title: str, body: str, repo: str = KIT_REPO,
                 which: Callable = shutil.which, run: Callable = subprocess.run) -> tuple[str | None, str]:
    """``(issue_url, "")`` when ``gh`` created it, else ``(None, reason)``."""
    if which("gh") is None:
        return None, "the GitHub CLI (gh) is not installed"
    try:
        if run(["gh", "auth", "status"], capture_output=True, text=True, timeout=30).returncode != 0:
            return None, "gh is not authenticated (run `gh auth login`)"
        done = run(["gh", "issue", "create", "--repo", repo, "--title", title, "--body-file", "-"],
                   input=body, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, f"gh failed: {exc}"
    if done.returncode != 0:
        return None, f"gh could not create the issue: {(done.stderr or '').strip() or 'unknown error'}"
    return (done.stdout or "").strip(), ""


def write_package(path: Path, text: str) -> None:
    """Write the package; refuses to overwrite so a second run never clobbers the first."""
    if path.exists():
        raise FileExistsError(f"{path} already exists; pick another with --output")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
