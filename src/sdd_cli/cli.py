"""sdd -- Spec-Driven Development scaffolding CLI.

Design rule: this CLI is deliberately DUMB. It only does deterministic file
operations (copy templates, place a provider shim, record a manifest). All
reasoning -- understanding the project, asking questions, writing specs --
lives in the skills under .sdd/skills/ and runs inside your AI agent.
"""

import argparse
import shutil
import sys
from pathlib import Path

from . import manifest, providers
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


# -------------------------------------------------------------------- init

def cmd_init(args) -> None:
    root = Path(args.path).resolve()
    if not root.exists():
        die(f"path does not exist: {root}")

    existing = manifest.load(root)
    if existing and not args.force:
        print(f"{yellow('note:')} .sdd/ already initialized "
              f"(kit {existing.get('kit_version')}).")
        print("      Use 'sdd migrate --to v2' to upgrade, or --force to "
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
    }
    if interactive and not args.estimation and not args.docs:
        print(bold("\nOptional features") + dim("  (toggle later in the constitution)"))
        features["estimation"] = input(
            "  Track schedule estimates? [y/N]: ").strip().lower().startswith("y")
        features["documentation"] = input(
            "  Enable documentation generation? [y/N]: "
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

    # user-owned files: only created if absent, never overwritten
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
            target.write_text(text, encoding="utf-8", newline="\n")
            print(f"  {green('ok')}    .sdd/{name}")

    (sdd_dst / "stages").mkdir(exist_ok=True)
    (sdd_dst / "stages" / ".gitkeep").touch()

    ga = root / ".gitattributes"
    if not ga.exists():
        shutil.copy2(CONTENT_DIR / "gitattributes.txt", ga)
        print(f"  {green('ok')}    .gitattributes {dim('(enforces LF)')}")

    print(bold("\nProvider shims"))
    for p in chosen:
        print(_install_shim(root, p, recorded, args.force))

    manifest.save(root, manifest.build(
        KIT_VERSION, language, [p.key for p in chosen], features, recorded))

    print(bold("\nDone.") + f"  language={language}  "
          f"estimation={'on' if features['estimation'] else 'off'}  "
          f"docs={'on' if features['documentation'] else 'off'}")
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


# ----------------------------------------------------------------- migrate

def cmd_migrate(args) -> None:
    root = Path(args.path).resolve()
    sdd = root / ".sdd"
    if not sdd.exists():
        die(f"no .sdd/ found in {root}. Run 'sdd init' first.")

    target = args.to.lower().lstrip("v")
    if target != "2":
        die(f"unsupported target version 'v{target}'. Only v2 is available.")

    old = manifest.load(root)
    old_version = old.get("kit_version") if old else "v1 (no manifest)"
    print(bold(f"Migrating {root}"))
    print(f"  from: {old_version}\n  to:   {KIT_VERSION}\n")

    # 1. detect hand-edited managed files
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
        print(dim("    They will be backed up as <file>.bak before replacing.\n"))

    if args.dry_run:
        print(yellow("  DRY RUN -- nothing written."))
        print("  Would replace: .sdd/README.md, .sdd/skills/**, .sdd/templates/**")
        print("  Would preserve: .sdd/constitution.md, .sdd/roadmap.md, "
              ".sdd/stages/**")
        return

    # 2. replace managed content only
    recorded: dict[str, str] = {}
    src = CONTENT_DIR / "sdd"
    for rel in MANAGED_ROOT_FILES:
        dst = sdd / rel
        if dst.exists() and f".sdd/{rel}" in edited:
            shutil.copy2(dst, dst.with_suffix(dst.suffix + ".bak"))
        shutil.copy2(src / rel, dst)
        recorded[f".sdd/{rel}"] = manifest.hash_file(dst)

    for d in MANAGED_DIRS:
        dst_dir = sdd / d
        # Keep hand-edited content in memory: the rmtree below would wipe any
        # .bak written inside the directory we are about to replace.
        stash: dict[Path, bytes] = {}
        if dst_dir.exists():
            for f in dst_dir.rglob("*"):
                rel = str(f.relative_to(root)).replace("\\", "/")
                if f.is_file() and rel in edited:
                    stash[f] = f.read_bytes()
            shutil.rmtree(dst_dir, ignore_errors=True)
        _copy_tree(src / d, dst_dir, recorded, root)
        for original, data in stash.items():
            bak = original.with_name(original.name + ".bak")
            bak.parent.mkdir(parents=True, exist_ok=True)
            bak.write_bytes(data)
        print(f"  {green('ok')}    replaced .sdd/{d}/")
    print(f"  {green('ok')}    replaced .sdd/README.md")
    print(f"  {green('keep')}  .sdd/constitution.md, roadmap.md, stages/ "
          f"{dim('(yours)')}")

    # 3. refresh shims for known providers
    prov_keys = (old or {}).get("providers") or ["generic"]
    for key in prov_keys:
        p = providers.get(key)
        if p:
            print(_install_shim(root, p, recorded, force=True))

    manifest.save(root, manifest.build(
        KIT_VERSION,
        (old or {}).get("language", "pt-BR"),
        prov_keys,
        (old or {}).get("features", {"estimation": False, "documentation": False}),
        recorded,
    ))

    print(bold("\nManaged files updated.") + " Remaining manual steps:\n")
    print("  1. Add the v2 blocks to .sdd/constitution.md (it is YOURS, so the")
    print("     CLI will not rewrite it): Settings block, section 5 marked as")
    print("     CANONICAL, section 7 Project decision conventions.")
    print("  2. Trim 'Current state' to a ~5-line pointer; move narrative into")
    print("     the stage reports and the change history.")
    print("  3. Run the sdd-reconcile skill in your agent -- it re-derives every")
    print("     stage status from disk and realigns roadmap.md with section 5.")
    print("  4. Normalize encoding/EOL (UTF-8 + LF) across .sdd/.")
    print(dim("\n  Ask your agent: \"read .sdd/README.md and run sdd-reconcile\""))


# ------------------------------------------------------------------ parser

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sdd",
        description="Spec-Driven Development scaffolding for AI coding agents.",
        epilog="Run 'sdd docs' for the full usage manual.",
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
    i.add_argument("--force", action="store_true",
                   help="overwrite managed files and shims")
    i.add_argument("-y", "--yes", action="store_true",
                   help="non-interactive, accept defaults")
    i.set_defaults(func=cmd_init)

    pr = sub.add_parser("providers", help="list supported AI agents")
    pr.add_argument("--plain", action="store_true",
                    help="bare keys, one per line (for agents/scripts)")
    pr.set_defaults(func=cmd_providers)

    d = sub.add_parser("docs", help="print the usage manual")
    d.add_argument("--md", nargs="?", const="SDD-USAGE.md", metavar="FILE",
                   help="write to a markdown file instead of stdout")
    d.set_defaults(func=cmd_docs)

    m = sub.add_parser("migrate", help="upgrade an existing .sdd/ to a new kit")
    m.add_argument("path", nargs="?", default=".", help="project root (default: .)")
    m.add_argument("--to", required=True, metavar="VERSION",
                   help="target kit version, e.g. v2")
    m.add_argument("--dry-run", action="store_true",
                   help="show what would change, write nothing")
    m.set_defaults(func=cmd_migrate)

    return p


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\naborted.", file=sys.stderr)
        raise SystemExit(130)
    except BrokenPipeError:
        # e.g. `sdd docs | head` -- close cleanly instead of dumping a traceback
        try:
            sys.stdout.close()
        finally:
            raise SystemExit(0)


if __name__ == "__main__":
    main()
