"""``sddkit adr init``: rebuild decision records for a project that already has decisions.

A project that adopted the kit before ``.sdd/decisions/`` has its decisions in section 3 and,
maybe, ADRs somewhere else. This module reads what the project already says, proposes candidates,
asks about what cannot be inferred and writes records that say so: every record it makes has
``reconstructed: true`` and a ``source:``, and whatever the sources do not say is left as a marked
placeholder, never invented. It only creates files; nothing the owner wrote is overwritten.

Three strategies for the records (``strategy`` in the answers file):

* ``rows``   -- build records from the ``D-NNN`` rows the owner confirms (the default);
* ``link``   -- ADRs stay where they are: section 7 says ``external — <path>`` and, for a folder
  with one file per ADR, the ``Record`` cells link them;
* ``import`` -- a folder with one file per ADR is copied into ``.sdd/decisions/`` (numbers kept).

The engine has no I/O of its own: the interview talks through ``_docs_plan.Console`` and saves its
answers after every step, so it resumes (``--resume``); an agent without a terminal passes the same
answers as JSON (``--answers``). Both end in the same ``build_plan`` / ``apply``.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Callable
from pathlib import Path

from . import _adr, _decisions, _docs_plan, _lock, _tracks

SCHEMA = "sdd-adr-init/v1"
STATE_NAME = ".adr-interview.json"
STRATEGIES = ("rows", "link", "import")
UNKNOWN = "[unknown: not recorded in the source]"

_EXTERNAL_DIRS = ("docs/decisoes", "docs/decisions", "docs/adr", "docs/adrs", "adr", "adrs", "decisions")
_EXTERNAL_FILE_RE = re.compile(r"(?i)^ADR[-_ ]?(\d+)(?:[-_ .].*)?\.md\Z")
_ISO_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
_DECISION_REF_RE = re.compile(r"\bD-\d+\b")
_ADR_REF_RE = re.compile(r"\bADR-?(\d+)\b", re.I)


# ----------------------------------------------------------------- analysis

def _constitution(root: Path) -> str:
    path = root / ".sdd" / "constitution.md"
    if not path.is_file():
        return ""
    return path.read_bytes().decode("utf-8", errors="replace").replace("\r\n", "\n")


def _stage_citations(root: Path) -> dict[str, list[str]]:
    """``D-NNN`` -> the stages whose spec or report mention it (a hint, never a fact to copy)."""
    found: dict[str, set[str]] = {}
    sdd = root / ".sdd"
    stage_dirs = list((sdd / "stages").glob("*")) + list((sdd / "tracks").glob("*/stages/*"))
    for stage in stage_dirs:
        if not stage.is_dir():
            continue
        for name in ("spec.md", "report.md"):
            try:
                text = (stage / name).read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for ref in set(_DECISION_REF_RE.findall(text)):
                found.setdefault(ref, set()).add(stage.name)
    return {ref: sorted(stages) for ref, stages in found.items()}


def _external_folder(root: Path, candidate: str) -> dict | None:
    folder = root / candidate
    if not folder.is_dir():
        return None
    files = []
    for path in sorted(folder.iterdir()):
        match = _EXTERNAL_FILE_RE.match(path.name) if path.is_file() else None
        if match:
            files.append({"number": int(match.group(1)), "path": path.relative_to(root).as_posix()})
    return {"path": candidate.rstrip("/") + "/", "kind": "folder", "files": files} if files else None


def detect_external(root: Path, field: dict) -> dict | None:
    """Where the project's ADRs already live: what section 7 names, else a folder with ADR files."""
    named = field.get("path") if field.get("mode") == _decisions.MODE_EXTERNAL else ""
    if named:
        target = root / named
        if target.is_file():
            return {"path": named, "kind": "document", "files": []}
        found = _external_folder(root, named.rstrip("/"))
        return found or {"path": named, "kind": "missing", "files": []}
    for candidate in _EXTERNAL_DIRS:
        found = _external_folder(root, candidate)
        if found:
            return found
    return None


def analyze(root: Path) -> dict:
    """Read-only survey: the rows that still lack a record, §7, existing records, external ADRs."""
    text = _constitution(root)
    table = _decisions.rows(text)
    field = _decisions.decision_records(text)
    cited = _stage_citations(root)
    external = detect_external(root, field)
    external_numbers = {f["number"] for f in (external or {}).get("files", [])}
    candidates = []
    for row in table or []:
        if row["placeholder"]:
            continue
        cells = row["cells"] + [""] * 5
        mentioned = sorted({int(n) for cell in cells[1:] for n in _ADR_REF_RE.findall(cell)})
        candidates.append({
            "id": row["id"], "decision": cells[1], "choice": cells[2], "rationale": cells[3],
            "locked_on": cells[4], "record": row["record"],
            "locked": bool(_ISO_DATE_RE.match(cells[4])),
            "cited_in": cited.get(row["id"], []),
            "external_numbers": [n for n in mentioned if n in external_numbers]})
    return {"has_table": table is not None, "candidates": candidates, "decision_records": field,
            "external": external, "existing": [r.id for r in _adr.list_adrs(root)],
            "has_record_column": _decisions.has_record_column(text)}


def pending(analysis: dict) -> list[dict]:
    """Rows with no record yet."""
    return [c for c in analysis["candidates"] if not c["record"].strip()]


# --------------------------------------------------------------- validation

def _text(value: object, where: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"{where} must be a string")
    return value.strip()


def validate(answers: dict, analysis: dict, root: Path) -> dict:
    """The answers, normalized; ``ValueError`` names the first thing that cannot be applied."""
    if not isinstance(answers, dict) or answers.get("schema_version") != SCHEMA:
        raise ValueError(f"answers must be an object with schema_version {SCHEMA!r}")
    if not analysis["has_table"]:
        raise ValueError("constitution.md has no section 3 table of decisions to link records to")
    strategy = answers.get("strategy", "rows")
    if strategy not in STRATEGIES:
        raise ValueError(f"strategy must be one of: {', '.join(STRATEGIES)}")
    path = ""
    if strategy in ("link", "import"):
        path = _text(answers.get("path"), "path")
        if not path:
            raise ValueError(f"strategy {strategy} needs `path`: the folder or document with the ADRs")
        try:
            _docs_plan._safe_relative(path.rstrip("/"), "path")
        except ValueError as exc:
            raise ValueError(str(exc)) from exc
        if not (root / path).exists():
            raise ValueError(f"path does not exist: {path}")
        if strategy == "import" and not (root / path).is_dir():
            raise ValueError("strategy import needs a folder with one file per ADR; a single document can "
                             "only be linked")
    open_ids = {c["id"] for c in pending(analysis)}
    records, seen = [], set()
    raw_records = answers.get("records", [])
    if not isinstance(raw_records, list):
        raise ValueError("records must be a list")
    for number, item in enumerate(raw_records, 1):
        where = f"records[{number}]"
        if not isinstance(item, dict):
            raise ValueError(f"{where} must be an object")
        decision = _text(item.get("decision"), f"{where}.decision")
        if decision not in {c["id"] for c in analysis["candidates"]}:
            raise ValueError(f"{where}.decision {decision!r} is not a row of section 3")
        if decision in seen:
            raise ValueError(f"{where}.decision {decision} appears twice")
        seen.add(decision)
        if decision not in open_ids:
            continue  # it already has a record: idempotent second run
        status = item.get("status")
        if status is not None and _adr.normalize_status(status) is None:
            raise ValueError(f"{where}.status {status!r} is outside the cycle: " + ", ".join(_adr.STATUSES))
        alternatives = item.get("alternatives", [])
        if not isinstance(alternatives, list) or any(not isinstance(a, str) for a in alternatives):
            raise ValueError(f"{where}.alternatives must be a list of strings")
        records.append({
            "decision": decision, "title": _text(item.get("title"), f"{where}.title"),
            "status": _adr.normalize_status(status) if status else "",
            "stage": _text(item.get("stage"), f"{where}.stage"),
            "date": _text(item.get("date"), f"{where}.date"),
            "context": _text(item.get("context"), f"{where}.context"),
            "alternatives": [a.strip() for a in alternatives if a.strip()],
            "implemented_in": _text(item.get("implemented_in"), f"{where}.implemented_in"),
            "source": _text(item.get("source"), f"{where}.source")})
    mapping = answers.get("map", {})
    if not isinstance(mapping, dict) or any(not isinstance(k, str) or not isinstance(v, str)
                                            for k, v in mapping.items()):
        raise ValueError("map must be an object of ADR-NNN -> D-NNN strings")
    return {"schema_version": SCHEMA, "strategy": strategy, "path": path, "records": records, "map": mapping}


def load_answers(path: Path, analysis: dict, root: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read answers {path}: {exc}") from exc
    return validate(data, analysis, root)


# --------------------------------------------------------------------- plan

def _external_decision(text: str, known: set[str]) -> str:
    """The first ``D-NNN`` an external ADR names, when it is a row of section 3."""
    for ref in _DECISION_REF_RE.findall(text):
        if ref in known:
            return ref
    return ""


def _external_title(text: str, number: int) -> str:
    match = re.search(r"(?m)^#\s+(?:ADR[-_ ]?\d+\s*[—–:.-]\s*)?(.+?)\s*$", text)
    return match.group(1).strip() if match else f"ADR-{number:03d}"


def build_plan(root: Path, analysis: dict, answers: dict) -> dict:
    """What would change, as data: files to create, the constitution edit, notes. Writes nothing."""
    strategy = answers["strategy"]
    rows = {c["id"]: c for c in analysis["candidates"]}
    known = set(rows)
    taken = set(_adr._used_numbers(root))  # files and the ledger: a number once handed out stays taken
    already = {str(r.meta.get("source", "")) for r in _adr.list_adrs(root)}
    create: list[dict] = []
    links: dict[str, str] = {}
    notes: list[str] = []
    section7: dict | None = None
    field = analysis["decision_records"]

    if strategy in ("link", "import"):
        folder = (root / answers["path"]).is_dir()
        files = []
        if folder:
            found = _external_folder(root, answers["path"].rstrip("/"))
            files = found["files"] if found else []
        if strategy == "link":
            section7 = {"mode": _decisions.MODE_EXTERNAL, "path": answers["path"]}
            if folder and not files:
                notes.append(f"{answers['path']} has no ADR-NNN files; section 7 is updated, no row is linked")
            if not folder:
                notes.append("a single document is linked from section 7 only: its ADRs cannot be told "
                             "apart safely, so no Record cell is filled")
        else:
            section7 = {"mode": _decisions.MODE_INTERNAL, "path": ""}
        for entry in files:
            number, rel = entry["number"], entry["path"]
            text = (root / rel).read_bytes().decode("utf-8", errors="replace").replace("\r\n", "\n")
            decision = answers["map"].get(f"ADR-{number:03d}") or _external_decision(text, known)
            if not decision:
                decision = next((c["id"] for c in analysis["candidates"]
                                 if number in c["external_numbers"] and not c["record"].strip()), "")
            row = rows.get(decision)
            target_rows = [decision] if decision and row and not row["record"].strip() else []
            if strategy == "link":
                link = f"[ADR-{number:03d}]({os.path.relpath(root / rel, root / '.sdd').replace(os.sep, '/')})"
                for did in target_rows:
                    links[did] = link
                continue
            if rel in already:
                notes.append(f"{rel} was already imported")
                continue
            if number in taken:
                notes.append(f"{rel}: ADR-{number:03d} already exists in .sdd/decisions/; not overwritten")
                continue
            taken.add(number)
            title = _external_title(text, number)
            locked = bool(row and row["locked"])
            meta = {"id": f"ADR-{number:03d}", "status": _adr.ACCEPTED if locked else _adr.PROPOSED, "date": "",
                    "stage": "", "decision": decision, "supersedes": [], "superseded_by": [],
                    "implemented_in": "", "reconstructed": True, "source": rel}
            name = f"ADR-{number:03d}-{_adr.slugify(title)}.md"
            create.append({"id": meta["id"], "number": number, "path": f".sdd/decisions/{name}",
                           "title": title, "status": meta["status"], "source": rel,
                           "content": _adr.render_record(meta, text)})
            for did in target_rows:
                links[did] = f"[{meta['id']}]({_adr.DECISIONS_DIR}/{name})"
    elif field["mode"] in (_decisions.MODE_UNSET, _decisions.MODE_LEGACY, _decisions.MODE_NONE):
        section7 = {"mode": _decisions.MODE_INTERNAL, "path": ""}

    next_number = max(taken, default=0) + 1
    for item in answers["records"]:
        row = rows[item["decision"]]
        if item["decision"] in links:
            notes.append(f"{item['decision']} is already covered by an existing ADR; no new record")
            continue
        number, next_number = next_number, next_number + 1
        record_id = f"ADR-{number:03d}"
        title = item["title"] or ": ".join(p for p in (row["decision"], row["choice"]) if p) or item["decision"]
        status = item["status"] or (_adr.ACCEPTED if row["locked"] else _adr.PROPOSED)
        date = item["date"] or (row["locked_on"] if row["locked"] else "")
        meta = {"id": record_id, "status": status, "date": date, "stage": item["stage"],
                "decision": item["decision"], "supersedes": [], "superseded_by": [],
                "implemented_in": item["implemented_in"], "reconstructed": True,
                "source": item["source"] or f"constitution.md section 3 ({item['decision']})"}
        body = _adr.render_body(
            root, record_id, title, item["context"] or UNKNOWN, item["alternatives"] or [UNKNOWN],
            _adr.decision_section(row["choice"], row["rationale"]) or UNKNOWN)
        name = f"{record_id}-{_adr.slugify(title)}.md"
        create.append({"id": record_id, "number": number, "path": f".sdd/decisions/{name}", "title": title,
                       "status": status, "source": meta["source"], "content": _adr.render_record(meta, body)})
        links[item["decision"]] = f"[{record_id}]({_adr.DECISIONS_DIR}/{name})"

    if section7 and section7["mode"] == field["mode"] and section7["path"] == field.get("path", ""):
        section7 = None
    return {"strategy": strategy, "create": create, "links": links, "section7": section7,
            "add_record_column": analysis["has_record_column"] is False and bool(links or section7),
            "notes": notes}


def summary(plan: dict) -> dict:
    """The plan without the file contents, for ``--dry-run`` and ``--json``."""
    return {"strategy": plan["strategy"], "add_record_column": plan["add_record_column"],
            "section7": plan["section7"], "links": plan["links"], "notes": plan["notes"],
            "create": [{k: v for k, v in item.items() if k not in ("content", "number")}
                       for item in plan["create"]]}


def is_empty(plan: dict) -> bool:
    return not (plan["create"] or plan["links"] or plan["section7"] or plan["add_record_column"])


# -------------------------------------------------------------------- apply

def apply(root: Path, plan: dict) -> dict:
    """Write the plan: records first (``x`` mode, never overwriting), then one constitution edit
    (with a backup), then the index. Returns what was written and what was skipped."""
    created, skipped = [], []
    with _lock.file_lock(root / ".sdd" / _tracks.LOCK_NAME):
        for item in plan["create"]:
            if _adr.write_new_file(root / item["path"], item["content"]):
                created.append(item["path"])
            else:
                skipped.append(item["path"])
        _adr.claim_numbers(root, [item["number"] for item in plan["create"] if item["path"] in created])

    def edit(text: str) -> str:
        if plan["add_record_column"]:
            text, _ = _decisions.add_record_column(text)
        for decision, link in plan["links"].items():
            text, _ = _decisions.set_record(text, decision, link)
        if plan["section7"]:
            text = _decisions.set_decision_records(text, plan["section7"]["mode"], plan["section7"]["path"])
        return text

    changed = _decisions.edit_constitution(root, edit)
    index = _adr.write_index(root) if _adr.decisions_dir(root).is_dir() else False
    return {"created": created, "skipped_existing": skipped, "constitution_changed": changed,
            "index_written": index}


# ---------------------------------------------------------------- interview

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


def save_state(root: Path, state: dict) -> None:
    _docs_plan._atomic_write(state_path(root), state)


def clear_state(root: Path) -> None:
    state_path(root).unlink(missing_ok=True)


def _ask_list(console: _docs_plan.Console, prompt: str) -> list[str]:
    answer = console.ask(prompt + " (separate with ';', empty if unknown)", "")
    return [part.strip() for part in answer.split(";") if part.strip()]


def run_interview(root: Path, analysis: dict, console: _docs_plan.Console, *, state: dict | None = None,
                  on_step: Callable[[dict], None] | None = None) -> dict:
    """Ask what the sources do not say and return the answers (validated by the caller).

    ``state`` resumes an interrupted run: steps already answered are not asked again.
    """
    state = state or {"done": [], "answers": {}}
    answers: dict = state["answers"]

    def step(name: str) -> bool:
        return name not in state["done"]

    def finish(name: str) -> None:
        state["done"].append(name)
        if on_step:
            on_step(state)

    todo = pending(analysis)
    external = analysis["external"]
    if step("sources"):
        console.say(f"Section 3 has {len(analysis['candidates'])} decision(s); {len(todo)} without a record.")
        if analysis["existing"]:
            console.say(f"Already in .sdd/decisions/: {', '.join(analysis['existing'])}.")
        if external and external["kind"] == "folder":
            console.say(f"Found {len(external['files'])} ADR file(s) in {external['path']}.")
        elif external and external["kind"] == "document":
            console.say(f"Section 7 points at the document {external['path']}.")
        console.say("Nothing is invented: what the sources do not say stays marked as unknown.")
        finish("sources")
    if step("strategy"):
        if external and external["kind"] in ("folder", "document"):
            options = ("link", "import", "rows") if external["kind"] == "folder" else ("link", "rows")
            console.say("The ADRs already exist outside .sdd/decisions/: link them (they stay where they are"
                        + (", or import them as records" if external["kind"] == "folder" else "")
                        + "), or build records from the rows of section 3 ('rows').")
            answers["strategy"] = console.choose("What to do with them", options, "link")
            answers["path"] = external["path"]
            if answers["strategy"] != "rows":
                answers["path"] = console.ask("Folder or document with the ADRs", external["path"])
        else:
            answers["strategy"] = "rows"
        finish("strategy")
    if step("records"):
        covered = set()
        if answers.get("strategy") in ("link", "import") and external:
            for candidate in todo:
                if candidate["external_numbers"]:
                    covered.add(candidate["id"])
        records = []
        for candidate in todo:
            if candidate["id"] in covered:
                continue
            label = f"{candidate['id']} {candidate['decision']}: {candidate['choice']}".strip()
            hint = []
            if candidate["cited_in"]:
                hint.append("cited by " + ", ".join(candidate["cited_in"]))
            if not candidate["locked"]:
                hint.append("still proposed")
            console.say(f"\n{label}" + (f"  ({'; '.join(hint)})" if hint else ""))
            default = len(candidate["cited_in"]) > 1
            if not console.confirm("Does it deserve a record (real alternatives, refutable premise, "
                                   "several stages, costly to reverse)?", default):
                continue
            status = console.choose("Status", _adr.STATUSES,
                                    _adr.ACCEPTED if candidate["locked"] else _adr.PROPOSED)
            item = {"decision": candidate["id"], "status": status,
                    "context": console.ask("Context: why it was needed (empty if unknown)", ""),
                    "alternatives": _ask_list(console, "Alternatives that were considered"),
                    "stage": console.ask("Stage where it was made (empty if unknown)", "")}
            if status == _adr.IMPLEMENTED:
                item["implemented_in"] = console.ask("Implemented in (stage, file or commit)",
                                                     candidate["cited_in"][0] if candidate["cited_in"] else "")
            records.append(item)
        answers["records"] = records
        finish("records")
    return {"schema_version": SCHEMA, "strategy": answers.get("strategy", "rows"),
            "path": answers.get("path", ""), "records": answers.get("records", []), "map": {}}
