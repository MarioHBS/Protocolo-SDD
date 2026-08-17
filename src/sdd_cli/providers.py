"""Canonical registry of supported AI coding agents (providers).

Each provider maps to a thin "shim" file placed in the location that agent
scans. The shim never duplicates the methodology: it only tells the agent to
read `.sdd/README.md` + `.sdd/constitution.md` and load the right skill.

Adding a new provider = one entry here + one file in content/shims/.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Provider:
    key: str            # stable id used in --provider
    name: str           # human label
    kind: str           # "cli" | "ide"
    shim_path: str      # destination path, relative to project root
    shim_source: str    # filename inside content/shims/
    invoke: str         # how the user triggers it


PROVIDERS: tuple[Provider, ...] = (
    Provider("claude", "Claude Code", "cli",
             ".claude/commands/sdd.md", "claude.md", "/sdd"),
    Provider("copilot", "GitHub Copilot (VS Code)", "ide",
             ".github/prompts/sdd.prompt.md", "copilot.md", "/sdd"),
    Provider("cursor", "Cursor", "ide",
             ".cursor/rules/sdd.mdc", "cursor.mdc", "always-on rule"),
    Provider("trae", "Trae", "ide",
             ".trae/rules/sdd.md", "trae.md", "always-on rule"),
    Provider("opencode", "OpenCode", "cli",
             ".opencode/command/sdd.md", "opencode.md", "/sdd"),
    Provider("antigravity", "Antigravity", "ide",
             ".agent/rules/sdd.md", "generic.md", "always-on rule"),
    Provider("windsurf", "Windsurf", "ide",
             ".windsurf/rules/sdd.md", "generic.md", "always-on rule"),
    Provider("gemini", "Gemini CLI", "cli",
             ".gemini/commands/sdd.toml", "gemini.toml", "/sdd"),
    Provider("codex", "Codex CLI", "cli",
             ".agents/skills/sdd/SKILL.md", "codex.md", "$sdd"),
    Provider("generic", "Generic / any other agent", "ide",
             "AGENTS.md", "generic.md", "read AGENTS.md"),
)

BY_KEY = {p.key: p for p in PROVIDERS}


def get(key: str) -> Provider | None:
    return BY_KEY.get(key.strip().lower())


def keys() -> list[str]:
    return [p.key for p in PROVIDERS]
