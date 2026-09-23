"""The documentation plan: an interview that ends in ``.sdd/documentation.json``.

``sdd document`` asks the user, one question at a time, what documentation the
project needs, where each file lives (it may be outside ``.sdd/`` and even
outside the project folder) and which stages must keep it fresh. The interview
engine here has no I/O of its own -- it talks through an injected ``Console`` --
so it is testable, resumable (answers are saved after every step) and reusable by
an agent through ``--answers FILE``.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

PLAN_NAME = "documentation.json"
STATE_NAME = ".document-interview.json"
DEPTHS = ("minimal", "medium", "comprehensive")
AUDIENCES = ("owner", "collaborator", "auditor")
# Distinct subjects that raise the cost of a wrong document. Deliberately narrow:
# "audit" is not here (stages are often called "audit-...") and only the vision,
# principles and locked decisions are searched, never the stage index.
_RISK_WORDS = re.compile(
    r"(?i)\b(financ\w*|payments?|pagamentos?|compliance|lgpd|gdpr|hipaa|regulat\w*|ledger|"
    r"sa[uú]de|healthcare|fiscal)\b")
_STACK_MARKERS = ("package.json", "pyproject.toml", "requirements.txt", "pom.xml", "go.mod",
                  "Cargo.toml", "composer.json", "Gemfile", "build.gradle", "pubspec.yaml")


class InterviewAborted(Exception):
    """The user interrupted the interview (Ctrl-C / end of input)."""


# ----------------------------------------------------------------- console

@dataclass
class Console:
    """Thin I/O wrapper so the interview can be scripted in tests."""

    read: Callable[[str], str] | None = None
    write: Callable[[str], None] = print

    def say(self, text: str = "") -> None:
        self.write(text)

    def ask(self, prompt: str, default: str | None = None) -> str:
        suffix = f" [{default}]" if default else ""
        try:
            answer = (self.read or input)(f"{prompt}{suffix}: ").strip()
        except (EOFError, KeyboardInterrupt) as exc:
            raise InterviewAborted from exc
        return answer or (default or "")

    def choose(self, prompt: str, options: tuple[str, ...], default: str) -> str:
        while True:
            answer = self.ask(f"{prompt} ({'/'.join(options)})", default).lower()
            if answer in options:
                return answer
            self.say(f"  choose one of: {', '.join(options)}")

    def confirm(self, prompt: str, default: bool = False) -> bool:
        while True:
            answer = self.ask(f"{prompt} (y/n)", "y" if default else "n").lower()
            if answer in ("y", "yes", "s", "sim"):
                return True
            if answer in ("n", "no", "nao", "não"):
                return False
            self.say("  answer y or n")


# --------------------------------------------------------------- validation

def _safe_relative(text: str, what: str) -> Path:
    path = Path(text)
    if path.is_absolute() or ".." in path.parts or path.name in {"", "."}:
        raise ValueError(f"unsafe {what}: {text!r} (must be relative and stay under its base)")
    return path


def validate(data: dict) -> dict:
    """Normalise a plan and reject anything that could write where it should not."""
    if not isinstance(data, dict) or not isinstance(data.get("documents"), list):
        raise ValueError("documentation plan must contain a documents list")
    allow_outside = bool(data.get("allow_outside_project", False))
    base = str(data.get("base_path", "docs"))
    base_path = Path(base)
    if not base or (not allow_outside and (base_path.is_absolute() or ".." in base_path.parts)):
        raise ValueError("base_path must be a non-empty relative path without '..' "
                         "(set allow_outside_project to place documents outside the project)")
    documents = []
    for item in data["documents"]:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise ValueError("each document needs a relative path")
        path = _safe_relative(item["path"], "document path")
        location = item.get("location")
        if location is not None:
            loc = Path(str(location))
            if not allow_outside and (loc.is_absolute() or ".." in loc.parts):
                raise ValueError(f"document location outside the project needs allow_outside_project: {location!r}")
        documents.append({
            "path": path.as_posix(),
            "title": str(item.get("title", "")),
            "purpose": str(item.get("purpose", "")),
            "owner_stage": str(item.get("owner_stage", "")),
            "format": str(item.get("format", "md")),
            "covers": [str(x) for x in item.get("covers", [])],
            "location": str(location) if location else None,
            "origin": str(item.get("origin", "new")),
        })
    depth = str(data.get("depth", "minimal"))
    if depth not in DEPTHS:
        raise ValueError(f"depth must be one of {', '.join(DEPTHS)}")
    header = data.get("header") or {}
    return {
        "schema_version": 1,
        "depth": depth,
        "audience": str(data.get("audience", "owner")),
        "cost_of_error": str(data.get("cost_of_error", "low")),
        "language": str(data.get("language", "")),
        "base_path": base,
        "allow_outside_project": allow_outside,
        "numbering": data.get("numbering") or {"scheme": "none"},
        "header": {"version": bool(header.get("version", True)),
                   "last_updated": bool(header.get("last_updated", True)),
                   "planned_marker": bool(header.get("planned_marker", True))},
        "maintenance": data.get("maintenance") or {"update_on_close": True, "reviewer": "owner"},
        "documents": documents,
    }


def load_answers(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid documentation answers file: {exc}") from exc
    return validate(data)


def resolve(root: Path, plan: dict, document: dict) -> Path:
    """Where a document lives: its own location, else base_path/path (both under root
    unless the plan explicitly allows outside)."""
    where = document.get("location")
    target = Path(where) if where else Path(plan["base_path"]) / document["path"]
    return target if target.is_absolute() else (root / target)


def is_outside(root: Path, target: Path) -> bool:
    try:
        target.resolve().relative_to(root.resolve())
    except ValueError:
        return True
    return False


# --------------------------------------------------------------- persistence

def _atomic_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def plan_path(root: Path) -> Path:
    return root / ".sdd" / PLAN_NAME


def save(root: Path, plan: dict) -> Path:
    _atomic_write(plan_path(root), plan)
    return plan_path(root)


def load(root: Path) -> dict | None:
    path = plan_path(root)
    if not path.is_file():
        return None
    try:
        return validate(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError, json.JSONDecodeError):
        return None


def state_path(root: Path) -> Path:
    return root / ".sdd" / STATE_NAME


def load_state(root: Path) -> dict | None:
    path = state_path(root)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def clear_state(root: Path) -> None:
    state_path(root).unlink(missing_ok=True)


# ------------------------------------------------------------------ signals

def project_signals(root: Path) -> dict:
    sdd = root / ".sdd"
    stages = [p.name for p in (sdd / "stages").iterdir() if p.is_dir()] if (sdd / "stages").is_dir() else []
    tracks = [p.name for p in (sdd / "tracks").iterdir() if p.is_dir() and not p.name.startswith(".")] \
        if (sdd / "tracks").is_dir() else []
    stack = sorted({m for m in _STACK_MARKERS for _ in root.glob(m)}
                   | {m for m in _STACK_MARKERS for _ in root.glob(f"*/{m}")})
    existing = []
    for pattern in ("README.md", "docs/**/*.md", "documentation/**/*.md", "doc/**/*.md"):
        existing += [p for p in root.glob(pattern) if p.is_file()]
    constitution = sdd / "constitution.md"
    text = constitution.read_text(encoding="utf-8", errors="replace") if constitution.is_file() else ""
    language = re.search(r"(?im)^[-*]\s+\*\*Language:\*\*\s*([A-Za-z-]+)", text)
    start, end = re.search(r"(?m)^##\s+1\.", text), re.search(r"(?m)^##\s+4\.", text)
    scope = text[start.start():end.start() if end else len(text)] if start else ""
    risk_terms = sorted({m.group(1).lower() for m in _RISK_WORDS.finditer(scope)})
    return {"stages": len(stages), "tracks": len(tracks), "stack": stack,
            "existing": sorted({str(p.relative_to(root)).replace("\\", "/") for p in existing}),
            "risk_terms": risk_terms,
            "language": language.group(1) if language else ""}


def recommend_depth(signals: dict, high_stakes: bool | None = None) -> tuple[str, str]:
    """A recommendation with its reason, drawn from the real project (bias: less).

    ``high_stakes`` is the owner's direct answer to "is money, health or regulation involved?";
    when given it beats the vocabulary guess, which stays as the fallback (``--answers`` runs).
    """
    if high_stakes:
        return ("comprehensive", "you said money, health or regulation are involved")
    terms = [] if high_stakes is False else signals.get("risk_terms", [])
    if len(terms) >= 3:
        return ("comprehensive",
                "the vision and decisions touch regulated or high-cost-of-error subjects "
                f"({', '.join(terms[:4])})")
    reasons = []
    if terms:
        reasons.append(f"the vision mentions {', '.join(terms)}")
    if signals["stages"] >= 8:
        reasons.append(f"{signals['stages']} stages of history")
    if signals["tracks"] >= 2:
        reasons.append(f"{signals['tracks']} parallel tracks")
    if len(signals["stack"]) >= 2:
        reasons.append(f"{len(signals['stack'])} separate packages/stacks")
    if len(signals["existing"]) >= 3:
        reasons.append(f"{len(signals['existing'])} documentation files already exist")
    if reasons:
        return ("medium", "; ".join(reasons))
    return ("minimal", "a small project: the SDD artifacts plus a good README already carry the knowledge")


# --------------------------------------------------------------- doc presets

def preset(depth: str) -> list[dict]:
    def doc(path: str, purpose: str, **extra) -> dict:
        return {"path": path, "purpose": purpose, "owner_stage": "", "format": "md", "covers": [],
                "location": None, "origin": "new", **extra}

    readme = doc("README.md", "what the project is and how to run it", location="README.md")
    if depth == "minimal":
        return [readme]
    medium = [readme,
              doc("architecture.md", "architecture overview and main flows"),
              doc("data-model.md", "entities, relations and constraints"),
              doc("api-reference.md", "API/contract reference"),
              doc("glossary.md", "domain terms"),
              doc("decisions.md", "decision records (ADRs)")]
    if depth == "medium":
        return medium
    return [readme,
            doc("DOC-001-architecture.md", "architecture and boundaries"),
            doc("DOC-002-governance.md", "ownership, review and change control"),
            doc("DOC-003-roles-permissions.md", "roles and permission matrix"),
            doc("DOC-004-state-machines.md", "states and transitions"),
            doc("DOC-005-domain-events.md", "events and their consumers"),
            doc("DOC-006-security.md", "threat model and controls"),
            doc("DOC-007-compliance.md", "regulatory obligations and evidence"),
            doc("DOC-008-operations.md", "runbooks, deploy, monitoring")]


# ---------------------------------------------------------------- interview

def _list(console: Console, documents: list[dict], root: Path, plan_base: str) -> None:
    console.say("")
    for i, item in enumerate(documents, 1):
        where = item.get("location") or f"{plan_base}/{item['path']}"
        console.say(f"  {i:>2}. {where}  — {item['purpose'] or '(no purpose yet)'}")


def _edit_documents(console: Console, documents: list[dict], root: Path, base: str, allow_outside: bool) -> None:
    console.say("Edit the list: 'a' add, 'r N' remove, 'e N' edit, Enter to accept.")
    while True:
        _list(console, documents, root, base)
        command = console.ask("Change the list? (a = add, r N = remove, e N = edit, Enter = accept)", "").lower()
        if not command:
            return
        head, _, tail = command.partition(" ")
        if head == "a":
            name = console.ask("File name (relative to the base folder)", "")
            if not name:
                continue
            documents.append({"path": name, "purpose": console.ask("Purpose", ""), "owner_stage": "",
                              "format": "md", "covers": [], "location": None, "origin": "new"})
        elif head in ("r", "e") and tail.strip().isdigit() and 1 <= int(tail) <= len(documents):
            index = int(tail) - 1
            if head == "r":
                documents.pop(index)
                continue
            item = documents[index]
            item["path"] = console.ask("File name", item["path"])
            item["purpose"] = console.ask("Purpose", item["purpose"])
            where = console.ask("Own location (path from the project root; empty = base folder)",
                                item.get("location") or "")
            item["location"] = where or None
        else:
            console.say("  unknown command")


def run_interview(root: Path, console: Console, *, state: dict | None = None,
                  save_state: Callable[[dict], None] | None = None) -> dict:
    """Ask, validate, echo -- and return a validated plan. ``state`` resumes an
    interrupted run: steps already answered are not asked again."""
    signals = project_signals(root)
    state = state or {"done": [], "answers": {}}
    answers: dict = state["answers"]

    def step(name: str) -> bool:
        return name not in state["done"]

    def finish(name: str) -> None:
        state["done"].append(name)
        if save_state:
            save_state(state)

    if step("risk"):
        answers["high_stakes"] = console.confirm(
            "Are money, health or regulation involved (a wrong or missing document costs a lot)?",
            bool(signals["risk_terms"]))
        finish("risk")
    if step("depth"):
        depth, reason = recommend_depth(signals, answers.get("high_stakes"))
        console.say(f"Project: {signals['stages']} stage(s), {signals['tracks']} track(s), "
                    f"{len(signals['existing'])} existing doc file(s).")
        console.say(f"Recommendation: {depth} — {reason}.")
        console.say("Bias toward less: documentation nobody maintains becomes a lie.")
        answers["depth"] = console.choose("Documentation depth", DEPTHS, depth)
        finish("depth")
    if step("audience"):
        answers["audience"] = console.choose("Who reads it (owner/collaborator/auditor)", AUDIENCES, "owner")
        answers["cost_of_error"] = console.choose("Cost of a wrong or missing document", ("low", "medium", "high"),
                                                  "high" if answers.get("high_stakes") else
                                                  {0: "low", 1: "medium", 2: "medium"}.get(len(signals["risk_terms"]), "high"))
        answers["language"] = console.ask("Language of the documents", signals["language"] or "en")
        finish("audience")
    if step("location"):
        default = "docs"
        if (root / "docs").is_dir():
            console.say("Found an existing docs/ folder.")
        base = console.ask("Base folder for the documents (relative to the project root; "
                           "may be outside .sdd/)", default)
        outside = Path(base).is_absolute() or ".." in Path(base).parts
        allow = False
        if outside:
            allow = console.confirm(f"'{base}' is OUTSIDE the project folder. Write there?", False)
            if not allow:
                base = default
                console.say(f"  keeping {default}/")
        answers["base_path"] = base
        answers["allow_outside_project"] = allow
        finish("location")
    if step("documents"):
        documents = preset(answers["depth"])
        console.say(f"Suggested set for '{answers['depth']}' — adjust it to what the project really needs.")
        _edit_documents(console, documents, root, answers["base_path"], answers["allow_outside_project"])
        answers["documents"] = documents
        finish("documents")
    if step("convention"):
        numbered = answers["depth"] == "comprehensive"
        if console.confirm("Use a numbered, versioned corpus (DOC-001 ...)?", numbered):
            answers["numbering"] = {"scheme": "DOC-001", "prefix": "DOC", "versioned": True}
        else:
            answers["numbering"] = {"scheme": "none"}
        answers["header"] = {
            "version": console.confirm("Every document states its version?", True),
            "last_updated": console.confirm("Every document states its last-updated date?", True),
            "planned_marker": console.confirm("Mark content not yet implemented as 'planned'?", True),
        }
        finish("convention")
    if step("maintenance"):
        update = console.confirm("Should closing a stage revise the documents it affects?", True)
        reviewer = console.ask("Who reviews documentation changes", "owner")
        if update:
            console.say("For each document, list the stages that must refresh it "
                        "(numbers or slugs, comma-separated; 'all'; Enter = only when its owner stage closes).")
            for item in answers["documents"]:
                raw = console.ask(f"  {item['path']} covers", "")
                item["covers"] = [x.strip() for x in raw.split(",") if x.strip()]
        answers["maintenance"] = {"update_on_close": update, "reviewer": reviewer}
        finish("maintenance")
    if step("existing"):
        planned = {Path(resolve(root, {"base_path": answers["base_path"]}, d)).resolve()
                   for d in answers["documents"]}
        found = [p for p in signals["existing"] if (root / p).resolve() not in planned][:15]
        if found:
            console.say("Documentation files that already exist and are not in the plan:")
            for name in found:
                if console.confirm(f"  adopt {name} into the plan?", False):
                    answers["documents"].append({"path": Path(name).name, "purpose": "existing document",
                                                 "owner_stage": "", "format": "md", "covers": [],
                                                 "location": name, "origin": "adopted"})
        finish("existing")
    plan = validate(answers)
    console.say("\nPlan:")
    for item in plan["documents"]:
        target = resolve(root, plan, item)
        outside = is_outside(root, target)
        shown = target if outside else target.resolve().relative_to(root.resolve())
        console.say(f"  - {str(shown).replace(chr(92), '/')}{'  (OUTSIDE the project)' if outside else ''}")
    if not console.confirm("Save this plan?", True):
        raise InterviewAborted
    return plan


# ------------------------------------------------------------------- stubs

def stub_text(plan: dict, document: dict) -> str:
    title = document["title"] or Path(document["path"]).stem.replace("-", " ").replace("_", " ").title()
    lines = [f"# {title}", ""]
    if plan["header"]["version"]:
        lines.append("- **Version:** 0.1")
    if plan["header"]["last_updated"]:
        lines.append(f"- **Last updated:** {date.today().isoformat()}")
    if document["purpose"]:
        lines.append(f"- **Purpose:** {document['purpose']}")
    lines.append("")
    if plan["header"]["planned_marker"]:
        lines += ["> **Planned** — not yet written; replace this note when the content is real.", ""]
    return "\n".join(lines)


def write_stubs(root: Path, plan: dict) -> tuple[list[str], list[str]]:
    """Create stubs for documents that do not exist yet; never overwrite."""
    created, skipped = [], []
    for item in plan["documents"]:
        if item.get("origin") == "adopted":
            continue
        target = resolve(root, plan, item)
        if target.exists():
            skipped.append(str(target))
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(stub_text(plan, item), encoding="utf-8", newline="\n")
        created.append(str(target))
    return created, skipped


# ------------------------------------------------------------------ doctor

def findings(root: Path) -> list[dict]:
    """Audit-only: planned documents that are missing, headerless or outside the project."""
    plan = load(root)
    if not plan:
        return []
    out: list[dict] = []
    for item in plan["documents"]:
        target = resolve(root, plan, item)
        shown = str(target) if is_outside(root, target) else str(target.relative_to(root)).replace("\\", "/")
        if is_outside(root, target):
            out.append({"severity": "note", "code": "docs_path_outside_project", "path": shown})
        if not target.is_file():
            out.append({"severity": "note", "code": "docs_missing_file", "path": shown})
            continue
        if target.name.lower().startswith("readme"):
            continue  # a README follows its own conventions; the header rule is for the documentation set
        head = target.read_text(encoding="utf-8", errors="replace")[:1500]
        missing = [label for flag, label in ((plan["header"]["version"], "Version"),
                                             (plan["header"]["last_updated"], "Last updated"))
                   if flag and not re.search(rf"(?i)\b{label}\b", head)]
        if missing:
            out.append({"severity": "warn", "code": "docs_missing_header", "path": shown,
                        "missing": missing})
    return out
