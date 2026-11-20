"""Slimming the constitution (E-01 and E-02, 4.9.6).

The constitution is the owner's file, so the kit splits the work in two:

* **What the kit can prove is disposable** (E-01): an HTML comment that is byte-for-byte one of the
  comments of the bundled constitution template. ``sddkit fix --slim`` removes only those, with
  ``--dry-run`` and a backup.
* **What only the owner can move** (E-02): long lines (over 600 bytes) and the cost of each
  section. ``sddkit doctor --slim`` lists them with the file they belong in and an instruction for
  the agent. Nothing here ever edits a line the owner wrote.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .content import CONTENT_DIR

LIMIT_BYTES = 24 * 1024
LONG_LINE_BYTES = 600

_COMMENT = re.compile(r"<!--.*?-->", re.S)
_H2 = re.compile(r"(?m)^##\s+(.+?)\s*$")
_FENCE = re.compile(r"^\s*(```|~~~)")

# Where a long line goes, by the number that opens its H2 heading. The owner decided on
# 2026-11-17 that long text leaves a locked decision (3) and the structural change history (6)
# for CHANGELOG.md, with the decision kept short in the constitution and a reference to the
# CHANGELOG entry; long stage-index rows (5) go to backlog.md. Any other section has no rule:
# the plan says "decide with the owner" instead of guessing.
_DESTINATION = {"3": "CHANGELOG.md", "5": "backlog.md", "6": "CHANGELOG.md"}

INSTRUCTION = (
    "For each line listed, with the owner's agreement: move the long text to the destination "
    "file, keep 2-3 sentences in the constitution, and add a pointer to where the rest went. "
    "Never reword a locked decision (section 3): its summary must say the same thing. "
    "Commit the move on its own, then run `sddkit doctor` again."
)


def _template_comments() -> set[str]:
    template = (CONTENT_DIR / "sdd" / "constitution.md").read_text(encoding="utf-8")
    return set(_COMMENT.findall(template.replace("\r\n", "\n")))


def _fenced_lines(lines: list[str]) -> set[int]:
    """Indexes (0-based) of lines inside a fenced code block, fences included."""
    inside: set[int] = set()
    open_fence = False
    for index, line in enumerate(lines):
        if _FENCE.match(line):
            inside.add(index)
            open_fence = not open_fence
        elif open_fence:
            inside.add(index)
    return inside


@dataclass
class Removal:
    line: int
    bytes: int


def slim_text(raw: str) -> tuple[str, list[Removal]]:
    """Return ``(new_text, removals)``: ``raw`` without the comments that match the bundled
    template exactly. The file's own line endings are kept. Edited comments, comments inside a
    fenced code block and everything else are left as they are."""
    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")
    known = _template_comments()
    fenced_chars = _fenced_char_ranges(text)
    spans: list[tuple[int, int, int]] = []
    for match in _COMMENT.finditer(text):
        if match.group(0) not in known or any(a <= match.start() < b for a, b in fenced_chars):
            continue
        start, end = match.start(), match.end()
        line_start = text.rfind("\n", 0, start) + 1
        line_end = text.find("\n", end)
        line_end = len(text) if line_end == -1 else line_end + 1
        alone = not text[line_start:start].strip() and not text[end:line_end].strip()
        if alone:
            start, end = line_start, line_end
            blank_before = start == 0 or text[:start].endswith("\n\n")
            if blank_before and text[end:end + 1] == "\n":
                end += 1  # do not leave two blank lines where a comment sat between them
        elif start > 0 and text[start - 1] == " ":
            start -= 1
        spans.append((start, end, text.count("\n", 0, match.start()) + 1))
    removals: list[Removal] = []
    out: list[str] = []
    cursor = 0
    for start, end, line in spans:
        out.append(text[cursor:start])
        removals.append(Removal(line, len(text[start:end].encode("utf-8"))))
        cursor = end
    out.append(text[cursor:])
    new_text = "".join(out)
    return (new_text.replace("\n", "\r\n") if crlf else new_text), removals


def _fenced_char_ranges(text: str) -> list[tuple[int, int]]:
    lines = text.split("\n")
    inside = _fenced_lines(lines)
    ranges: list[tuple[int, int]] = []
    offset = 0
    for index, line in enumerate(lines):
        if index in inside:
            ranges.append((offset, offset + len(line) + 1))
        offset += len(line) + 1
    return ranges


def _heading_number(heading: str) -> str:
    match = re.match(r"(\d+)\.", heading)
    return match.group(1) if match else ""


def plan(raw: str) -> dict:
    """The read-only slimming plan for one constitution (what ``doctor --slim`` prints)."""
    text = raw.replace("\r\n", "\n")
    lines = text.split("\n")
    fenced = _fenced_lines(lines)
    sections: list[dict] = []
    matches = list(_H2.finditer(text))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections.append({"heading": match.group(1), "bytes": len(text[match.start():end].encode("utf-8"))})
    section_at = [""] * len(lines)  # H2 heading that owns each line
    current = ""
    for index, line in enumerate(lines):
        found = _H2.match(line)
        if found and index not in fenced:
            current = found.group(1)
        section_at[index] = current
    long_lines = []
    for index, line in enumerate(lines):
        size = len(line.encode("utf-8"))
        if size <= LONG_LINE_BYTES or index in fenced or _COMMENT.fullmatch(line.strip()):
            continue
        heading = section_at[index]
        long_lines.append({"line": index + 1, "bytes": size, "section": heading,
                           "kind": "table row" if "|" in line else "text",
                           "destination": _DESTINATION.get(_heading_number(heading))})
    _, removals = slim_text(raw)
    total = len(raw.encode("utf-8"))
    return {"bytes": total, "limit": LIMIT_BYTES, "over_by": max(0, total - LIMIT_BYTES),
            "sections": sections,
            "template_comments": {"count": len(removals), "bytes": sum(r.bytes for r in removals),
                                  "lines": [r.line for r in removals]},
            "long_lines": long_lines, "instruction": INSTRUCTION}


def recoverable_bytes(raw: str) -> int:
    return sum(r.bytes for r in slim_text(raw)[1])


def top_sections(raw: str, count: int = 3) -> str:
    """The ``count`` biggest sections as one short string, for the doctor's one-line message."""
    ranked = sorted(plan(raw)["sections"], key=lambda s: s["bytes"], reverse=True)[:count]
    return ", ".join(f"{s['heading']} {s['bytes']} B" for s in ranked)


def render(report: dict, project: str) -> str:
    """Plain-text form of :func:`plan`."""
    out = [f"slim plan — {project}",
           f"  constitution.md: {report['bytes']} bytes, limit {report['limit']}"
           + (f" (over by {report['over_by']})" if report["over_by"] else " (within the limit)"),
           "", "where the bytes are (H2 sections, biggest first)"]
    for section in sorted(report["sections"], key=lambda s: s["bytes"], reverse=True):
        out.append(f"  {section['bytes']:>7}  {section['heading']}")
    template = report["template_comments"]
    out += ["", "what sddkit removes by itself: sddkit fix --slim --dry-run",
            f"  {template['count']} template comment(s) unchanged since the kit, {template['bytes']} bytes"]
    out += ["", "what only the owner can move (the kit edits none of it)"]
    if not report["long_lines"]:
        out.append("  no line over 600 bytes")
    for item in report["long_lines"]:
        where = item["destination"] or "decide with the owner"
        out.append(f"  line {item['line']:<5} {item['bytes']:>6} B  {item['kind']:<9} "
                   f"{item['section'] or '(before the first section)'}  ->  {where}")
    out += ["", "how", f"  {report['instruction']}"]
    return "\n".join(out)
