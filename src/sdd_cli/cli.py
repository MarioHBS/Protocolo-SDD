"""sdd -- Spec-Driven Development scaffolding CLI.

Design rule: this CLI is deliberately DUMB. It only does deterministic file
operations (copy templates, place a provider shim, record a manifest). All
reasoning -- understanding the project, asking questions, writing specs --
lives in the skills under .sdd/skills/ and runs inside your AI agent.
"""

import argparse
import json
import os
import re
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

from . import (
    _deps,
    _docs_plan,
    _mojibake,
    _session,
    _tracks,
    _user_files,
    manifest,
    providers,
)
from .content import CONTENT_DIR, KIT_VERSION

# ---------------------------------------------------------------- utilities

def _c(text: str, code: str) -> str:
    return text if not sys.stdout.isatty() else f"\033[{code}m{text}\033[0m"


def bold(t): return _c(t, "1")
def green(t): return _c(t, "32")
def yellow(t): return _c(t, "33")
def red(t): return _c(t, "31")
def dim(t): return _c(t, "2")


def die(msg: str) -> None:
    print(f"{red('error:')} {msg}", file=sys.stderr)
    raise SystemExit(1)


LANGUAGES = {
    "1": ("pt-BR", "Português (Brasil)"),
    "2": ("en", "English"),
    "3": ("es", "Español"),
}

MANAGED_DIRS = ("skills", "templates")
MANAGED_ROOT_FILES = ("README.md",)

# Canonical v2 state machine (see .sdd/README.md). The shims must list every
# one of these. IMPLEMENTING is an official v2 state -- the executor builds the
# active stage here; sdd-close is loaded when it ends.
V2_STATES = ("INITIALIZING", "DECIDING", "ROADMAP",
             "SPECIFYING", "IMPLEMENTING", "CLOSING")

V2_SECTIONS = (
    "Settings", "Current state",
    "1. Project vision", "2. Inviolable principles",
    "3. Locked structural decisions", "4. Open questions",
    "5. Stage index (CANONICAL)", "6. Structural change history",
    "7. Project decision conventions",
)

# v1 used Portuguese skill names; v2 uses English. Used by the migration-TODO.
V1_SKILL_MAP = {
    "sdd-iniciar": "sdd-init",
    "sdd-decidir": "sdd-decide",
    "sdd-especificar": "sdd-specify",
    "sdd-fechar": "sdd-close",
    "sdd-roadmap": "sdd-roadmap",  # unchanged
}

# Only IMPLEMENTANDO is auto-mapped; any other non-v2 state is surfaced to the
# owner (never guessed). The user explicitly chose this single mapping.
STATE_MAP = {"IMPLEMENTANDO": "IMPLEMENTING"}

# Portuguese equivalents of v2 headings, accepted as "present" so the migration
# does not add a duplicate section that already exists under a v1 name.
V1_HEADING_EQUIV = {
    "Estado atual": "Current state",
    "1. Visão do projeto": "1. Project vision",
    "2. Princípios invioláveis": "2. Inviolable principles",
    "3. Decisões estruturais travadas": "3. Locked structural decisions",
    "4. Perguntas em aberto": "4. Open questions",
    "5. Índice de etapas": "5. Stage index (CANONICAL)",
    "6. Histórico de mudanças estruturais": "6. Structural change history",
    "7. Convenções de decisão do projeto": "7. Project decision conventions",
}


def _copy_tree(src: Path, dst: Path, recorded: dict, root: Path) -> None:
    """Copy a directory, recording hashes of everything written."""
    for item in sorted(src.rglob("*")):
        if item.is_dir():
            continue
        rel = item.relative_to(src)
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
        recorded[str(target.relative_to(root)).replace("\\", "/")] = \
            manifest.hash_file(target)


def _install_shim(root: Path, prov: providers.Provider,
                  recorded: dict, force: bool) -> str:
    src = CONTENT_DIR / "shims" / prov.shim_source
    dst = root / prov.shim_path
    if dst.exists() and not force:
        return f"  {yellow('skip')}  {prov.shim_path} {dim('(already exists)')}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    recorded[prov.shim_path] = manifest.hash_file(dst)
    return f"  {green('ok')}    {prov.shim_path} {dim('-> ' + prov.invoke)}"


def _detect_providers(root: Path) -> list[str]:
    """Scan the project root for existing shim paths; return detected keys.

    Used only when a manifest is absent or lists no providers. ``generic`` is
    skipped as a detector because its shim_path (AGENTS.md) is not
    provider-specific -- a real provider is reported by its own shim file.
    """
    detected: list[str] = []
    for p in providers.PROVIDERS:
        if p.key == "generic":
            continue
        if (root / p.shim_path).exists():
            detected.append(p.key)
    return detected


def _detect_language(root: Path) -> tuple[str, str]:
    """Heuristic seed of the project language from the v1 constitution.

    Returns (code, confidence) where confidence is ``"detected"`` or
    ``"default"``. The migration-TODO ALWAYS asks the owner to confirm before
    the value is written -- this only proposes.
    """
    c = root / ".sdd" / "constitution.md"
    if not c.exists():
        return ("pt-BR", "default")
    try:
        text = c.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ("pt-BR", "default")

    if re.search(r"(^##\s.*Estado|Estado\s+atual|\*\*Estado:\*\*)", text):
        return ("pt-BR", "detected")
    if any(w in text for w in ("decisões", "etapas", "visão", "princípios")):
        return ("pt-BR", "detected")
    if "¿" in text or ("proyecto" in text and "ñ" in text):
        return ("es", "detected")
    if re.search(r"[一-鿿]", text):
        return ("zh", "detected")
    if "## Current state" in text or "## 1. Project vision" in text:
        return ("en", "detected")
    return ("pt-BR", "default")  # SDD v1 default


def _kit_hash(rel_source: Path) -> str:
    """Hash of a bundled content file (to detect kit-identical copies)."""
    return manifest.hash_file(rel_source)


def _backup_managed(root: Path, sdd: Path,
                    old: dict | None, recorded: dict) -> tuple[Path | None, list[str]]:
    """Back up existing managed files before overwriting. Returns (backup_dir,
    backed-up relative paths). When ``old`` is None (v1, no manifest) every
    existing managed file is backed up -- there is no baseline to diff against.
    When ``old`` exists, only hand-edited files (current hash != recorded) are
    backed up. kit-identical files (no user content to lose) are skipped.

    The backup lives in a timestamped subdir so repeated migrates never clobber
    a prior backup.
    """
    managed_paths: list[Path] = []
    for name in MANAGED_ROOT_FILES:
        f = sdd / name
        if f.exists():
            managed_paths.append(f)
    for d in MANAGED_DIRS:
        dd = sdd / d
        if dd.exists():
            managed_paths.extend(x for x in dd.rglob("*") if x.is_file())
    # Shims referenced by an existing manifest, if any.
    if old:
        for rel in old.get("managed_files", {}):
            f = root / rel
            if f.exists() and f not in managed_paths:
                managed_paths.append(f)

    to_backup: list[Path] = []
    old_files = old.get("managed_files", {}) if old else {}
    src_sdd = CONTENT_DIR / "sdd"
    for f in managed_paths:
        rel = str(f.relative_to(root)).replace("\\", "/")
        cur_hash = manifest.hash_file(f)
        # Skip if byte-identical to the kit's own source (no user content lost).
        kit_rel = {
            ".sdd/README.md": src_sdd / "README.md",
        }.get(rel)
        if kit_rel and kit_rel.exists() and cur_hash == manifest.hash_file(kit_rel):
            continue
        # Only back up hand-edited files (current differs from recorded).
        if old and rel in old_files and cur_hash == old_files[rel]:
            continue  # unmodified since last install -- nothing to lose
        to_backup.append(f)

    if not to_backup:
        return (None, [])

    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    bdir = sdd / ".pre-migrate-backup" / ts
    bdir.mkdir(parents=True, exist_ok=True)
    backed: list[str] = []
    for f in to_backup:
        rel = str(f.relative_to(root)).replace("\\", "/")
        # Flatten any leading .sdd/ so backups sit at a readable depth.
        flat = rel
        dst = bdir / flat
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dst)
        backed.append(rel)
    return (bdir, backed)


def _normalize_file(path: Path) -> bool:
    """Rewrite a file as UTF-8 (no BOM) with LF line endings. Idempotent.
    Returns True if the bytes changed."""
    data = path.read_bytes()
    # Strip BOM if present.
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    text = data.decode("utf-8", errors="replace")
    new_text = text.replace("\r\n", "\n").replace("\r", "\n")
    new_bytes = new_text.encode("utf-8")
    if new_bytes == path.read_bytes():
        return False
    path.write_bytes(new_bytes)
    return True


# -------------------------------------------------------------------- init

def cmd_init(args) -> None:
    root = Path(args.path).resolve()
    if not root.exists():
        die(f"path does not exist: {root}")

    existing = manifest.load(root)
    if existing and not args.force:
        print(f"{yellow('note:')} .sdd/ already initialized "
              f"(kit {existing.get('kit_version')}).")
        print("      Use 'sdd migrate --to v4' to upgrade, or --force to "
              "reinstall managed files.")
        raise SystemExit(0)

    interactive = sys.stdin.isatty() and not args.yes

    # --- language -----------------------------------------------------
    language = args.language
    if not language:
        if interactive:
            print(bold("\nLanguage for interactions and generated artifacts"))
            print(dim("  (skill instructions stay in English regardless)"))
            for k, (code, label) in LANGUAGES.items():
                print(f"  {k}) {label} [{code}]")
            choice = input("Choose [1]: ").strip() or "1"
            language = LANGUAGES.get(choice, LANGUAGES["1"])[0]
        else:
            language = "pt-BR"

    # --- providers ----------------------------------------------------
    chosen: list[providers.Provider] = []
    if args.provider:
        for key in args.provider:
            p = providers.get(key)
            if not p:
                die(f"unknown provider '{key}'. Run 'sdd providers' to list.")
            chosen.append(p)
    elif interactive:
        print(bold("\nWhich AI agent(s) will use this project?"))
        print(dim("  Multiple allowed (e.g. 1,3) -- they all share one .sdd/"))
        for i, p in enumerate(providers.PROVIDERS, 1):
            print(f"  {i:>2}) {p.name} {dim('[' + p.kind + ']')}")
        raw = input("Choose [1]: ").strip() or "1"
        for tok in raw.replace(" ", "").split(","):
            if tok.isdigit() and 1 <= int(tok) <= len(providers.PROVIDERS):
                chosen.append(providers.PROVIDERS[int(tok) - 1])
        if not chosen:
            die("no valid provider selected")
    else:
        chosen = [providers.BY_KEY["generic"]]

    # --- feature flags -------------------------------------------------
    features = {
        "estimation": bool(args.estimation),
        "documentation": bool(args.docs),
        "tracks": bool(args.tracks),
        "edd": bool(getattr(args, "edd", False)),
    }
    if interactive and not args.estimation and not args.docs and not args.tracks:
        print(bold("\nOptional features") + dim("  (toggle later in the constitution)"))
        features["estimation"] = input(
            "  Track schedule estimates? [y/N]: ").strip().lower().startswith("y")
        features["documentation"] = input(
            "  Enable documentation generation? [y/N]: "
        ).strip().lower().startswith("y")
        features["tracks"] = input(
            "  Enable parallel tracks (sdd-track)? [y/N]: "
        ).strip().lower().startswith("y")

    # --- install -------------------------------------------------------
    print(bold(f"\nInstalling SDD kit {KIT_VERSION} into {root}"))
    recorded: dict[str, str] = {}
    sdd_src = CONTENT_DIR / "sdd"
    sdd_dst = root / ".sdd"
    sdd_dst.mkdir(exist_ok=True)

    for name in MANAGED_ROOT_FILES:
        shutil.copy2(sdd_src / name, sdd_dst / name)
        recorded[f".sdd/{name}"] = manifest.hash_file(sdd_dst / name)
        print(f"  {green('ok')}    .sdd/{name}")

    for d in MANAGED_DIRS:
        _copy_tree(sdd_src / d, sdd_dst / d, recorded, root)
        print(f"  {green('ok')}    .sdd/{d}/")

    # user-owned files with seed: only created if absent, never overwritten. The
    # constitution/roadmap get placeholder substitution; CHANGELOG.md is a pure
    # template copy (English skeleton, no placeholders) — it is user-owned so a
    # migrate never discards the project's accumulated structural history.
    for name in ("constitution.md", "roadmap.md"):
        target = sdd_dst / name
        if target.exists():
            print(f"  {yellow('keep')}  .sdd/{name} {dim('(yours, untouched)')}")
        else:
            text = (sdd_src / name).read_text(encoding="utf-8")
            text = text.replace("{{LANGUAGE}}", language)
            text = text.replace("{{ESTIMATION}}",
                                "on" if features["estimation"] else "off")
            text = text.replace("{{DOCUMENTATION}}",
                                "on" if features["documentation"] else "off")
            text = text.replace("{{TRACKS}}",
                                "on" if features["tracks"] else "off")
            text = text.replace("{{EDD}}", "on" if features["edd"] else "off")
            target.write_text(text, encoding="utf-8", newline="\n")
            print(f"  {green('ok')}    .sdd/{name}")

    cg = sdd_dst / "CHANGELOG.md"
    if cg.exists():
        print(f"  {yellow('keep')}  .sdd/CHANGELOG.md {dim('(yours, untouched)')}")
    else:
        shutil.copy2(sdd_src / "templates" / "CHANGELOG.template.md", cg)
        print(f"  {green('ok')}    .sdd/CHANGELOG.md")

    evaluation_dir = sdd_dst / "kit-evaluation"
    evaluation = evaluation_dir / "README.md"
    if evaluation.exists():
        print(f"  {yellow('keep')}  .sdd/kit-evaluation/README.md {dim('(yours, untouched)')}")
    else:
        evaluation_dir.mkdir(exist_ok=True)
        shutil.copy2(sdd_src / "templates" / "kit-evaluation.template.md", evaluation)
        print(f"  {green('ok')}    .sdd/kit-evaluation/README.md")
        print(dim("  suggestion: add /.sdd/kit-evaluation/ to .gitignore (local evaluation evidence)"))

    (sdd_dst / "stages").mkdir(exist_ok=True)
    (sdd_dst / "stages" / ".gitkeep").touch()

    (sdd_dst / "tracks").mkdir(exist_ok=True)
    (sdd_dst / "tracks" / ".gitkeep").touch()

    ga = root / ".gitattributes"
    if not ga.exists():
        shutil.copy2(CONTENT_DIR / "gitattributes.txt", ga)
        print(f"  {green('ok')}    .gitattributes {dim('(enforces LF)')}")

    print(bold("\nProvider shims"))
    for p in chosen:
        print(_install_shim(root, p, recorded, args.force))

    initial_manifest = manifest.build(KIT_VERSION, language, [p.key for p in chosen], features, recorded)
    initial_manifest["dashboard_renderer"] = getattr(args, "dashboard_ui", "rich") or "rich"
    manifest.save(root, initial_manifest)

    print(bold("\nDone.") + f"  language={language}  "
          f"estimation={'on' if features['estimation'] else 'off'}  "
          f"docs={'on' if features['documentation'] else 'off'}  "
          f"tracks={'on' if features['tracks'] else 'off'}")
    print(dim("\nNext: open your agent and trigger "
              f"{chosen[0].invoke} -- it will read .sdd/ and start the "
              "INITIALIZING phase."))


# --------------------------------------------------------------- providers

def cmd_providers(args) -> None:
    if args.plain:
        print("\n".join(providers.keys()))
        return
    print(bold(f"Supported providers ({len(providers.PROVIDERS)})\n"))
    w = max(len(p.key) for p in providers.PROVIDERS)
    for p in providers.PROVIDERS:
        print(f"  {bold(p.key.ljust(w))}  {p.name}")
        print(f"  {' ' * w}  {dim(p.kind + ' | ' + p.shim_path + ' | ' + p.invoke)}")
    print(dim("\nUse: sdd init --provider <key> [--provider <key> ...]"))
    print(dim("Machine-readable list: sdd providers --plain"))


# -------------------------------------------------------------------- docs

def cmd_docs(args) -> None:
    text = (CONTENT_DIR / "USAGE.md").read_text(encoding="utf-8")
    text = text.replace("{{VERSION}}", KIT_VERSION)
    text = text.replace("{{PROVIDERS}}", ", ".join(providers.keys()))
    if args.md:
        out = Path(args.md if isinstance(args.md, str) else "SDD-USAGE.md")
        out.write_text(text, encoding="utf-8", newline="\n")
        print(f"{green('ok')}  wrote {out}")
    else:
        print(text)


# ``docs`` was the original name of this command.  Keep it as a compatibility
# alias until v5, but make the unambiguous name available to people and agents.
def cmd_manual(args) -> None:
    cmd_docs(args)


def _constitution_sections(path: Path) -> list[tuple[str, int]]:
    """Return H2 headings and their UTF-8 byte sizes (read-only)."""
    text = path.read_text(encoding="utf-8", errors="replace")
    matches = list(re.finditer(r"(?m)^##\s+(.+?)\s*$", text))
    result = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        result.append((match.group(1), len(text[match.start():end].encode("utf-8"))))
    return result


def _context_payload(root: Path, budget: bool = False) -> dict:
    sdd = root / ".sdd"
    constitution = sdd / "constitution.md"
    if not constitution.is_file():
        die(f"no .sdd/constitution.md found in {root}")
    text = constitution.read_text(encoding="utf-8", errors="replace")
    # Settings and Current state are deliberately the only constitution content
    # loaded during session startup.  Skills load other sections on demand.
    cutoff = re.search(r"(?m)^##\s+1\.\s", text)
    startup = text[:cutoff.start()] if cutoff else text
    state, stage = _scope_state(root)
    data = {"version": 1, "command": "context", "project": str(root),
            "settings_and_current_state": startup, "state": state,
            "active_stage": stage}
    if stage:
        active = _find_stage(root, stage)
        data["active_paths"] = ({name: str((active / name).relative_to(root)).replace("\\", "/")
                                 for name in ("spec.md", "todo.md") if (active / name).exists()}
                                if active else {})
    if budget:
        def row(kind: str, path: Path, size: int, part: str = "") -> dict:
            rel = str(path.relative_to(root)).replace("\\", "/")
            return {"class": kind, "path": rel, "part": part, "bytes": size,
                    "estimated_tokens": (size + 3) // 4}

        head_bytes = len(startup.encode("utf-8"))
        total_bytes = len(text.encode("utf-8"))
        rows = []
        if (sdd / "README.md").is_file():
            rows.append(row("hot", sdd / "README.md", (sdd / "README.md").stat().st_size))
        rows.append(row("hot", constitution, head_bytes, "Settings + Current state"))
        # Provider shims are read by the host agent before anything else.
        for key in (manifest.load(root) or {}).get("providers") or []:
            entry = next((x for x in providers.PROVIDERS if x.key == key), None)
            if entry and (root / entry.shim_path).is_file():
                rows.append(row("hot", root / entry.shim_path, (root / entry.shim_path).stat().st_size))
        rows.append(row("cold", constitution, total_bytes - head_bytes, "sections 1-7, on demand"))
        for name in ("roadmap.md", "estimates.md", "CHANGELOG.md"):
            if (sdd / name).is_file():
                rows.append(row("cold", sdd / name, (sdd / name).stat().st_size))
        data["budget"] = rows
        hot_bytes = sum(x["bytes"] for x in rows if x["class"] == "hot")
        data["startup_estimated_tokens"] = (hot_bytes + 3) // 4
        # What startup cost when the whole constitution was read (pre-4.1.0 shims).
        data["full_read_estimated_tokens"] = (hot_bytes + total_bytes - head_bytes + 3) // 4
    return data


def cmd_context(args) -> None:
    data = _context_payload(Path(args.path).resolve(), args.budget)
    if args.json:
        _emit_json(data)
        return
    print(data["settings_and_current_state"].rstrip())
    print(f"\nActive stage: {data['active_stage'] or '(none)'}")
    for name, path in data.get("active_paths", {}).items():
        print(f"  {name}: {path}")
    if args.budget:
        print("\nContext budget (bytes/4 is an estimate):")
        for row in data["budget"]:
            part = f" ({row['part']})" if row.get("part") else ""
            print(f"  {row['class']:4} {row['path']}{part}: {row['bytes']} B ~= {row['estimated_tokens']} tokens")
        print(f"  startup total: ~= {data['startup_estimated_tokens']} tokens "
              f"(reading the whole constitution would be ~= {data['full_read_estimated_tokens']})")


# ----------------------------------------------------------------- migrate

def cmd_doctor(args) -> None:
    """Audit the project's `.sdd/` — mojibake + user-file hygiene. Reports only;
    never rewrites a file."""
    root = Path(args.path).resolve()
    sdd = root / ".sdd"
    if getattr(args, "json", False):
        payload = _doctor_payload(root)
        _emit_json(payload)
        if payload["status"]:
            raise SystemExit(payload["status"])
        return

    print(bold(f"doctor — {root}"))

    # --- SDD presence + version -------------------------------------------
    # The doctor's first job is to tell whether this is an SDD project at all,
    # and which kit version is installed. The rest of the audit (mojibake +
    # hygiene) only makes sense once an .sdd/ exists.
    if not sdd.exists():
        print(f"  {yellow('note')}  no .sdd/ here — not an SDD project.")
        print(dim("        Run 'sdd init' to scaffold one."))
        raise SystemExit(0)

    m = manifest.load(root)
    if m is None:
        # Legacy v1 install: no .sdd/.sdd-manifest.json. Same literal used by
        # `migrate` (cmd_migrate) so the two commands agree on what to call it.
        project_ver = "v1 (no manifest)"
        print(f"  sdd    {project_ver}")
        print(dim("        Legacy install (no .sdd/.sdd-manifest.json). "
                  "Run 'sdd migrate --to v4' to record a manifest and upgrade."))
    else:
        project_ver = m.get("kit_version") or "unknown"
        print(f"  sdd    {project_ver}")
    print()

    # --- mojibake ---
    reports = _mojibake.scan_tree(sdd)
    v2_files, v1_only = _mojibake.classify_reports(reports)
    non_utf8 = [r for r in reports if not r.is_utf8]

    status = 0
    if v2_files:
        status = 1
        print(red(f"\n{red('ERROR')} double-encoding mojibake (v2) in "
                  f"{len(v2_files)} file(s) — deterministic, fixable with "
                  "--fix-mojibake"))
        for r in v2_files:
            rel = r.path.relative_to(root)
            sample = r.v2[0].snippet if r.v2 else ""
            print(f"  {red('v2')}   {rel} {dim('(' + str(len(r.v2)) + ' hits)')} "
                  f"{dim('e.g. ' + repr(sample))}")
        print(dim("    Repair: re-run migrate with --fix-mojibake (only v2 is "
                  "touched; v1 `?` is left for manual review)."))

    if v1_only:
        print(yellow(f"\n{yellow('WARN')} accent-loss (`?` for accents, v1) in "
                     f"{len(v1_only)} file(s) — NOT auto-fixed: a `?` next to a "
                     "letter may be a real question mark. Review by hand."))
        for r in v1_only[:20]:
            rel = r.path.relative_to(root)
            print(f"  {yellow('v1')}   {rel} {dim('(' + str(len(r.v1)) + ' hits)')}")
        if len(v1_only) > 20:
            print(dim(f"    ...and {len(v1_only) - 20} more files"))

    if non_utf8:
        status = max(status, 1)
        print(red(f"\n{red('ERROR')} {len(non_utf8)} file(s) are not valid UTF-8"))
        for r in non_utf8:
            print(f"  {red('enc')}  {r.path.relative_to(root)}")

    if not reports:
        print(green("  ok    no mojibake detected"))

    # --- session (read-only) ---
    session_data = _session.load(root)
    session_issues = _session.validate(root, session_data)
    if session_data and not session_data.get("invalid"):
        print(f"  session {session_data.get('state', 'unknown').lower()} "
              f"stage={session_data.get('active_stage') or '(none)'}")
    for issue in session_issues:
        print(yellow(f"  WARN session: {issue}"))

    # --- user-file hygiene (audit-only) ---
    hyg = _user_files.scan_hygiene(sdd)
    print(bold("\nhygiene — stages & indexes"))
    if hyg.closed_with_open_todo:
        print(yellow(f"  {yellow('WARN')} closed stage with open todo.md "
                     f"checkboxes ({len(hyg.closed_with_open_todo)}):"))
        note = dim('(report.md exists; complete the work or '
                   'record the divergence in report §7)')
        for d in hyg.closed_with_open_todo:
            print(f"    - {d.stage}: {d.open_checkboxes}/{d.total_checkboxes} "
                  f"unchecked {note}")
    else:
        print(green("  ok    no closed stage with open checkboxes"))

    if hyg.spec_without_todo:
        print(yellow(f"  {yellow('WARN')} stage with spec but no todo.md "
                     f"({len(hyg.spec_without_todo)}):"))
        for name in hyg.spec_without_todo:
            print(f"    - {name}")
    else:
        print(green("  ok    every spec'd stage has a todo.md"))

    if hyg.track_divergences:
        print(yellow(f"  {yellow('WARN')} track hygiene "
                     f"({len(hyg.track_divergences)}):"))
        for t in hyg.track_divergences:
            print(f"    - {t.track} [{t.kind}]: {t.detail}")

    if not hyg.changelog_exists:
        print(yellow("  note  no CHANGELOG.md — the constitution §6 is an index "
                     "pointing here; create it with 'sdd init' (new) or migrate "
                     "(legacy)."))
    else:
        print(green("  ok    CHANGELOG.md present"))

    if status:
        raise SystemExit(status)
    print(bold("\nclean.") if not (hyg.closed_with_open_todo
                                  or hyg.spec_without_todo) else "")


_STAGE_NUMBER_RE = re.compile(r"\b(\d{3}(?:-[A-Za-z])?)\b")


def _find_stage(root: Path, raw: str, track: str | None = None) -> Path | None:
    """Resolve a stage folder from an ``Active stage`` value without dying.

    The field is free text in real projects ("Etapa 091 (`slug`) especificada e
    travada..."), so try, in order: the value as a folder name, each backticked
    slug (folder name or ``NNN-<slug>`` suffix), then a lone ``NNN`` number.
    """
    base = root / ".sdd" / "tracks" / track / "stages" if track else root / ".sdd" / "stages"
    if not base.is_dir():
        return None
    folders = [p for p in base.iterdir() if p.is_dir()]
    slugs = [x.strip() for x in re.findall(r"`([^`]+)`", raw)]
    for token in slugs + [raw.strip()]:
        if not token:
            continue
        exact = [p for p in folders if p.name == token]
        if exact:
            return exact[0]
        suffixed = [p for p in folders if p.name.endswith("-" + token)]
        if len(suffixed) == 1:
            return suffixed[0]
    for number in _STAGE_NUMBER_RE.findall(raw):
        prefixed = [p for p in folders if p.name.startswith(number + "-")]
        if len(prefixed) == 1:
            return prefixed[0]
    return None


def _scope_state(root: Path, track: str | None = None) -> tuple[str | None, str | None]:
    """Read the small current-state pointer without owning or rewriting it."""
    path = root / ".sdd" / "tracks" / track / "state.md" if track else root / ".sdd" / "constitution.md"
    if not path.is_file():
        return None, None
    text = path.read_text(encoding="utf-8", errors="replace")
    state = re.search(r"(?im)^[-*]?\s*\*\*(?:State|Estado):\*\*\s*([A-Z_]+)", text)
    stage = re.search(r"(?im)^[-*]?\s*\*\*(?:Active stage|Active stage in this track):\*\*\s*(.+)$", text)
    if not stage:
        return (state.group(1) if state else None, None)
    raw = stage.group(1).strip()
    found = _find_stage(root, raw, track)
    if found:
        return (state.group(1) if state else None, found.name)
    ticked = re.search(r"`([^`]+)`", raw)
    return (state.group(1) if state else None, (ticked.group(1) if ticked else raw).strip())


def _doctor_payload(root: Path) -> dict:
    sdd = root / ".sdd"
    if not sdd.is_dir():
        return {"version": 1, "command": "doctor", "project": str(root),
                "status": 0, "sdd": None, "findings": [{"severity": "note", "code": "no_sdd"}]}
    reports = _mojibake.scan_tree(sdd)
    hyg = _user_files.scan_hygiene(sdd)
    findings: list[dict] = []
    for report in reports:
        rel = str(report.path.relative_to(root)).replace("\\", "/")
        for hit in report.v2:
            findings.append({"severity": "error", "code": "mojibake_v2", "path": rel,
                             "offset": hit.offset, "actionable": True})
        for hit in report.v1:
            findings.append({"severity": "warn", "code": "mojibake_v1", "path": rel,
                             "offset": hit.offset, "actionable": False})
        if not report.is_utf8:
            findings.append({"severity": "error", "code": "invalid_utf8", "path": rel,
                             "actionable": False})
    for stage in hyg.spec_without_todo:
        findings.append({"severity": "warn", "code": "spec_without_todo", "stage": stage})
    for item in hyg.closed_with_open_todo:
        findings.append({"severity": "warn", "code": "closed_open_todo", "stage": item.stage,
                         "open": item.open_checkboxes})
    for item in hyg.track_divergences:
        findings.append({"severity": "warn", "code": f"track_{item.kind}",
                         "track": item.track, "track_state": item.track_state, "detail": item.detail})
    manifest_data = manifest.load(root)
    constitution = sdd / "constitution.md"
    if constitution.is_file():
        ctext = constitution.read_text(encoding="utf-8", errors="replace")
        size = constitution.stat().st_size
        if size > 24 * 1024:
            largest = sorted(_constitution_sections(constitution), key=lambda x: x[1], reverse=True)[:3]
            findings.append({"severity": "warn", "code": "constitution_oversized", "bytes": size,
                             "sections": [{"heading": h, "bytes": b} for h, b in largest]})
        headings = re.findall(r"(?m)^##\s+(.+?)\s*$", ctext)
        duplicates = sorted({h for h in headings if headings.count(h) > 1})
        for heading in duplicates:
            findings.append({"severity": "warn", "code": "duplicate_h2", "heading": heading})
        for line_no, line in enumerate(ctext.splitlines(), 1):
            if "|" in line and len(line.encode("utf-8")) > 600:
                findings.append({"severity": "warn", "code": "long_table_cell", "line": line_no})
            if "file:///" in line.lower():
                findings.append({"severity": "warn", "code": "abs_file_links", "line": line_no,
                                 "actionable": True})
        settings = {m.group(1).strip().lower(): m.group(2).strip().lower()
                    for m in re.finditer(r"(?m)^[-*]\s+\*\*([^*]+):\*\*\s*([^\n]+)", ctext)}
        feature_names = {"estimation tracking": "estimation", "documentation": "documentation",
                         "parallel tracks": "tracks", "eval driven development": "edd"}
        for label, key in feature_names.items():
            if label in settings and key in (manifest_data or {}).get("features", {}):
                expected = settings[label].split()[0] in {"on", "true", "yes"}
                actual = bool(manifest_data["features"][key])
                if expected != actual:
                    findings.append({"severity": "warn", "code": "feature_mismatch", "feature": key,
                                     "constitution": expected, "manifest": actual, "actionable": True})
    for p in providers.PROVIDERS:
        if p.key != "generic" and (root / p.shim_path).exists() and p.key not in (manifest_data or {}).get("providers", []):
            findings.append({"severity": "warn", "code": "provider_shim_unmanaged", "provider": p.key,
                             "path": p.shim_path, "actionable": True})
    if manifest_data:
        try:
            if manifest.parse_version(manifest_data.get("kit_version", "0.0.0")) > manifest.parse_version(KIT_VERSION):
                findings.append({"severity": "warn", "code": "cli_older_than_project"})
        except ValueError:
            pass
    for name in ("roadmap.md", "estimates.md", "CHANGELOG.md"):
        path = sdd / name
        if path.is_file() and path.stat().st_size > 48 * 1024:
            findings.append({"severity": "note", "code": "cold_file_oversized", "path": f".sdd/{name}",
                             "bytes": path.stat().st_size})
    if (manifest_data or {}).get("features", {}).get("edd"):
        for stage in sorted((sdd / "stages").glob("*")) if (sdd / "stages").is_dir() else []:
            if not stage.is_dir() or not (stage / "spec.md").is_file():
                continue
            if not (stage / "evals.md").is_file():
                findings.append({"severity": "warn", "code": "edd_missing_evals", "stage": stage.name})
            if (stage / "report.md").is_file() and not (stage / "checklist.md").is_file():
                findings.append({"severity": "warn", "code": "edd_missing_checklist", "stage": stage.name})
            if (stage / "report.md").is_file() and (stage / "evals.md").is_file():
                eval_ids = set(re.findall(r"\bE-\d{3}\b", (stage / "evals.md").read_text(encoding="utf-8", errors="replace")))
                evidence = ""
                for name in ("checklist.md", "report.md"):
                    path = stage / name
                    if path.is_file():
                        evidence += path.read_text(encoding="utf-8", errors="replace")
                missing = sorted(eval_ids - set(re.findall(r"\bE-\d{3}\b", evidence)))
                for eval_id in missing:
                    findings.append({"severity": "warn", "code": "edd_eval_uncovered",
                                     "stage": stage.name, "eval": eval_id})
        if (sdd / "milestones").is_dir() and not (sdd / "avaliacao-desempenho.md").is_file():
            findings.append({"severity": "note", "code": "edd_missing_performance_doc"})
    saved_session = _session.load(root)
    for issue in _session.validate(root, saved_session):
        findings.append({"severity": "warn", "code": "session_inconsistent", "detail": issue})
    constitution_state, _ = _scope_state(root)
    if saved_session and not saved_session.get("invalid") and constitution_state != "IMPLEMENTING":
        findings.append({"severity": "warn", "code": "session_state_mismatch",
                         "detail": f"session exists while constitution is {constitution_state or 'unknown'}"})
    for issue in _deps.findings(root):
        findings.append({"severity": "warn", "code": "dependency_inconsistent", "detail": issue})
    try:
        for conflict in _tracks.check(root):
            findings.append({"severity": "error", "code": "track_overlap", "detail": conflict})
    except ValueError as exc:
        findings.append({"severity": "warn", "code": "track_claims_invalid", "detail": str(exc)})
    for duplicate in _tracks.duplicate_numbers(root):
        findings.append({"severity": "error", "code": "sequence_duplicate", **duplicate})
    branch = _tracks.current_branch(root)
    if branch:
        scopes = [(None, saved_session)] + [(slug, _session.load(root, slug))
                                            for slug in _tracks.active_tracks(root)]
        for slug, saved in scopes:
            if not saved or saved.get("invalid"):
                continue
            expected = saved.get("branch")
            if slug and not expected:
                try:
                    expected = _tracks.load(root, slug).get("branch")
                except ValueError:
                    expected = None
            if expected and expected != branch:
                findings.append({"severity": "warn", "code": "session_branch_mismatch",
                                 "track": slug, "expected": expected, "current": branch})
    dot_git = root / ".git"
    if dot_git.is_file():
        findings.append({"severity": "warn", "code": "inside_linked_worktree",
                         "detail": "linked worktree has a separate, potentially stale .sdd/ copy"})
    for worktree_dir in (root / ".kilo" / "worktrees", root / ".claude" / "worktrees", root / ".cursor" / "worktrees"):
        if not worktree_dir.is_dir():
            continue
        copies = [path for path in worktree_dir.iterdir() if path.is_dir() and (path / ".sdd").is_dir()]
        if copies:
            findings.append({"severity": "warn", "code": "nested_worktree_copies",
                             "path": str(worktree_dir.relative_to(root)).replace("\\", "/"),
                             "count": len(copies),
                             "hint": "run 'sdd fix --gitignore' and exclude this folder from test, lint "
                                     "and type-check globs (vitest/eslint/tsc/pytest); never read or edit "
                                     ".sdd/ inside it"})
    return {"version": 1, "command": "doctor", "project": str(root),
            "sdd": (manifest_data or {}).get("kit_version", "v1 (no manifest)"),
            "status": 1 if any(x["severity"] == "error" for x in findings) else 0,
            "findings": findings}


def _emit_json(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False, sort_keys=True))


_FILE_LINK_RE = re.compile(r"file:///[^\s)`>\"]+")
_AGENT_WORKTREE_DIRS = (".kilo/worktrees", ".claude/worktrees", ".cursor/worktrees")


def _relativize_file_links(text: str, root: Path) -> str:
    """Rewrite absolute ``file:///`` links into links relative to ``.sdd/``.

    The constitution lives in ``.sdd/``, so a target ``<root>/.sdd/stages/x`` becomes
    ``stages/x`` and one outside ``.sdd/`` becomes ``../...``. A link from a moved
    or foreign checkout is still recognised when it contains ``/.sdd/``. Anything
    else is left alone.
    """
    from urllib.parse import unquote

    root_posix = root.resolve().as_posix().lower().rstrip("/") + "/"

    def convert(match: re.Match[str]) -> str:
        target = unquote(match.group(0)[len("file:///"):])
        lowered = target.lower()
        if lowered.startswith(root_posix.lstrip("/")):
            rel = target[len(root_posix.lstrip("/")):]
        elif "/.sdd/" in lowered:
            rel = ".sdd/" + target[lowered.index("/.sdd/") + len("/.sdd/"):]
        else:
            return match.group(0)
        return rel[len(".sdd/"):] if rel.startswith(".sdd/") else "../" + rel

    return _FILE_LINK_RE.sub(convert, text)


def _missing_worktree_ignores(root: Path) -> list[str]:
    """``.gitignore`` entries for agent worktree folders that exist but are not ignored."""
    ignore = root / ".gitignore"
    lines = {x.strip().strip("/") for x in ignore.read_text(encoding="utf-8", errors="replace").splitlines()} \
        if ignore.is_file() else set()
    return [f"/{name}/" for name in _AGENT_WORKTREE_DIRS
            if (root / name).is_dir() and name not in lines]


def cmd_fix(args) -> None:
    """Repair only deterministic SDD file problems."""
    root = Path(args.path).resolve()
    sdd = root / ".sdd"
    if not sdd.is_dir():
        die(f"no .sdd/ found in {root}. Run 'sdd init' first.")
    dry_run = bool(getattr(args, "dry_run", False))
    use_mojibake = bool(getattr(args, "mojibake", False) or getattr(args, "all", False))
    use_eol = bool(getattr(args, "eol", False) or getattr(args, "all", False))
    use_links = bool(getattr(args, "links", False) or getattr(args, "all", False))
    use_features = bool(getattr(args, "features", False) or getattr(args, "all", False))
    use_gitignore = bool(getattr(args, "gitignore", False))  # opt-in: never part of --all
    if not (use_mojibake or use_eol or use_links or use_features or use_gitignore):
        use_mojibake = use_eol = use_links = use_features = True
    repairs: list[dict] = []
    unresolved: list[dict] = []
    reports = _mojibake.scan_tree(sdd, suffixes=(".md", ".json"))
    for report in reports:
        rel = str(report.path.relative_to(root)).replace("\\", "/")
        if report.v2 and use_mojibake:
            repairs.append({"kind": "mojibake_v2", "path": rel, "count": len(report.v2)})
            if not dry_run:
                _mojibake.repair_v2_file(report.path)
        if not report.is_utf8:
            unresolved.append({"kind": "invalid_utf8", "path": rel})
    if use_eol:
        for path in sorted(sdd.rglob("*")):
            if not path.is_file() or path.suffix not in {".md", ".json"}:
                continue
            try:
                raw = path.read_bytes()
                raw.decode("utf-8")
            except UnicodeDecodeError:
                continue
            normalized = raw[3:] if raw.startswith(b"\xef\xbb\xbf") else raw
            normalized = normalized.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
            if normalized != raw:
                repairs.append({"kind": "encoding_eol", "path": str(path.relative_to(root)).replace("\\", "/")})
                if not dry_run:
                    path.write_bytes(normalized)
    constitution = sdd / "constitution.md"
    if use_links and constitution.is_file():
        text = constitution.read_text(encoding="utf-8", errors="replace")
        changed = _relativize_file_links(text, root)
        if changed != text:
            repairs.append({"kind": "absolute_file_links", "path": ".sdd/constitution.md"})
            if not dry_run:
                constitution.write_text(changed, encoding="utf-8", newline="\n")
    if use_features and constitution.is_file():
        data = manifest.load(root)
        if data:
            text = constitution.read_text(encoding="utf-8", errors="replace")
            labels = {"estimation": "Estimation tracking", "documentation": "Documentation",
                      "tracks": "Parallel tracks", "edd": "Eval Driven Development"}
            updated = False
            for key, label in labels.items():
                found = re.search(rf"(?im)^([-*]\s+\*\*{re.escape(label)}:\*\*\s*)(on|off|true|false|yes|no)", text)
                if found:
                    value = found.group(2).lower() in {"on", "true", "yes"}
                    if data.setdefault("features", {}).get(key) != value:
                        data["features"][key] = value
                        updated = True
            if updated:
                repairs.append({"kind": "feature_manifest_sync", "path": ".sdd/.sdd-manifest.json"})
                if not dry_run:
                    manifest.save(root, data)
    if use_gitignore:
        if not (root / ".git").exists():
            unresolved.append({"kind": "gitignore_without_git", "path": ".gitignore"})
        else:
            missing = _missing_worktree_ignores(root)
            if missing:
                repairs.append({"kind": "gitignore_worktrees", "path": ".gitignore", "entries": missing})
                if not dry_run:
                    ignore = root / ".gitignore"
                    existing = ignore.read_text(encoding="utf-8") if ignore.is_file() else ""
                    sep = "" if not existing or existing.endswith("\n") else "\n"
                    ignore.write_text(existing + sep + "# Agent worktrees are full copies of the repo (and of .sdd/)\n"
                                      + "\n".join(missing) + "\n", encoding="utf-8", newline="\n")
    status = 2 if unresolved else (1 if repairs else 0)
    result = {"version": 1, "command": "fix", "project": str(root), "dry_run": dry_run,
              "status": status, "repairs": repairs, "unresolved": unresolved}
    if getattr(args, "json", False):
        _emit_json(result)
    else:
        for item in repairs:
            print(f"{'would fix' if dry_run else 'fixed'} {item['kind']}: {item['path']}")
        for item in unresolved:
            print(f"{yellow('unfixable')} {item['kind']}: {item['path']}")
        if not repairs and not unresolved:
            print(green("clean — nothing deterministic to repair"))
    if status:
        raise SystemExit(status)


def cmd_session(args) -> None:
    root = Path(args.path).resolve()
    track = getattr(args, "track", None)
    if not (root / ".sdd").is_dir():
        die(f"no .sdd/ found in {root}")
    state, stage = _scope_state(root, track)
    action = args.session_command
    current = _session.load(root, track)
    if action == "sync":
        if state == "IMPLEMENTING":
            current = current if current and not current.get("invalid") else _session.new(state, stage)
            current["state"] = "IMPLEMENTING"
            current["active_stage"] = stage
            current["branch"] = _tracks.current_branch(root)
            current["updated_at"] = _session.now()
            path = _session.save(root, current, track)
            print(f"synced {path.relative_to(root)}")
        elif current:
            _session.clear(root, track)
            print("cleared session outside IMPLEMENTING")
        else:
            print("no session needed")
        return
    if action == "pause":
        if state != "IMPLEMENTING":
            die("session pause requires scope state IMPLEMENTING")
        data = current if current and not current.get("invalid") else _session.new(state, stage)
        task = getattr(args, "task", None)
        context = getattr(args, "context", "") or ""
        if task:
            data["active_task"] = {"id": task, "description": context or task,
                                   "started_at": data.get("updated_at") or _session.now(), "context": context}
            data.setdefault("stack", []).append({"stage": stage, "task": task, "context": context})
        data.update({"state": "PAUSED", "active_stage": stage, "interrupted_at": _session.now(),
                     "interruption_reason": args.reason, "updated_at": _session.now(),
                     "branch": _tracks.current_branch(root)})
        if context:
            data["resume_hints"] = [context] + data.get("resume_hints", [])
        path = _session.save(root, data, track)
        print(f"paused {path.relative_to(root)}")
        return
    if action == "resume":
        if not current:
            die("no saved session")
        if current.get("invalid"):
            die("session JSON is invalid")
        current["state"] = "IMPLEMENTING"
        current["updated_at"] = _session.now()
        _session.save(root, current, track)
        print(f"resume stage: {current.get('active_stage') or '(none)'}")
        for hint in current.get("resume_hints", []):
            print(f"  - {hint}")
        return
    if action == "close":
        print("session cleared" if _session.clear(root, track) else "no session to clear")
        return
    issues = _session.validate(root, current, track)
    result = {"scope": track or "root", "constitution_state": state, "session": current,
              "issues": issues}
    if getattr(args, "json", False):
        _emit_json(result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_track(args) -> None:
    root = Path(args.path).resolve()
    if not (root / ".sdd").is_dir():
        die(f"no .sdd/ found in {root}")
    if args.track_command == "claim":
        if not (root / ".sdd" / "tracks" / args.slug).is_dir():
            die(f"track not found: {args.slug}")
        try:
            data = _tracks.load(root, args.slug)
        except ValueError as exc:
            die(str(exc))
        claim = {"stage": args.stage, "paths": args.path_claim or [],
                 "sequences": args.seq or [], "runtime": args.runtime or [],
                 "stability_sensitive": bool(args.stability_sensitive)}
        changed = False
        if claim not in data["claims"]:
            data["claims"].append(claim)
            changed = True
        if getattr(args, "branch", None) and data.get("branch") != args.branch:
            data["branch"] = args.branch
            changed = True
        if changed:
            _tracks.save(root, args.slug, data)
        _emit_json(claim) if args.json else print(f"claimed {args.slug}: {args.stage}")
        return
    if args.track_command == "incorporate":
        try:
            stage_dir = _find_stage(root, args.stage, args.slug)
            if stage_dir is None:
                die(f"cannot resolve stage {args.stage!r} in track {args.slug}")
            result = _tracks.incorporate(root, args.slug, stage_dir, dry_run=args.dry_run)
        except (ValueError, TimeoutError) as exc:
            die(str(exc))
        if args.json:
            _emit_json(result)
        else:
            verb = "would move" if args.dry_run else "moved"
            print(f"{verb} {result['from']} -> {result['to']}")
            print(f"index row: {result['row']}")
            if not args.dry_run:
                print(dim("Next: drop this stage from the track's row in 'Active tracks' if it was the "
                          "last one, and run sdd-reconcile to regenerate roadmap.md."))
        return
    if args.track_command == "verify":
        try:
            findings = _tracks.verify(root, args.slug, args.since)
        except ValueError as exc:
            die(str(exc))
        result = {"command": "track verify", "project": str(root), "track": args.slug,
                  "findings": findings, "status": 1 if findings else 0}
        if args.json:
            _emit_json(result)
        elif findings:
            for finding in findings:
                who = ", ".join(finding["tracks"]) if "tracks" in finding else finding.get("track", "")
                print(f"{finding['kind']}: {finding['path']} ({who})")
        else:
            print(f"track {args.slug} verified")
        if findings:
            raise SystemExit(1)
        return
    try:
        conflicts = _tracks.check(root)
    except ValueError as exc:
        die(str(exc))
    result = {"command": "track check", "project": str(root), "conflicts": conflicts,
              "status": 1 if conflicts else 0}
    if args.json:
        _emit_json(result)
    elif conflicts:
        for conflict in conflicts:
            detail = conflict.get("paths") or conflict.get("value") or ""
            print(f"conflict {conflict['kind']}: {' vs '.join(conflict['tracks'])} {detail}".rstrip())
        print(dim("Sequence the later stage after the earlier one: fill its 'Depends on' cell in section 5."))
    else:
        print("track claims clean")
    if conflicts:
        raise SystemExit(1)


def cmd_seq(args) -> None:
    root = Path(args.path).resolve()
    if not (root / ".sdd").is_dir():
        die(f"no .sdd/ found in {root}")
    try:
        record = _tracks.reserve_sequence(root, args.name, args.track)
    except ValueError as exc:
        die(str(exc))
    _emit_json(record) if args.json else print(record["number"])


def _stage_path(root: Path, token: str, track: str | None) -> Path:
    found = _find_stage(root, token, track)
    if found:
        return found
    die(f"cannot resolve stage {token!r}")


def cmd_scaffold(args) -> None:
    root = Path(args.path).resolve()
    stage = _stage_path(root, args.stage, getattr(args, "track", None))
    spec = stage / "spec.md"
    if not spec.is_file() or not re.search(r"(?im)^[-*]?\s*\*\*Status:\*\*\s*locked\b", spec.read_text(encoding="utf-8", errors="replace")):
        die("scaffold requires a locked spec.md")
    text = spec.read_text(encoding="utf-8")
    section = re.search(r"(?ms)^## 5\. Acceptance criteria\s*$(.*?)(?=^## 6\.|\Z)", text)
    criteria = re.findall(r"(?m)^[-*]\s+\[\s\]\s+(.+)$", section.group(1) if section else "")
    targets = [stage / "todo.md"]
    features = (manifest.load(root) or {}).get("features", {})
    if features.get("edd"):
        targets += [stage / "evals.md", stage / "checklist.md"]
    created: list[str] = []
    for target in targets:
        if target.exists():
            continue
        if target.name == "todo.md":
            body = "# TODO — " + stage.name + "\n\n## Acceptance verification\n\n" + "\n".join(f"- [ ] {x}" for x in criteria) + "\n"
        else:
            template = CONTENT_DIR / "sdd" / "templates" / ("evals.template.md" if target.name == "evals.md" else "checklist.template.md")
            body = template.read_text(encoding="utf-8") if template.exists() else f"# {target.stem.title()} — {stage.name}\n"
        created.append(str(target.relative_to(root)).replace("\\", "/"))
        if not args.dry_run:
            target.write_text(body, encoding="utf-8", newline="\n")
    print(json.dumps({"created": created, "dry_run": args.dry_run}) if args.json else "\n".join(created or ["nothing to scaffold"]))


def cmd_deps(args) -> None:
    root = Path(args.path).resolve()
    data = _deps.load(root)
    if args.deps_command == "add":
        target = str(Path(args.dependency).resolve())
        edge = {"path": target, "kind": args.kind, "stage": args.stage, "description": args.description or ""}
        if edge not in data["dependencies"]:
            data["dependencies"].append(edge)
            _deps.save(root, data)
        print(target)
        return
    if args.deps_command == "remove":
        target = str(Path(args.dependency).resolve())
        data["dependencies"] = [x for x in data["dependencies"] if x.get("path") != target]
        _deps.save(root, data)
        print(target)
        return
    if args.deps_command == "graph" and args.format == "mermaid":
        print("graph LR")
        for edge in data["dependencies"]:
            print(f'  project["{root.name}"] --> dep["{Path(edge["path"]).name}"]')
        return
    _emit_json(data) if getattr(args, "json", False) or args.format == "json" else print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_impact(args) -> None:
    root = Path(args.path).resolve()
    needle = re.compile(rf"(?<![A-Z0-9-]){re.escape(args.decision)}(?![A-Z0-9-])")
    hits: list[dict] = []
    for path in sorted((root / ".sdd").rglob("*.md")):
        for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if needle.search(line):
                hits.append({"path": str(path.relative_to(root)).replace("\\", "/"), "line": number, "text": line.strip()})
    result = {"decision": args.decision, "impacts": hits}
    _emit_json(result) if args.json else print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_health(args) -> None:
    payload = _doctor_payload(Path(args.path).resolve())
    errors = sum(x["severity"] == "error" for x in payload["findings"])
    warnings = sum(x["severity"] == "warn" for x in payload["findings"])
    score = max(0, 100 - errors * 25 - warnings * 5)
    result = {"version": 1, "command": "health", "score": score,
              "errors": errors, "warnings": warnings, "findings": payload["findings"]}
    _emit_json(result) if args.json else print(f"health: {score}/100 ({errors} errors, {warnings} warnings)")


def cmd_evaluate(args) -> None:
    """Produce local, portable evidence for a later kit evaluation."""
    root = Path(args.path).resolve()
    if not (root / ".sdd").is_dir():
        die(f"no .sdd/ found in {root}")
    doctor = _doctor_payload(root)
    context = _context_payload(root, budget=True)
    stages = root / ".sdd" / "stages"
    tracks = root / ".sdd" / "tracks"
    result = {"schema_version": 1, "command": "evaluate", "generated_at": datetime.now(UTC).isoformat(),
              "kit_version": KIT_VERSION, "project_kit_version": doctor["sdd"],
              "context": {"startup_estimated_tokens": context.get("startup_estimated_tokens", 0), "files": context.get("budget", [])},
              "artifacts": {"stages": len([p for p in stages.iterdir() if p.is_dir()]) if stages.is_dir() else 0,
                            "tracks": len([p for p in tracks.iterdir() if p.is_dir()]) if tracks.is_dir() else 0},
              "doctor_findings": doctor["findings"]}
    if args.write:
        output = root / ".sdd" / "kit-evaluation" / "snapshot.json"
        output.parent.mkdir(exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if not args.json:
            print(f"wrote {output.relative_to(root)}")
    if args.json or not args.write:
        _emit_json(result)


def cmd_document(args) -> None:
    root = Path(args.path).resolve()
    if not (root / ".sdd").is_dir():
        die(f"no .sdd/ found in {root}")
    if args.answers:
        try:
            plan = _docs_plan.load_answers(Path(args.answers))
        except ValueError as exc:
            die(str(exc))
    elif not sys.stdin.isatty():
        die("sdd document needs --answers FILE.json without a TTY")
    else:
        base = input("Documentation base path [docs]: ").strip() or "docs"
        raw = input("Documents (comma-separated relative names) [README.md]: ").strip() or "README.md"
        plan = _docs_plan.validate({"base_path": base, "documents": [{"path": name.strip(), "purpose": "", "owner_stage": "", "format": "md"} for name in raw.split(",") if name.strip()]})
    targets = [root / plan["base_path"] / item["path"] for item in plan["documents"]]
    conflicts = [str(path.relative_to(root)).replace("\\", "/") for path in targets if path.exists()]
    if conflicts and args.create_stubs:
        die("refusing to overwrite existing documentation: " + ", ".join(conflicts))
    result = {"command": "document", "plan": plan, "targets": [str(p.relative_to(root)).replace("\\", "/") for p in targets], "dry_run": args.dry_run}
    if args.dry_run:
        _emit_json(result) if args.json else print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    _docs_plan.save(root, plan)
    if args.create_stubs:
        for target, document in zip(targets, plan["documents"]):
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f"# {Path(document['path']).stem}\n\n> Planned documentation.\n", encoding="utf-8")
    m = manifest.load(root)
    if m:
        m.setdefault("features", {})["documentation"] = True
        manifest.save(root, m)
    constitution = root / ".sdd" / "constitution.md"
    if constitution.is_file():
        text = constitution.read_text(encoding="utf-8", errors="replace")
        text = re.sub(r"(?im)^(\s*[-*]\s+\*\*Documentation:\*\*\s*)off\b", r"\1on", text)
        constitution.write_text(text, encoding="utf-8", newline="\n")
    _emit_json(result) if args.json else print(f"wrote .sdd/documentation.json ({len(targets)} document(s))")


def _dashboard_data(root: Path) -> dict[str, str]:
    """Read-only shared data model for both dashboard renderers."""
    doctor = _doctor_payload(root)
    sdd = root / ".sdd"
    context = _context_payload(root, budget=True) if sdd.is_dir() and (sdd / "constitution.md").is_file() else {}
    stages = [path.name for path in (sdd / "stages").iterdir() if path.is_dir()] if (sdd / "stages").is_dir() else []
    tracks = [path.name for path in (sdd / "tracks").iterdir() if path.is_dir()] if (sdd / "tracks").is_dir() else []
    sections = _constitution_sections(sdd / "constitution.md") if (sdd / "constitution.md").is_file() else []
    edd = [item for item in doctor["findings"] if item["code"].startswith("edd_")]
    return {
        "Overview": f"kit: {doctor.get('sdd', 'not initialized')}\nstate: {context.get('state') or 'unknown'}\nactive stage: {context.get('active_stage') or '(none)'}\nstartup: ~{context.get('startup_estimated_tokens', 0)} tokens",
        "Constitution": "\n".join(f"{name}: {size} B" for name, size in sections) or "nothing to show",
        "Stages / Tracks": f"stages ({len(stages)}): {', '.join(stages) or 'none'}\ntracks ({len(tracks)}): {', '.join(tracks) or 'none'}",
        "EDD": "\n".join(f"{item['code']}: {item.get('stage', '')}" for item in edd) or "nothing to show",
        "Doctor / Fix": "\n".join(f"{item['severity']}: {item['code']}" for item in doctor["findings"]) or "clean",
        "Session": json.dumps(_session.load(root) or {"state": "none"}, ensure_ascii=False, indent=2),
    }


def cmd_dashboard(args) -> None:
    root = Path(args.path).resolve()
    renderer = args.ui or (manifest.load(root) or {}).get("dashboard_renderer", "rich")
    if args.set_default:
        data = manifest.load(root)
        if not data:
            die("dashboard configuration requires an initialized project")
        data["dashboard_renderer"] = renderer
        manifest.save(root, data)
    views = _dashboard_data(root)
    if renderer == "rich":
        try:
            from rich.console import Console
            from rich.table import Table
        except ImportError:
            die("install dashboard support: pip install 'sdd-cli[dashboard-rich]'")
        table = Table(title="SDD Dashboard — Overview")
        table.add_column("View")
        table.add_column("Data")
        for view, value in views.items():
            table.add_row(view, value)
        Console().print(table)
    elif renderer == "textual":
        try:
            from textual.app import App, ComposeResult
            from textual.widgets import Static, TabbedContent, TabPane
        except ImportError:
            die("install dashboard support: pip install 'sdd-cli[dashboard-textual]'")
        class Dashboard(App):
            def compose(self) -> ComposeResult:
                with TabbedContent():
                    for name, value in views.items():
                        with TabPane(name):
                            yield Static(value)
        Dashboard().run()
    else:
        die("--ui must be rich or textual")


def _section_body(section: str) -> str:
    """Extract the body of a v2 section from the bundled template, including
    its ``## <section>`` heading. Used by D5 to emit placeholder text verbatim."""
    text = (CONTENT_DIR / "sdd" / "constitution.md").read_text(encoding="utf-8")
    # Match the heading (allowing the "N. " numeric prefix) and capture until
    # the next "\n---\n" separator or end of file.
    pat = re.compile(
        r"(## " + re.escape(section) + r"[^\n]*\n)"     # heading line
        r"(.*?)(?=\n---\n|\Z)",                           # body until sep/EOF
        re.DOTALL,
    )
    m = pat.search(text)
    return m.group(0).rstrip() if m else f"## {section}\n\n[to be filled]"


# Ordinal of a numbered v2 section ("1. Project vision" -> "1"). Used by
# _present_sections to detect a section by its number regardless of the heading
# language/wording -- a v1 constitution may use a PT synonym the CLI does not
# list (e.g. "4. Questoes em aberto" vs. the mapped "4. Perguntas em aberto").
# Detecting by ordinal prevents the migration-TODO from re-adding a section
# that already exists under an unmapped name (which would duplicate the heading
# -- an MD024 violation -- and, for section 4, would overwrite the real Q-NNN
# rows with a blank placeholder).
_NUMBERED_SECTION_RE = re.compile(r"^##\s+(\d+)\.\s+\S", re.MULTILINE)


def _section_ordinal(sec: str) -> str | None:
    """Return the ordinal prefix of a numbered v2 section ("1" for
    "1. Project vision"), or None for non-numbered sections ("Settings",
    "Current state")."""
    m = re.match(r"^(\d+)\.", sec)
    return m.group(1) if m else None


def _heading_for_ordinal(text: str, ordinal: str) -> str | None:
    """If ``text`` has any ``## <ordinal>. ...`` heading, return the found
    heading text (the full "N. Whatever" after the ``## ``), else None. This
    lets the migration-TODO rename the ACTUAL heading even when it is an
    unmapped PT synonym (catches A1: unmapped "4. Questoes em aberto")."""
    for m in re.finditer(r"^##\s+(\d+)\.\s+(.+?)\s*$", text, re.MULTILINE):
        if m.group(1) == ordinal:
            return f"{ordinal}. {m.group(2)}"
    return None


def _present_sections(text: str) -> dict[str, str]:
    """Map each PRESENT v2 section title to the heading text actually found in
    ``text``. A section counts as present if EITHER:

    - the exact v2 English heading appears; OR
    - the heading's Portuguese equivalent (V1_HEADING_EQUIV) appears; OR
    - for numbered sections, ANY heading with the same ordinal appears
      (``## 4. <anything>``), even an unmapped PT synonym.

    The ordinal rule is what prevents the A1 regression: a v1 "4. Questoes em
    aberto" (synonym NOT in V1_HEADING_EQUIV) is still recognised as present,
    so Task 5 never re-adds section 4 -- and the found heading text flows into
    Task 2 so the agent renames the REAL heading rather than a mapped one that
    is not there.
    """
    present: dict[str, str] = {}
    heading_re = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
    headings = [m.group(1) for m in heading_re.finditer(text)]
    for sec in V2_SECTIONS:
        # Exact English heading.
        if sec in headings:
            present[sec] = sec
            continue
        # Known PT equivalent (by reversed lookup of V1_HEADING_EQUIV).
        pt_hit = next((pt for pt, en in V1_HEADING_EQUIV.items()
                       if en == sec and pt in headings), None)
        if pt_hit:
            present[sec] = pt_hit
            continue
        # Numbered section: any heading with the same ordinal, mapped or not.
        ord_ = _section_ordinal(sec)
        if ord_:
            found = _heading_for_ordinal(text, ord_)
            if found:
                present[sec] = found
    return present


def _current_state_value(text: str) -> str:
    """Find the current state value after ``**State:**`` or ``**Estado:**``."""
    m = re.search(r"^\s*-\s*\*\*(?:Estado|State):\*\*\s*(\S+)\s*$",
                  text, re.MULTILINE)
    return m.group(1) if m else ""


def _current_state_linecount(text: str) -> int:
    """Count non-empty lines in the Current state / Estado atual section.

    Stops at a ``### Active tracks`` sub-heading (parallel-tracks feature) as
    well as the next ``##`` heading: the tracks table is legitimate content
    of that section, not diary creep, so it must not inflate the ~5-line
    pointer-cap heuristic used by the migration TODO generator.
    """
    m = re.search(
        r"^##\s+(Current state|Estado atual)\s*\n(.*?)(?=^###\s|^##\s|\Z)",
        text, re.MULTILINE | re.DOTALL,
    )
    if not m:
        return 0
    return sum(1 for ln in m.group(2).splitlines() if ln.strip())


def _has_settings(text: str) -> bool:
    return bool(re.search(r"^##\s+Settings\s*$", text, re.MULTILINE))


def _active_stage_report_state(root: Path) -> str:
    """Inspect disk and return whether the active stage is open or closed.

    Returns ``"open"`` if ANY stage on disk has a folder but no ``report.md``
    (there is live, in-progress work whose narrative is NOT history yet), and
    ``"closed"`` otherwise (every stage folder on disk has a report.md -- all
    narrative is historical). Used by Task 4 to decide where the active stage's
    narrative belongs during migration:

    - open  -> narrative stays in ``stages/NNN/spec.md`` (it is the state of the
      art, NOT history); Current state becomes a one-line pointer;
    - closed -> narrative moves to `CHANGELOG.md` (dated entries) with §6 kept
      as a dated-band index pointing at it.

    Disk arbitrates; the constitution's "Status" claims are not trusted here.
    """
    stages_dir = root / ".sdd" / "stages"
    if not stages_dir.exists():
        return "closed"
    stage_dirs = [d for d in stages_dir.iterdir() if d.is_dir()]
    if not stage_dirs:
        return "closed"
    has_open = any(not (d / "report.md").exists() for d in stage_dirs)
    return "open" if has_open else "closed"


def _write_migration_todo(root: Path, sdd: Path, old: dict | None,
                          lang: tuple[str, str], prov_keys: list[str],
                          backup_dir: Path | None, target: str) -> Path:
    """Generate .sdd/.migration-todo.md -- a structured prompt an AI agent reads
    to conduct the constitution edits, asking the owner to confirm ONE change at
    a time. The CLI stays dumb: it never rewrites constitution.md itself."""
    constitution = sdd / "constitution.md"
    ctext = constitution.read_text(encoding="utf-8", errors="replace") \
        if constitution.exists() else ""

    lang_code, lang_conf = lang
    present = _present_sections(ctext)
    state_value = _current_state_value(ctext)
    cs_lines = _current_state_linecount(ctext)
    active_report = _active_stage_report_state(root)  # "open" | "closed"

    sections: list[str] = []

    sections.append(f"""# Migration TODO — -> {KIT_VERSION}

> This file was generated by `sdd migrate --to v{target}` as a POINT-IN-TIME snapshot
> of the constitution's state at migration time. The CLI is deliberately dumb:
> it replaced the MANAGED files (`.sdd/README.md`, `.sdd/skills/`,
> `.sdd/templates/`, the provider shims) and left YOUR files
> (`.sdd/constitution.md`, `.sdd/roadmap.md`, `.sdd/stages/`) untouched.
>
> You are now the agent that completes the migration. Each task below was
> derived by inspecting the constitution ONCE -- tasks that were not needed
> at that moment are omitted, and tasks that were needed may have been
> satisfied by an earlier edit in the same run. So treat each task as
> IDEMPOTENT: re-verify its precondition against the LIVE constitution text
> (and disk, where a task mentions it) before proposing it. If a task's
> precondition no longer holds, skip it silently -- do NOT propose an edit
> that has nothing to do.
>
> Rules:
> 1. Do ONE change at a time. Show the owner the exact diff you propose.
> 2. Wait for an explicit yes/no from the owner before applying each change.
> 3. If the owner says no, skip that change and note it in `CHANGELOG.md` (and
>    refresh the §6 dated-band index) as "declined during migration".
> 4. Never batch multiple constitution edits into one yes.
> 5. Before proposing a task, re-read the relevant part of the live
>    `constitution.md` (and disk) and confirm the precondition still holds.
>    This TODO is a snapshot -- it does NOT track edits already applied.
> 6. The canonical v2 state enum is:
>    INITIALIZING, DECIDING, ROADMAP, SPECIFYING, IMPLEMENTING, CLOSING.
> 7. When every task below is done, read `.sdd/README.md` and invoke the
>    `sdd-reconcile` skill to re-derive section 5 from disk and regenerate
>    `roadmap.md`. Then delete this file.
>
> Project root: `{root}`
> Detected language: {lang_code} ({lang_conf})
> Detected providers: {", ".join(prov_keys) if prov_keys else "(none)"}
""")

    # D1 -- Settings block
    if not _has_settings(ctext):
        sections.append(f"""---

## Task 1 -- Add the `## Settings` section

The constitution has no `## Settings` section (v1 omitted it). Propose inserting
this block immediately after the H1 title (the first `# ...` line) and before
the first existing `##` heading, asking the owner to confirm FIRST. Re-check
the live constitution first -- if `## Settings` is already present, skip.

```markdown
## Settings

<!-- Set by `sdd init`. Edit by hand to toggle features later. -->

- **Language:** {lang_code}
  <!-- All interactions and generated artifacts use this language.
       The skill instructions stay in English by design. -->
- **Estimation tracking:** off
  <!-- When turning this ON later: past stages may have coarse metrics.
       Durations are reconstructed from report dates, so early stages can be
       approximate. Say so explicitly rather than presenting them as exact. -->
- **Documentation:** off
  <!-- When on, the sdd-document skill plans the documentation set together
       with the user, based on the actual project. -->
- **Parallel tracks:** off
  <!-- Off by default -- turn on only if you actually want two agent
       sessions working stages of this project at the same time. -->
```

The language is seeded as `{lang_code}` ({lang_conf}). CONFIRM the language
with the owner before pasting -- do not assume. Show the exact insert point
(the line you will paste above and the line below) so the owner can vet the
placement before you apply it.
""")

    # D2 -- rename Portuguese headings and skill references (one at a time).
    # `present` (built by _present_sections) maps each canonical v2 title to
    # the ACTUAL heading text found in the constitution -- including unmapped PT
    # synonyms caught by ordinal (e.g. "4. Questoes em aberto", which is NOT in
    # V1_HEADING_EQUIV). So every numbered section present under any name yields
    # a rename row, which is the A5 fix ("align ALL numbered headings to EN"),
    # and A1 is cleaned up along the way: section 4 always gets an explicit
    # rename whatever its PT synonym, instead of being re-added.
    seen_canonical: set[str] = set()
    rename_rows: list[tuple[str, str]] = []

    # Heading renames for every present section whose found heading is not the
    # canonical v2 English one (covers the 5 numbered sections AND unmapped
    # synonyms detected by ordinal, plus "Current state"/"Estado atual").
    for sec in V2_SECTIONS:
        found = present.get(sec)
        if found is None or found == sec:
            continue
        rename_rows.append((f"`## {found}`", f"`## {sec}`"))
        seen_canonical.add(sec)

    # Inline Current-state fields (Portuguese -> English).
    for frm, to in [("Estado:", "State:"), ("Etapa ativa:", "Active stage:"),
                    ("Próxima ação:", "Next action:"),
                    ("Última atualização:", "Last updated:")]:
        if f"**{frm}" in ctext:
            rename_rows.append((f"`- **{frm}**`", f"`- **{to}**`"))
    # v1 Portuguese skill names -> v2 English.
    for v1sk in ("sdd-iniciar", "sdd-decidir",
                 "sdd-especificar", "sdd-fechar"):
        if re.search(r"\b" + v1sk + r"\b", ctext):
            rename_rows.append((f"`{v1sk}`", f"`{V1_SKILL_MAP[v1sk]}`"))

    if rename_rows:
        rows = "\n".join(f"| {a} | {b} |" for a, b in rename_rows)
        sections.append(f"""---

## Task 2 -- Rename Portuguese headings and skill references

The constitution uses v1 Portuguese headings/skill names. Rename each below,
**one at a time**, showing the owner the before/after line and waiting for
yes/no. Only rename occurrences that exactly match the left column; do not
bulk-rename by partial match. Every numbered heading (sections 1-7) present
under ANY Portuguese name is listed here -- canonical v2 headings are English
only, so aligning them all is part of moving to a clean v2 constitution.

| Current | Rename to |
|---------|-----------|
{rows}

`## Settings` (Task 1) should already exist by the time you start this task;
if a `## Estado atual` section still exists, rename it to `## Current state`.
""")

    # D3 -- map current state value. Only emitted when there is actual work:
    # a state outside the v2 canonical enum (a v1 PT name to map, or an
    # unknown value to ask about). A state ALREADY in V2_STATES needs no
    # task -- the D1/D2/D5 tasks are data-gated (empty for a canonical
    # constitution), so a clean v2 project gets a TODO with only D4 (if
    # oversized), D6 and D7. The old "confirm a canonical state" branch was
    # removed: the TODO header already makes the agent re-verify every
    # precondition against the live constitution, so a confirm-only task was
    # noise for both v1->v2 (rare EN state) and v2->v3 (every case).
    if state_value and state_value not in V2_STATES:
        if state_value in STATE_MAP:
            note = (f"The constitution's current state is `{state_value}`, which "
                    f"is the v1 Portuguese name. Rename it to its v2 canonical "
                    f"name `{STATE_MAP[state_value]}`. Show the owner the one-line "
                    "diff and confirm.")
        else:
            note = (f"The constitution's current state is `{state_value}` -- UNKNOWN "
                    "to v2. Do not guess. Show the owner the canonical v2 enum "
                    "and ASK which state the project is actually in, then set the "
                    "value to the owner's choice.\n\n"
                    "Canonical v2 enum: INITIALIZING, DECIDING, ROADMAP, SPECIFYING, "
                    "IMPLEMENTING, CLOSING.")
        sections.append(f"""---

## Task 3 -- Map the current state value

{note}

Read the live `Current state` field of `constitution.md` before acting -- if a
prior task already set a v2 canonical state, use that value and skip.
""")

    # D4 -- trim Current state if oversized. The narrative's destination depends
    # on whether the active stage is OPEN (no report.md yet -- it is the state of
    # the art, NOT history) or CLOSED (report.md exists -- it IS history). This
    # is the A3 fix: moving an active stage's narrative to section 6 would
    # describe it as past while it is still open, which misleads the next agent.
    if cs_lines > 8:
        if active_report == "open":
            narrative_note = (
                "At least one stage on disk has NO `report.md` -- that stage is "
                "OPEN (still being built) and its narrative is the STATE OF THE "
                "ART, not history. Do NOT move that stage's narrative to "
                "`CHANGELOG.md` -- it stays in `stages/NNN-<slug>/spec.md`. Only "
                "relocate narrative that belongs to a CLOSED stage (one that has "
                "a `report.md`) to `CHANGELOG.md`, dated as history. Before "
                "relocating any line, identify which stage's narrative it is: if "
                "that stage has a `stages/NNN-<slug>/report.md` on disk, history "
                "(`CHANGELOG.md`); otherwise, leave it in the spec.")
            history_dest = ("(for CLOSED stages only) `CHANGELOG.md` (dated), "
                            "then refresh §6's dated-band index to point there")
        else:
            narrative_note = (
                "Every stage on disk already has a `report.md` -- all stages are "
                "CLOSED, so the narrative in Current state IS history. Move it "
                "all to `CHANGELOG.md`, dated; then refresh §6's dated-band index "
                "rather than storing the narrative in the constitution itself.")
            history_dest = "`CHANGELOG.md` (dated), with §6's index refreshed"
        sections.append(f"""---

## Task 4 -- Trim `Current state` to ~5 lines

The Current state section has ~{cs_lines} non-empty lines (v2 hard cap ~5).
{narrative_note}

Move narrative OUT of this section and into {history_dest}. Keep only a
pointer shape:

- **State:** [value from Task 3]
- **Active stage:** [slug or (none)]
- **Next action:** [one line]
- **Last updated:** [date]

plus the existing one-line blockquote pointer to README, if present.

Show the owner the proposed trimmed section AND the proposed section-6
additions, but apply them as two separate confirmations (trim, then history).
Do not delete narrative -- relocate it. A note that the owner rules stale can
be removed, but show the owner before you drop it. Verify the open/closed state
of each stage on disk before deciding where its narrative goes -- this file's
guidance was derived at migration time and the disk may have changed since.
""")

    # D5 -- add missing v2 sections
    missing = [s for s in V2_SECTIONS if s not in present]
    if missing:
        blocks = []
        for i, sec in enumerate(missing, start=1):
            blocks.append(f"""### Task 5.{i} -- Add `## {sec}`

Not found under any name -- neither the v2 English heading, a known v1
Portuguese equivalent, nor any heading with the same ordinal number. Propose
inserting it at its canonical position (before the next existing section, or
at the end of the constitution if it is the last). Use this verbatim
placeholder text from the v2 template:

```markdown
{_section_body(sec)}
```

Show the owner the position, then paste. One confirmation per section.
""")
        sections.append("""

---

## Task 5 -- Add missing v2 sections

The constitution is missing these v2 sections. Add each, one confirmation per
section. (Sections that already exist under any name -- English, a known v1
Portuguese synonym, or ANY heading sharing their ordinal number -- are NOT
re-added; Task 2 renames the Portuguese ones to English.) Re-check the
constitution's current text before proposing each addition -- the table above
was derived at migration time and the file may have changed since.

""" + "\n".join(blocks))

    # D6 -- normalize EOL/encoding for user-owned files
    sections.append("""---

## Task 6 -- Normalize encoding/EOL of the user-owned files

The CLI already normalized the files it owns (README, skills, templates,
shims) to UTF-8 (no BOM) + LF. Your files were left untouched. Run a
normalization pass over:

- `.sdd/constitution.md`
- `.sdd/roadmap.md`
- `.sdd/stages/` (every file)

For each, ensure UTF-8 without BOM and LF line endings. Before applying, show
the owner the list of files that would change and a brief summary (CRLF->LF
count; whether the file had a BOM). This is ONE confirmation for the whole set
unless the owner asks for a per-file review. A file that is already UTF-8 LF is
a no-op; report only what changes.
""")

    # D7 -- run sdd-reconcile
    sections.append("""---

## Task 7 -- Reconcile indexes

After Tasks 1-6 are applied and confirmed, read `.sdd/README.md`, then invoke
the `sdd-reconcile` skill. It re-derives section 5 of the constitution from the
stages on disk and regenerates `roadmap.md` from section 5. Show the owner the
updated section 5 and the regenerated `roadmap.md` before declaring the
migration done.

Once the owner confirms section 5 and `roadmap.md` are correct, DELETE this
file (`.sdd/.migration-todo.md`). It is a one-shot migration artifact.
""")

    out = sdd / ".migration-todo.md"
    out.write_text("\n".join(sections) + "\n",
                   encoding="utf-8", newline="\n")
    return out


def cmd_migrate(args) -> None:
    root = Path(args.path).resolve()
    sdd = root / ".sdd"
    if not sdd.exists():
        die(f"no .sdd/ found in {root}. Run 'sdd init' first.")

    target = args.to.lower().lstrip("v")
    current_major = str(manifest.parse_version(KIT_VERSION)[0])
    if target != current_major:
        die(f"unsupported target version 'v{target}'. Choose --to v{current_major}.")

    old = manifest.load(root)
    old_version = old.get("kit_version") if old else "v1 (no manifest)"
    no_manifest = old is None
    print(bold(f"Migrating {root}"))
    print(f"  from: {old_version}\n  to:   {KIT_VERSION}\n")

    # 0. mojibake gate. Double-encoding (v2) is a deterministic ERROR: do not
    #    touch a single file until it is resolved. --fix-mojibake repairs v2 in
    #    place (only v2; v1 `?` stays for manual review). This runs BEFORE any
    #    backup/replacement so a dirty tree never gets migrated on top of.
    reports = _mojibake.scan_tree(sdd)
    v2_files, _v1_only = _mojibake.classify_reports(reports)
    if v2_files:
        if args.fix_mojibake:
            total = 0
            for r in v2_files:
                total += _mojibake.repair_v2_file(r.path)
            print(green(f"  repaired double-encoding mojibake (v2): {total} "
                        f"span(s) across {len(v2_files)} file(s)"))
            # re-scan: assert nothing v2 remains after the repair.
            still = _mojibake.scan_tree(sdd)
            still_v2, _ = _mojibake.classify_reports(still)
            if still_v2:
                die(f"re-scan after --fix-mojibake still found v2 in "
                    f"{len(still_v2)} file(s); aborting migrate. Open "
                    f"{still_v2[0].path.relative_to(root)} and re-run.")
            print(green("  re-scan clean — all v2 repaired"))
        else:
            print(red(f"\n{red('error:')} double-encoding mojibake (v2) detected "
                      f"in {len(v2_files)} file(s). Migration aborts — migrating "
                      "on top of mojibake would copy the corruption forward."))
            print(dim("  Nothing was written. Resolve it first:"))
            print(dim("    sdd doctor            # full report (v2 + v1 + hygiene)"))
            print(dim("    sdd migrate --to v4 --fix-mojibake   # repair v2 inline"))
            print(dim("  v1 accent-loss (`?`) is NOT auto-fixed; review it by "
                      "hand after migrate."))
            raise SystemExit(1)

    # 1. detect hand-edited managed files (only possible with a manifest).
    edited: list[str] = []
    if old:
        for rel, old_hash in old.get("managed_files", {}).items():
            f = root / rel
            if f.exists() and manifest.hash_file(f) != old_hash:
                edited.append(rel)
    if edited:
        print(yellow("  Hand-edited managed files detected:"))
        for e in edited:
            print(f"    - {e}")
        print(dim("    They will be backed up before replacing.\n"))
    if no_manifest:
        print(dim("  No v1 manifest -- all existing managed files will be backed "
                  "up before replacing (no baseline to diff against).\n"))

    if getattr(args, "provider", None):
        prov_keys = []
        for key in args.provider:
            if not providers.get(key):
                die(f"unknown provider '{key}'")
            prov_keys.append(key)
    elif old:
        prov_keys = old.get("providers") or _detect_providers(root) or ["generic"]
    else:
        prov_keys = _detect_providers(root) or ["generic"]
    if no_manifest:
        lang = _detect_language(root)
        lang_code, lang_conf = lang
    else:
        lang_code = (old or {}).get("language", "pt-BR")
        lang = (lang_code, "from manifest")
        lang_conf = lang[1]

    if args.dry_run:
        print(yellow("  DRY RUN -- nothing written."))
        print("  Would replace: .sdd/README.md, .sdd/skills/**, .sdd/templates/**")
        if "generic" not in prov_keys and (root / "AGENTS.md").exists():
            print(dim("  Would also remove a stray AGENTS.md (byte-identical to "
                      "the generic shim left by a prior buggy migrate)."))
        print("  Would preserve: .sdd/constitution.md, .sdd/roadmap.md, "
              ".sdd/CHANGELOG.md, .sdd/stages/**")
        print(f"  Would refresh shims for: {', '.join(prov_keys)}")
        print(f"  Detected language: {lang_code} ({lang_conf})")
        if no_manifest:
            bdir_sample = (sdd / ".pre-migrate-backup" / "<timestamp>")
            print(f"  Would back up existing managed files to {bdir_sample}/")
        print("  Would generate .sdd/.migration-todo.md (constitution edits, "
              "to be conducted interactively by the agent with the owner).")
        return

    # 2. back up managed files BEFORE overwriting (esp. when no manifest).
    backup_dir, backed = _backup_managed(root, sdd, old, recorded={})
    if backup_dir:
        print(f"  {green('backup')} {backup_dir.relative_to(root)}/ "
              f"{dim('(' + str(len(backed)) + ' files)')}")
        for b in backed:
            print(f"           - {b}")

    # 3. replace managed content only.
    recorded: dict[str, str] = {}
    src = CONTENT_DIR / "sdd"
    for rel in MANAGED_ROOT_FILES:
        dst = sdd / rel
        shutil.copy2(src / rel, dst)
        recorded[f".sdd/{rel}"] = manifest.hash_file(dst)

    for d in MANAGED_DIRS:
        dst_dir = sdd / d
        shutil.rmtree(dst_dir, ignore_errors=True)
        _copy_tree(src / d, dst_dir, recorded, root)
        print(f"  {green('ok')}    replaced .sdd/{d}/")
    print(f"  {green('ok')}    replaced .sdd/README.md")
    print(f"  {green('keep')}  .sdd/constitution.md, roadmap.md, CHANGELOG.md, "
          f"stages/ {dim('(yours)')}")

    # 4. refresh shims only for the detected/recorded providers; clean up stray
    #    shims left by prior installs/migrates when the project no longer wants
    #    that provider.
    for provider in providers.PROVIDERS:
        if provider.key not in prov_keys:
            p = root / provider.shim_path
            src = CONTENT_DIR / "shims" / provider.shim_source
            if p.exists() and src.exists() and \
                    manifest.hash_file(p) == manifest.hash_file(src):
                p.unlink()
                print(f"  {yellow('cleanup')} removed stale {provider.shim_path} "
                      f"{dim('(byte-identical managed shim)')}")
    for key in prov_keys:
        p = providers.get(key)
        if p:
            print(_install_shim(root, p, recorded, force=True))

    # 5. normalize EOL/encoding of the files the CLI just wrote (idempotent;
    #    it owns them). User-owned files are normalized via the TODO.
    for rel in list(recorded):
        if _normalize_file(root / rel):
            # re-hash after normalization
            recorded[rel] = manifest.hash_file(root / rel)

    # 6. write the migration-todo (constitution edits conducted by the agent).
    todo = _write_migration_todo(root, sdd, old, lang, prov_keys, backup_dir,
                                 target)
    print(f"  {green('ok')}    wrote {todo.relative_to(root)} "
          f"{dim('(agent walks the owner through each constitution edit)')}")

    # 7. save the manifest (with a backups ledger for audit).
    features = {"estimation": False, "documentation": False, "tracks": False, "edd": False}
    features.update((old or {}).get("features", {}))
    mdata = manifest.build(KIT_VERSION, lang_code, prov_keys, features, recorded)
    mdata["dashboard_renderer"] = (old or {}).get("dashboard_renderer", "rich")
    if backup_dir:
        ledger = mdata.setdefault("backups", [])
        ledger.append({
            "dir": str(backup_dir.relative_to(root)).replace("\\", "/"),
            "files": backed,
        })
    manifest.save(root, mdata)

    print(bold("\nManaged files updated. Constitution edits are YOUR turn."))
    print(f"  Read {todo.relative_to(root)}, then run "
          f"{(providers.get(prov_keys[0]).invoke if prov_keys else '/sdd')}"
          f" (or your agent's SDD trigger). The agent will walk you through the "
          "remaining constitution edits one at a time, asking you to confirm each "
          "change, then invoke `sdd-reconcile`.")


def cmd_update(args) -> None:
    """Selectively sync managed files for a minor/patch bump within the same
    major kit generation. Unlike `migrate`, this never wipes skills/templates
    wholesale -- it diffs each managed file's old-bundled vs new-bundled
    content and only touches what actually changed, skipping (and backing up)
    anything hand-edited. Requires an existing manifest as a diff baseline.
    """
    root = Path(args.path).resolve()
    sdd = root / ".sdd"
    if not sdd.exists():
        die(f"no .sdd/ found in {root}. Run 'sdd init' first.")

    m = manifest.load(root)
    if m is None:
        die("no .sdd-manifest.json found -- 'sdd update' needs an existing "
            "manifest as a baseline to diff against. Legacy v1 projects have "
            "none; run 'sdd migrate --to v4' first.")

    try:
        installed = manifest.parse_version(m.get("kit_version", ""))
    except ValueError:
        die(f"manifest kit_version {m.get('kit_version')!r} is not a "
            f"parseable semver -- run 'sdd migrate --to v4' instead.")

    bundled = manifest.parse_version(KIT_VERSION)

    print(bold(f"Updating {root}"))
    print(f"  installed: v{'.'.join(map(str, installed))}\n"
          f"  bundled:   v{'.'.join(map(str, bundled))}\n")

    if installed[0] != bundled[0]:
        if getattr(args, "major", False):
            migrated = argparse.Namespace(path=args.path, to=f"v{bundled[0]}",
                                          dry_run=args.dry_run, fix_mojibake=False,
                                          provider=None)
            cmd_migrate(migrated)
            return
        die(f"installed kit is v{installed[0]}.x, bundled kit is "
            f"v{bundled[0]}.x -- 'sdd update' only handles minor/patch "
            f"changes within the same major. Run 'sdd migrate --to "
            f"v{bundled[0]}' instead.")

    if installed >= bundled:
        print(green("Already up to date. Nothing to do."))
        return

    src_sdd = CONTENT_DIR / "sdd"
    managed_files = dict(m.get("managed_files", {}))

    def _in_scope(rel: str) -> bool:
        return rel == ".sdd/README.md" or rel.startswith(".sdd/skills/") \
            or rel.startswith(".sdd/templates/")

    # Hand-edited managed files are never overwritten (detected up front).
    edited: set[str] = {
        rel for rel, old_hash in managed_files.items()
        if _in_scope(rel) and (root / rel).exists()
        and manifest.hash_file(root / rel) != old_hash
    }

    changed, added, removed_flagged, restored, preserved = [], [], [], [], []
    recorded: dict[str, str] = {}

    for rel, old_hash in sorted(managed_files.items()):
        if not _in_scope(rel):
            continue
        if rel in edited:
            preserved.append(rel)
            continue
        new_src = src_sdd / rel[len(".sdd/"):]
        if not new_src.exists():
            removed_flagged.append(rel)
            continue
        new_hash = manifest.hash_file(new_src)
        if new_hash == old_hash:
            continue  # unchanged across the version bump
        cur = root / rel
        (restored if not cur.exists() else changed).append(rel)
        recorded[rel] = new_hash

    # Files added upstream that this project's manifest never recorded.
    for item in sorted(src_sdd.rglob("*")):
        if item.is_dir():
            continue
        rel_from_sdd = item.relative_to(src_sdd).as_posix()
        if rel_from_sdd != "README.md" and not rel_from_sdd.startswith(("skills/", "templates/")):
            continue
        rel = f".sdd/{rel_from_sdd}"
        if rel in managed_files:
            continue
        added.append(rel)
        recorded[rel] = manifest.hash_file(item)

    if args.dry_run:
        print(yellow("  DRY RUN -- nothing written.\n"))
    for rel in changed:
        print(f"  {green('would update' if args.dry_run else 'updated')}   {rel}")
    for rel in restored:
        print(f"  {green('would restore' if args.dry_run else 'restored')}  {rel} "
              f"{dim('(missing on disk)')}")
    for rel in added:
        print(f"  {green('would add' if args.dry_run else 'added')}      {rel}")
    for rel in preserved:
        print(f"  {yellow('hand-edited')} {rel} "
              f"{dim('(would be preserved, not overwritten)' if args.dry_run else '(preserved, not overwritten)')}")
    for rel in removed_flagged:
        print(f"  {yellow('removed upstream')} {rel} "
              f"{dim('(kept on disk; delete manually if no longer needed)')}")

    if args.dry_run:
        print(dim(f"\nWould bump kit_version -> {KIT_VERSION}"))
        return

    if not (changed or restored or added or preserved or removed_flagged):
        print(dim("  (no managed file changes to apply)"))

    backup_dir = None
    if preserved:
        backup_dir, backed = _backup_managed(root, sdd, m, recorded={})
        if backup_dir:
            print(f"\n  {yellow('backup')} {backup_dir.relative_to(root)}/ "
                  f"{dim('(' + str(len(backed)) + ' hand-edited file(s))')}")

    for rel in changed + restored + added:
        new_src = src_sdd / rel[len(".sdd/"):]
        cur = root / rel
        cur.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(new_src, cur)

    managed_files.update(recorded)
    m["managed_files"] = managed_files
    m["kit_version"] = KIT_VERSION
    manifest.save(root, m)

    print(bold("\nDone.") +
          f"  updated={len(changed)} restored={len(restored)} "
          f"added={len(added)} preserved(hand-edited)={len(preserved)} "
          f"flagged-removed={len(removed_flagged)}")
    print(dim(f"  kit_version -> {KIT_VERSION}"))


# ------------------------------------------------------------------ parser

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sdd",
        description="Spec-Driven Development scaffolding for AI coding agents.",
        epilog="Run 'sdd manual' for the full usage manual. 'sdd docs' is a deprecated alias.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--version", action="version", version=f"sdd {KIT_VERSION}")
    sub = p.add_subparsers(dest="command", required=True)

    i = sub.add_parser("init", help="install the SDD kit into a project")
    i.add_argument("path", nargs="?", default=".", help="project root (default: .)")
    i.add_argument("--provider", action="append", metavar="KEY",
                   help="agent to install a shim for (repeatable)")
    i.add_argument("--language", metavar="CODE",
                   help="language for interactions/artifacts, e.g. pt-BR")
    i.add_argument("--estimation", action="store_true",
                   help="enable schedule estimate tracking")
    i.add_argument("--docs", action="store_true",
                   help="enable documentation generation")
    i.add_argument("--tracks", action="store_true",
                   help="enable parallel tracks (sdd-track)")
    i.add_argument("--edd", action="store_true", help="enable Eval Driven Development")
    i.add_argument("--dashboard-ui", choices=("rich", "textual"), default="rich",
                   help="default optional dashboard renderer")
    i.add_argument("--force", action="store_true",
                   help="overwrite managed files and shims")
    i.add_argument("-y", "--yes", action="store_true",
                   help="non-interactive, accept defaults")
    i.set_defaults(func=cmd_init)

    pr = sub.add_parser("providers", help="list supported AI agents")
    pr.add_argument("--plain", action="store_true",
                    help="bare keys, one per line (for agents/scripts)")
    pr.set_defaults(func=cmd_providers)

    d = sub.add_parser(
        "docs",
        help="print the usage manual",
        description="Print the full SDD usage manual (the kit's USAGE.md).",
        epilog="""\
examples:
  sdd docs                       # print the manual to stdout
  sdd docs --md SDD-USAGE.md     # write it to a markdown file
  sdd docs | head                # safe -- prints cleanly, no traceback
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    d.add_argument("--md", nargs="?", const="SDD-USAGE.md", metavar="FILE",
                   help="write the manual to a markdown file instead of stdout")
    d.set_defaults(func=cmd_docs)

    manual = sub.add_parser("manual", help="print the usage manual")
    manual.add_argument("--md", nargs="?", const="SDD-USAGE.md", metavar="FILE",
                        help="write the manual to a markdown file instead of stdout")
    manual.set_defaults(func=cmd_manual)

    ctx = sub.add_parser("context", help="print the minimal session context")
    ctx.add_argument("path", nargs="?", default=".", help="project root (default: .)")
    ctx.add_argument("--budget", action="store_true", help="include hot/cold file byte and token estimates")
    ctx.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    ctx.set_defaults(func=cmd_context)

    m = sub.add_parser(
        "migrate",
        help="upgrade an existing .sdd/ to a new kit",
        description="Upgrade an existing .sdd/ to a new kit version.",
        epilog="""\
flags:
  --to v4             migrate legacy v1, v2 or v3 projects to this release
  --dry-run           preview what would change; write nothing
  --fix-mojibake      repair double-encoding mojibake (v2) inline, then migrate
  path                project root (default: current directory)

examples:
  sdd migrate --to v4 --dry-run      # preview first -- always do this
  sdd migrate --to v4                # migrate to the current kit
  sdd migrate --to v4 --fix-mojibake # repair v2 mojibake, then apply

mojibake gate:
  If double-encoding mojibake (v2: Ã§, Ã£, Ã© ...) is found anywhere under .sdd/,
  migrate ABORTS without writing anything -- migrating on top of corruption
  would copy it forward. Resolve it with --fix-mojibake (v2 only; the ambiguous
  v1 accent-loss `?` is never auto-fixed and stays for manual review) or with
  `sdd doctor` for a full report. The re-scan after --fix-mojibake asserts
  nothing v2 remains before the migration proceeds.

migration todo:
  The CLI is deliberately dumb. It replaces only the MANAGED files
  (.sdd/README.md, .sdd/skills/, .sdd/templates/, the provider shims) and
  leaves .sdd/constitution.md, roadmap.md and stages/ untouched. After the
  run it writes .sdd/.migration-todo.md -- a structured prompt the agent reads
  to walk the OWNER through the remaining constitution edits ONE at a time,
  each confirmed with a yes/no, then to invoke sdd-reconcile. Never edit the
  constitution by hand when a .migration-todo.md is present -- let the agent
  drive it, confirming each change.
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    m.add_argument("path", nargs="?", default=".", help="project root (default: .)")
    m.add_argument("--to", required=True, metavar="VERSION",
                   help="target kit version; current release is v4")
    m.add_argument("--provider", action="append", metavar="KEY",
                   help="replace installed provider shims (repeatable)")
    m.add_argument("--dry-run", action="store_true",
                   help="show what would change, write nothing")
    m.add_argument("--fix-mojibake", action="store_true",
                   help="repair double-encoding (v2) mojibake inline before migrating")
    m.set_defaults(func=cmd_migrate)

    u = sub.add_parser(
        "update",
        help="sync patch/minor kit changes within the same major version",
        description="Selectively sync managed files (README, skills/, "
                    "templates/) when the bundled kit's version is a "
                    "minor/patch bump over what's installed, preserving "
                    "hand-edited files (backed up, not overwritten). "
                    "Refuses across a major-version boundary -- use "
                    "'sdd migrate' for that.",
        epilog="""\
examples:
  sdd update              # sync this project to the bundled kit's minor/patch
  sdd update PATH         # sync another project
  sdd update --dry-run    # preview what would change; write nothing

Unlike 'sdd migrate', this never does a full skills/templates wipe: it diffs
old-bundled vs new-bundled content per managed file and only touches files
that actually changed, skipping any file you've hand-edited (those are
backed up under .sdd/.pre-migrate-backup/<timestamp>/ instead of being
overwritten). Requires an existing .sdd/.sdd-manifest.json -- a legacy v1
project with no manifest has no baseline to diff against; run
'sdd migrate --to v2' first. Refuses to run across a major-version boundary;
run 'sdd migrate --to vN' for that instead.
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    u.add_argument("path", nargs="?", default=".", help="project root (default: .)")
    u.add_argument("--dry-run", action="store_true",
                   help="show what would change, write nothing")
    u.add_argument("--major", action="store_true",
                   help="allow a major update through the migration planner")
    u.set_defaults(func=cmd_update)

    dr = sub.add_parser(
        "doctor",
        help="report SDD presence/version, then audit .sdd/ (read-only)",
        description="First report whether the directory is an SDD project and "
                    "which kit version is installed (from "
                    ".sdd/.sdd-manifest.json, or 'v1 (no manifest)' for legacy "
                    "installs). Then audit .sdd/ for mojibake (double-encoding "
                    "v2, accent-loss v1) and user-file hygiene. Read-only: never "
                    "rewrites a file.",
        epilog="""\
examples:
  sdd doctor            # full report; exit 0 if no SDD, exit 1 if v2 mojibake
  sdd doctor PATH       # audit another project

doctor first reports whether the directory is an SDD project and which kit
version is installed (from .sdd/.sdd-manifest.json, or 'v1 (no manifest)' for
legacy installs). With no .sdd/ it exits 0. It then audits mojibake and
user-file hygiene. v2 (deterministic) mojibake is reported as ERROR (`sdd
migrate --fix-mojibake` repairs it); v1 `?`-accent-loss and closed stages
with open todo.md checkboxes as WARNINGS. Nothing is edited.
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    dr.add_argument("path", nargs="?", default=".", help="project root (default: .)")
    dr.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    dr.set_defaults(func=cmd_doctor)

    fx = sub.add_parser("fix", help="repair deterministic SDD hygiene issues")
    fx.add_argument("path", nargs="?", default=".", help="project root (default: .)")
    fx.add_argument("--all", action="store_true", help="repair all deterministic issues (default)")
    fx.add_argument("--mojibake", action="store_true", help="repair deterministic v2 mojibake")
    fx.add_argument("--eol", action="store_true", help="normalize UTF-8 files to LF")
    fx.add_argument("--links", action="store_true", help="make in-project file:/// links relative")
    fx.add_argument("--features", action="store_true", help="sync manifest feature flags from constitution")
    fx.add_argument("--gitignore", action="store_true",
                    help="opt-in: ignore agent worktree folders (.kilo/worktrees, ...) in .gitignore")
    fx.add_argument("--dry-run", action="store_true", help="report repairs without writing")
    fx.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    fx.set_defaults(func=cmd_fix)

    ses = sub.add_parser("session", help="manage resumable SDD work context")
    ses_sub = ses.add_subparsers(dest="session_command", required=True)
    for name in ("resume", "status", "close", "sync"):
        item = ses_sub.add_parser(name)
        item.add_argument("path", nargs="?", default=".", help="project root (default: .)")
        item.add_argument("--track", help="parallel track slug")
        item.add_argument("--json", action="store_true", help="emit machine-readable JSON")
        item.set_defaults(func=cmd_session)
    pause = ses_sub.add_parser("pause")
    pause.add_argument("path", nargs="?", default=".", help="project root (default: .)")
    pause.add_argument("--track", help="parallel track slug")
    pause.add_argument("--reason", choices=("emergency", "planned", "context_switch"), default="planned", help="why work stopped")
    pause.add_argument("--task", help="active task identifier")
    pause.add_argument("--context", help="resume context")
    pause.set_defaults(func=cmd_session)

    track = sub.add_parser("track", help="declare and check parallel-track footprints")
    track_sub = track.add_subparsers(dest="track_command", required=True)
    claim = track_sub.add_parser("claim", help="record a track footprint")
    claim.add_argument("slug", help="track slug")
    claim.add_argument("--stage", required=True, help="local stage identifier")
    claim.add_argument("--path", dest="path_claim", action="append", help="relative path or glob (repeatable)")
    claim.add_argument("--seq", action="append", help="exclusive sequence name (repeatable)")
    claim.add_argument("--runtime", action="append", help="exclusive runtime resource (repeatable)")
    claim.add_argument("--stability-sensitive", action="store_true", help="cannot overlap any mutating claim")
    claim.add_argument("--branch", help="Git branch this track works on (when it does not use the shared one)")
    claim.add_argument("path", nargs="?", default=".", help="project root (default: .)")
    claim.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    claim.set_defaults(func=cmd_track)
    incorporate = track_sub.add_parser(
        "incorporate", help="move a closed track stage into the canonical queue (atomic)")
    incorporate.add_argument("slug", help="track slug")
    incorporate.add_argument("stage", help="local stage folder or slug inside the track")
    incorporate.add_argument("path", nargs="?", default=".", help="project root (default: .)")
    incorporate.add_argument("--dry-run", action="store_true", help="show the new number and row, write nothing")
    incorporate.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    incorporate.set_defaults(func=cmd_track)
    check = track_sub.add_parser("check", help="fail when active track footprints overlap")
    check.add_argument("path", nargs="?", default=".", help="project root (default: .)")
    check.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    check.set_defaults(func=cmd_track)
    verify = track_sub.add_parser("verify", help="find Git changes outside a track's declared paths")
    verify.add_argument("slug", help="track slug")
    verify.add_argument("--since", help="Git revision to compare against (default: working tree)")
    verify.add_argument("path", nargs="?", default=".", help="project root (default: .)")
    verify.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    verify.set_defaults(func=cmd_track)

    seq = sub.add_parser("seq", help="reserve a shared numeric sequence")
    seq_sub = seq.add_subparsers(dest="seq_command", required=True)
    seq_next = seq_sub.add_parser("next", help="reserve the next identifier")
    seq_next.add_argument("name", help="sequence name (currently: migration)")
    seq_next.add_argument("path", nargs="?", default=".", help="project root (default: .)")
    seq_next.add_argument("--track", help="track holding this reservation")
    seq_next.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    seq_next.set_defaults(func=cmd_seq)

    sc = sub.add_parser("scaffold", help="create missing stage artifacts from a locked spec")
    sc.add_argument("stage", help="stage identifier")
    sc.add_argument("path", nargs="?", default=".", help="project root (default: .)")
    sc.add_argument("--track", help="parallel track slug")
    sc.add_argument("--dry-run", action="store_true", help="show files without writing")
    sc.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    sc.set_defaults(func=cmd_scaffold)

    dep = sub.add_parser("deps", help="manage local cross-project dependencies")
    dep_sub = dep.add_subparsers(dest="deps_command", required=True)
    for name in ("list", "graph"):
        item = dep_sub.add_parser(name)
        item.add_argument("path", nargs="?", default=".", help="project root (default: .)")
        item.add_argument("--format", choices=("text", "json", "mermaid"), default="text", help="output format")
        item.add_argument("--json", action="store_true", help="emit machine-readable JSON")
        item.set_defaults(func=cmd_deps)
    for name in ("add", "remove"):
        item = dep_sub.add_parser(name)
        item.add_argument("dependency", help="dependency project path")
        item.add_argument("path", nargs="?", default=".", help="project root (default: .)")
        if name == "add":
            item.add_argument("--kind", choices=("requires", "provides"), default="requires", help="relationship type")
            item.add_argument("--stage", help="owning stage")
            item.add_argument("--description", help="human-readable rationale")
        item.set_defaults(func=cmd_deps)

    impact = sub.add_parser("impact", help="find stage artifacts affected by a decision")
    impact.add_argument("decision", help="locked decision id, e.g. D-013")
    impact.add_argument("path", nargs="?", default=".", help="project root (default: .)")
    impact.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    impact.set_defaults(func=cmd_impact)

    health = sub.add_parser("health", help="calculate a deterministic SDD health score")
    health.add_argument("path", nargs="?", default=".", help="project root (default: .)")
    health.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    health.set_defaults(func=cmd_health)

    evaluate = sub.add_parser("evaluate", help="capture local evidence for a future kit evaluation")
    evaluate.add_argument("path", nargs="?", default=".", help="project root (default: .)")
    evaluate.add_argument("--write", action="store_true", help="write .sdd/kit-evaluation/snapshot.json")
    evaluate.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    evaluate.set_defaults(func=cmd_evaluate)

    document = sub.add_parser("document", help="persist a project documentation plan")
    document.add_argument("path", nargs="?", default=".", help="project root (default: .)")
    document.add_argument("--answers", help="JSON plan for non-interactive execution")
    document.add_argument("--create-stubs", action="store_true", help="create planned markdown stubs without overwriting")
    document.add_argument("--dry-run", action="store_true", help="validate and show the plan without writing")
    document.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    document.set_defaults(func=cmd_document)

    dash = sub.add_parser("dashboard", help="open the optional SDD dashboard")
    dash.add_argument("path", nargs="?", default=".", help="project root (default: .)")
    dash.add_argument("--ui", choices=("rich", "textual"), help="dashboard renderer")
    dash.add_argument("--set-default", action="store_true", help="save renderer in manifest")
    dash.set_defaults(func=cmd_dashboard)

    return p


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\naborted.", file=sys.stderr)
        raise SystemExit(130)
    except BrokenPipeError:
        # `sdd <cmd> | head` closes the pipe early. Redirect any further stdout
        # to devnull so teardown prints do not re-raise BrokenPipeError, then
        # exit 0 -- covers every subcommand, not just `docs`.
        try:
            sys.stdout.close()
        except BrokenPipeError:
            pass
        try:
            os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        except OSError:
            pass
        raise SystemExit(0)
    except Exception as exc:
        if os.environ.get("SDD_DEBUG") == "1":
            raise
        die(f"unexpected error: {exc}")


if __name__ == "__main__":
    main()
