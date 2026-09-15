"""Mojibake detection and repair — shared by `doctor` (report mode) and
`migrate` (gate mode).

Two kinds of mojibake can appear in `.sdd/` Markdown, and they are handled very
differently because they differ in how mechanically recoverable they are:

1. **Double-encoding (v2)** — a Latin-1/Cp1252 character that was UTF-8-encoded
   twice. Shows up as `Ã§`, `Ã£`, `Ã©`, … (bytes `c3 83 c2 xx` or `c3 83 c3 xx`).
   This is **deterministic and unambiguous**: the byte pattern is impossible in
   legitimate UTF-8 prose, and the repair (`encode('cp1252').decode('utf-8')`)
   inverts it exactly with zero false positives. So it is an **ERROR**: `migrate`
   hard-blocks until it is resolved, and `--fix-mojibake` repairs it inline.

2. **Accent-loss (v1)** — accented chars were replaced by literal `?` (ASCII
   `0x3f`) at some past save (an editor that could not encode the accent). Shows
   up as `Decis?es`, `aplica??o`. This is **ambiguous**: a `?` adjacent to a
   word *might* be a lost accent, but there are genuine `?` everywhere (Python
   `?`-pseudo-syntax, ternaries in pseudo-code, plain questions). They cannot be
   told apart mechanically with confidence. So it is **audit-only**: `doctor`
   reports a WARNING with counts and snippets, and `migrate` only requires the
   owner to acknowledge (`--review-mojibake`) — it never auto-fixes `?`.

A single detector backs both modes so the set `doctor` reports and the set
`migrate` blocks on can never drift apart.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# ----------------------------------------------------------------- detector

# Double-encoding (v2): a `Ã` (U+00C3, bytes `c3 83`) immediately followed by a
# Latin-1 char in 0xa7-0xbf that was UTF-8-encoded a second time (`c2 a7`..`c2
# bf`). The only LEGITIMATE `Ã` in PT prose is the standalone letter in "NÃO" —
# its following byte is `o` (0x6f), NOT in the 0x80-0xff range, so "NÃO" never
# matches. Zero false positives confirmed against the real corpus: 130 spans in
# stages 001–014 (all branch `c3 83 c2 [80-bf]`), zero in 015–027.
#
# Why only the `c2` branch (not `c3`): a double-encoded real-world accent always
# lands on a `c2`-led continuation because the ORIGINAL byte was in 0x80-0xff
# (Latin-1 range) — `ç`->a7, `ã`->a3, `é`->e9, `õ`->f5 — all `c2`-led after the
# double-encode. Keeping the regex to this one branch guarantees EVERY hit is
# reversible by `encode('latin-1').decode('utf-8')` (the bytes reduce to valid
# UTF-8 of the original accent). A `c3 83 c3 [80-bf]` span would NOT be
# reversible and does not occur in real corruption; omitting it keeps the
# detector and the repair in lockstep (no detectable-but-unfixable spans).
_V2_BYTE_RE = re.compile(rb"\xc3\x83\xc2[\x80-\xbf]")

# Accent-loss (v1): a `?` (0x3f) BURIED in a word — "Decis?es", "aplica??o",
# "pr?prio". A lost-accent `?` sits between *letters* (or a run of `?` between
# letters). A real question mark sits at a word boundary followed by space / a
# bracket / a quote / a digit — never a letter. So the left neighbour must be a
# letter and the right neighbour a letter or another `?` (so `aplica??o`
# counts). This rejects `it?`, `[y/N]?`, `?"`, `?2`, ` ? ` — the sentence-end
# question marks that flood English instructions — while catching `es?es`,
# `ca??o`, `pr?pri`. Deliberately a *suspect* detector, never auto-fixed.
_V1_BYTE_RE = re.compile(rb"[A-Za-z]\?[A-Za-z?]")


@dataclass
class Hit:
    """One mojibake occurrence."""

    kind: str          # "v2" (double-encoding) | "v1" (accent-loss `?`)
    offset: int       # byte offset in the file
    snippet: str      # ~12-char context, replacement chars for undecodable bytes

    @property
    def actionable(self) -> bool:
        """Only deterministic double-encoding is safe for automation."""
        return self.kind == "v2"


@dataclass
class FileReport:
    """Result of scanning one file."""

    path: Path
    v2: list[Hit]      # double-encoding hits (ERROR-class)
    v1: list[Hit]      # accent-loss hits (WARN-class)
    is_utf8: bool      # False if the file is not decodable as UTF-8 at all

    @property
    def actionable(self) -> bool:
        return bool(self.v2)


def _make_hit(kind: str, m: re.Match, raw: bytes) -> Hit:
    start = max(0, m.start() - 8)
    end = min(len(raw), m.end() + 8)
    snippet = raw[start:end].decode("utf-8", errors="replace")
    return Hit(kind=kind, offset=m.start(), snippet=snippet)


def scan_file(path: Path) -> FileReport:
    """Scan a single file. Reads bytes — never decodes the whole file as text
    first, because a non-UTF-8 file would raise before we could classify it."""
    raw = path.read_bytes()
    v2 = [_make_hit("v2", m, raw) for m in _V2_BYTE_RE.finditer(raw)]
    v1 = [_make_hit("v1", m, raw) for m in _V1_BYTE_RE.finditer(raw)]
    try:
        raw.decode("utf-8")
        is_utf8 = True
    except UnicodeDecodeError:
        is_utf8 = False
    return FileReport(path=path, v2=v2, v1=v1, is_utf8=is_utf8)


def scan_tree(root: Path, *, suffixes: tuple[str, ...] = (".md",)) -> list[FileReport]:
    """Scan every file under `root` whose suffix matches. Returns one FileReport
    per file that has at least one hit OR is not valid UTF-8 (clean files are
    omitted so the caller isn't flooded with no-ops)."""
    out: list[FileReport] = []
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix not in suffixes:
            continue
        rep = scan_file(p)
        if rep.v2 or rep.v1 or not rep.is_utf8:
            out.append(rep)
    return out


# ------------------------------------------------------------------- repair

def repair_v2_text(text: str) -> str:
    """Repair double-encoding mojibake in already-decoded text.

    The corruption: original `ç` (bytes `c3 a7`) was decoded as Latin-1 — byte
    `c3` -> `Ã`, byte `a7` -> `§` — then UTF-8-encoded AGAIN, yielding the bytes
    `c3 83 c2 a7`, which a UTF-8 pass now decodes back to the two chars `Ã§`
    (U+00C3, U+00A7). To invert: take those two chars, encode them as **Latin-1**
    (the reverse of the first mistaken decode — Latin-1 maps every byte 0-255
    one-to-one, so it is fully round-trippable), getting `c3 a7` back, then
    decode as UTF-8 to recover the original `ç`.

    Latin-1 (NOT cp1252) is required here: cp1252 leaves several byte slots
    undefined (0x81, 0x83, 0x8d, 0x8f, 0x90, 0x9d), and a v2 span can contain
    any byte in 0x80-0xff as its second char, so cp1252 would raise on spans
    Latin-1 handles cleanly. The original incident was a WIN1252 client-encoding
    bug in Postgres, but the file on disk is pure double-encoded UTF-8, and
    Latin-1 is the exact algebraic inverse.
    """
    return text.encode("latin-1").decode("utf-8")


def repair_v2_file(path: Path) -> int:
    """Repair a file in place. Only the V2 (double-encoding) spans are touched;
    everything else is byte-preserved. Returns the number of spans repaired."""
    raw = path.read_bytes()
    spans = [m.span() for m in _V2_BYTE_RE.finditer(raw)]
    if not spans:
        return 0
    # Rebuild the bytes: copy unaffected regions verbatim, repair each span by
    # decoding its bytes, undoing the double-encode, and re-encoding.
    out = bytearray()
    cursor = 0
    for start, end in spans:
        out += raw[cursor:start]
        bad = raw[start:end].decode("utf-8", errors="replace")
        out += repair_v2_text(bad).encode("utf-8")
        cursor = end
    out += raw[cursor:]
    path.write_bytes(bytes(out))
    return len(spans)


# ------------------------------------------------------------- classification

def classify_reports(reports: list[FileReport]) -> tuple[list[FileReport], list[FileReport]]:
    """Split reports into (v2_files, v1_only_files): files with any double-
    encoding vs. files with only accent-loss `?` (no v2). Files that are merely
    non-UTF-8 with neither hit land in neither list — the caller surfaces them
    separately as a hygiene finding."""
    v2_files = [r for r in reports if r.v2]
    v1_only = [r for r in reports if r.v1 and not r.v2]
    return v2_files, v1_only
